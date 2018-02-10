import os
import os.path
import logging
import time
from ..cli import runner, fsl, fs, mrtrix
from .core import Flow


class AaToDiff(Flow):
    "Move a subject's aparc+aseg to diffusion space."

    def __init__(self, subj: fs.Subj, dwi: os.PathLike, out_aa: os.PathLike):
        self.subj = subj
        self.dwi = dwi
        self.out_aa = out_aa

    def run(self, runner: runner.Runner):

        log = logging.getLogger('aparc_aseg_in_diffusion')
        tic = time.time()

        fs_t1 = runner.fname(self.subj.fname(fs.Subj.File.T1))
        fs_aa = runner.fname(self.subj.fname(fs.Subj.File.aparc_aseg))

        tmp_t1 = runner.tmp_fname('t1-ras.nii')
        tmp_aa = runner.tmp_fname('aparc+aseg.nii')
        tmp_b0 = runner.tmp_fname('bzero.nii')
        tmp_aa_reo = runner.tmp_fname('aparc+aseg-reo.nii')
        tmp_d2t_mat = runner.tmp_fname('d2t.mat')
        tmp_t2d_mat = runner.tmp_fname('t2d.mat')

        log.info('extracting bzero from dwi')
        runner.run(mrtrix.extract_bzero(self.dwi, tmp_b0))

        log.info('converting FS T1 to RAS nii gz')
        runner.run(fs.convert(
            fs_t1, tmp_t1,
            fs.mri_convert.OutOri.RAS,
        ))

        log.info('converting FS aparc+aseg to RAS nii gz')
        runner.run(fs.convert(
            fs_aa, tmp_aa,
            fs.mri_convert.OutOri.RAS,
            fs.mri_convert.ResampleType.nearest,
        ))

        log.info('reorienting aparc+aseg')
        runner.run(fsl.reorient(tmp_aa, tmp_aa_reo))

        log.info('registering bzero to T1')
        runner.run(fsl.register(
            in_=tmp_b0,
            ref=tmp_t1,
            omat=tmp_d2t_mat,
        ))

        log.info('inverting transform')
        runner.run(fsl.invert_transform(
            in_mat=tmp_d2t_mat,
            out_mat=tmp_t2d_mat
        ))

        log.info('applying transform to aparc+aseg')
        runner.run(fsl.apply_xfm(
            in_=tmp_aa_reo,
            ref=tmp_b0,
            out=self.out_aa,
            mat=tmp_t2d_mat
        ))

        log.info('complete in %0.2fs', time.time() - tic)
