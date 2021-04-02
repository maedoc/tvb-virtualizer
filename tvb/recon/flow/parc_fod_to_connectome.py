
import os
import numpy as np
import logging
import time
from ..cli import mrtrix
from ..cli.runner import Runner, File
from .core import Flow


class ParcFodToConnectome(Flow):

    FRACTION_SIFT = 0.2
    CONV_TC = 1e-2
    MIN_TRACKS = 5 * 10**5
    MAX_TRACKS = 64 * 10**6

    def __init__(self,
                 parc: os.PathLike,
                 fod: os.PathLike,
                 out_track_counts: os.PathLike,
                 out_mean_lengths: os.PathLike,
                 gmwmi: os.PathLike=None,
                 ftt: os.PathLike=None):
        self.parc = parc
        self.fod = fod
        self.gmwmi = gmwmi
        self.ftt = ftt
        self.out_track_counts = out_track_counts
        self.out_mean_lengths = out_mean_lengths

    def _get_track_stats(self, track_assignments: os.PathLike, track_lengths: os.PathLike, keep_unassigned=False)\
            -> (np.ndarray, np.ndarray):

        tck_ass = np.genfromtxt(os.fspath(track_assignments), dtype=int)
        tck_len = np.genfromtxt(os.fspath(track_lengths), dtype=float)
        ntracks = tck_len.size
        assert tck_ass.shape == (ntracks, 2)

        nregions = np.max(tck_ass) + 1

        mean_len_mtx = np.zeros((nregions, nregions), dtype=float)
        track_count_mtx = np.zeros((nregions, nregions), dtype=float)

        lengths = [[[] for i in range(nregions)] for j in range(nregions)]
        for i, ind in enumerate(tck_ass[:]):
            row, col = min(ind[0], ind[1]), max(ind[0], ind[1])
            lengths[row][col].append(tck_len[i])

        for i in range(nregions):
            for j in range(nregions):
                mean_len_mtx[i, j] = np.mean(lengths[i][j])
                track_count_mtx[i, j] = len(lengths[i][j])

        # Replace NaNs with zeros. NaNs are present where is no connection.
        mean_len_mtx[mean_len_mtx != mean_len_mtx] = 0

        if not keep_unassigned:
            # Unassigned values are in the first row/column according to tck2connectome docs
            mean_len_mtx = mean_len_mtx[1:, 1:]
            track_count_mtx = track_count_mtx[1:, 1:]

        # Normalize track counts
        ntracks = np.sum(track_count_mtx)
        track_count_mtx /= ntracks

        return mean_len_mtx, track_count_mtx

    def _gen_connectome(self, runner: Runner, tracks: os.PathLike, ntracks: int, parc_lbl: os.PathLike) \
            -> (np.ndarray, np.ndarray, np.ndarray):
        """Generate a connectome and track statistics from tracks file."""

        # Sift the tracks
        ntracks_sift = int(ntracks * self.FRACTION_SIFT)
        tracks_sifted = runner.tmp_fname('tracks_sifted_N%s.tck' % ntracks)
        runner.run(mrtrix.run_tcksift(tracks, self.fod, tracks_sifted, ntracks_sift))

        # Save the lengths of all tracks
        track_lengths = runner.tmp_fname('track_lengths_N%s.txt' % ntracks)
        runner.run(mrtrix.dump_streamlines_length(tracks_sifted, track_lengths))

        # Generate the connnectome and save the track assignments
        conn = runner.tmp_fname('conn_N%s.csv' % ntracks)
        track_assignments = runner.tmp_fname('track_assignments_N%s.txt' % ntracks)
        runner.run(mrtrix.run_tck2connectome(tracks_sifted, parc_lbl, conn,
                                             assignment=mrtrix.tck2connectome.Assignment.radial_search(2.0),
                                             out_assignments=track_assignments))

        # Get the track statistics
        mean_len_mtx, track_count_mtx = self._get_track_stats(track_assignments, track_lengths)

        return mean_len_mtx, track_count_mtx

    def run(self, runner: Runner):
        log = logging.getLogger('parc_fod_to_connectome')
        tic = time.time()

        log.info('Relabeling parcellation')
        lut_in = File(os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt'))
        lut_out = File(os.path.join(os.environ['MRT3'], 'src/connectome/tables/fs_default.txt'))
        parc_lbl = runner.tmp_fname('parc_lbl.nii.gz')
        runner.run(mrtrix.run_labelconvert(self.parc, lut_in, lut_out, parc_lbl))

        ntracks = self.MIN_TRACKS
        conv_history = []

        # Generate initial number of tracks, the connectome and its statistics
        log.info('Generating initial %i tracks' % ntracks)
        tracks_a = runner.tmp_fname('tracks_A_N%s.tck' % ntracks)
        runner.run(mrtrix.run_tckgen(self.fod, tracks_a, ntracks, seed_gmwmi=self.gmwmi, act=self.ftt))

        log.info('Generating the connectome from %i tracks' % ntracks)
        mean_len_mtx_0, track_count_mtx_0 = self._gen_connectome(runner, tracks_a, ntracks, parc_lbl)

        converged = False
        while ntracks <= self.MAX_TRACKS/2:
            # TODO: catching errors, warnings

            log.info('Generating additional %i tracks' % ntracks)
            tracks_b = runner.tmp_fname('tracks_B_N%s.tck' % ntracks)
            runner.run(mrtrix.run_tckgen(self.fod, tracks_b, ntracks, seed_gmwmi=self.gmwmi, act=self.ftt))

            ntracks *= 2
            tracks_merged = runner.tmp_fname('tracks_A_N%s.tck' % ntracks)
            runner.run(mrtrix.merge_trackfiles(tracks_a, tracks_b, tracks_merged))
            tracks_a = tracks_merged

            log.info('Generating the connectome from %i tracks' % ntracks)
            mean_len_mtx_1, track_count_mtx_1 = self._gen_connectome(runner, tracks_a, ntracks, parc_lbl)

            # Evaluate convergence criteria
            norm_tc = np.linalg.norm(track_count_mtx_1 - track_count_mtx_0)/np.linalg.norm(track_count_mtx_1)

            log.info('N = %i' % ntracks)
            log.info('    Rel. track lengths difference norm = %s' % norm_tc)
            conv_history.append((ntracks, norm_tc))

            mean_len_mtx_0, track_count_mtx_0 = mean_len_mtx_1, track_count_mtx_1

            if norm_tc < self.CONV_TC:
                converged = True
                break

        if not converged:
            log.warning('MAX_TRACKS reached, convergence criteria not satisfied for N=%s tracks' % ntracks)
        else:
            log.info('Convergence criteria satisfied for N=%i tracks' % ntracks)

        np.savetxt(os.fspath(self.out_track_counts), track_count_mtx_0)
        np.savetxt(os.fspath(self.out_mean_lengths), mean_len_mtx_0)
        log.info('Convergence history: ')
        log.info(' '.join([str(a) for a in conv_history]))
        log.info('complete in %0.2fs', time.time() - tic)
