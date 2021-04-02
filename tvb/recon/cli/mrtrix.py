
"""
CLI information for mtrix.

"""

import enum
import os
import abc
from .core import BaseCLI, BaseEnv, BaseFlags


class BaseMtrixFlags(BaseFlags):
    """
    Base flags for mtrix commands.

    """
    pass


class BaseMtrixEnv(BaseEnv):
    """
    Base environment variables for mtrix commands.

    """
    pass


class BaseMtrixCLI(BaseCLI):
    """
    Base CLI for mtrix commands.

    """

    class Flags(BaseMtrixFlags):
        nthreads = "-nthreads"
        force = "-force"

    class Env(BaseMtrixEnv):
        pass


class fttgen(BaseMtrixCLI):
    """
    The 5ttgen command from the mtrix package.

    """
    class Algorithm(enum.Enum):
        """The algorithm to be used to derive the 5TT image."""
        fsl = 'fsl'
        freesurfer = 'freesurfer'

    exe = '5ttgen'


class ftt2gmwmi(BaseMtrixCLI):
    """
    The 5tt2gmwmi command from the mtrix package.

    """
    exe = '5tt2gmwmi'


class ftt2vis(BaseMtrixCLI):
    """
    The 5tt2vis command from the mtrix package.

    """
    exe = '5tt2vis'


class dwi2fod(BaseMtrixCLI):
    """
    The dwi2fod command from the mtrix package.

    """
    class Flags(BaseMtrixCLI.Flags):
        mask = '-mask'

    class Algorithm(enum.Enum):
        """The algorithm to use for FOD estimation"""
        csd = 'csd'
        msmt_csd = 'msmt_csd'

    exe = 'dwi2fod'


class dwi2mask(BaseMtrixCLI):
    """
    The dwi2mask command from the mtrix package.

    """
    exe = 'dwi2mask'


class dwi2response(BaseMtrixCLI):
    """
    The dwi2response command from the mtrix package.

    """

    class Algorithm(enum.Enum):
        fa = 'fa'
        manual = 'manual'
        msmt_5tt = 'msmt_5tt'
        tax = 'tax'
        tournier = 'tournier'

    exe = 'dwi2response'


class dwipreproc(BaseMtrixCLI):
    """
    The dwipreproc command from the mtrix package.

    """
    exe = 'dwipreproc'


class dwiextract(BaseMtrixCLI):
    """
    The dwiextract command from the mtrix package.

    """
    exe = 'dwiextract'

    class Flags(BaseMtrixCLI.Flags):
        bzero = '-bzero'


class labelconvert(BaseMtrixCLI):
    """
    The labelconvert command from the mtrix package.

    """
    exe = 'labelconvert'


class mrview(BaseMtrixCLI):
    """
    The mrview command from the mtrix package.

    """
    exe = 'mrview'


class mrconvert(BaseMtrixCLI):
    """
    The mrconvert command from the mtrix package.

    """
    exe = 'mrconvert'


class msdwi2fod(BaseMtrixCLI):
    """
    The msdwi2fod command from the mtrix package.

    """
    exe = 'msdwi2fod'


class tck2connectome(BaseMtrixCLI):
    """
    The tck2connectome command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        out_assignments = "-out_assignments"
        stat_edge = "-stat_edge"

    class Assignment:
        def __init__(self, suffix, *extras):
            self.flag = '-assignment_' + suffix
            self.extras = extras

        def to_args(self):
            return [self.flag] + list(self.extras)

        @classmethod
        def end_voxels(cls):
            return cls('end_voxels')

        @classmethod
        def radial_search(cls, radius):
            return cls('radial_search', str(radius))

        @classmethod
        def reverse_search(cls, max_dist):
            return cls('reverse_search', str(max_dist))

        @classmethod
        def forward_search(cls, max_dist):
            return cls('forward_search', str(max_dist))

        @classmethod
        def all_voxels(cls):
            return cls('all_voxels')

    class Scale:
        def __init__(self, suffix, *extras):
            self.flag = '-scale_' + suffix
            self.extras = extras

        def to_args(self):
            return [self.flag] + list(self.extras)

        @classmethod
        def length(cls):
            return cls('length')

        @classmethod
        def invlength(cls):
            return cls('invlength')

        @classmethod
        def invnodevol(cls):
            return cls('invnodevol')

        @classmethod
        def file(cls, path):
            return cls('file', path)

    class stat_edge(enum.Enum):
        sum = "sum"
        mean = "mean"
        min = "min"
        max = "max"

    exe = 'tck2connectome'


class tckedit(BaseMtrixCLI):
    """
    The tckedit command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        pass

    exe = 'tckedit'


class tckgen(BaseMtrixCLI):
    """
    The tckgen command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        number = "-number"
        unidirectional = "-unidirectional"
        maxlength = "-maxlength"
        step = "-step"
        act = "-act"
        seed_gmwmi = "-seed_gmwmi"

    exe = 'tckgen'


class tckmap(BaseMtrixCLI):
    """
    The tckmap command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        vox = "-vox"
        ends_only = "-ends_only"
        template = "-template"


    exe = 'tckmap'


class tcksift(BaseMtrixCLI):
    """
    The tcksift command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        term_number = "-term_number"
        act = "-act"


    exe = 'tcksift'


class tckstats(BaseMtrixCLI):
    """
    The tckstats command from the mtrix package.

    """

    class Flags(BaseMtrixCLI.Flags):
        dump = '-dump'

    exe = 'tckstats'


def extract_bzero(in_, out):
    return [dwiextract.exe, dwiextract.Flags.bzero, in_, out]


def run_tckgen(source: os.PathLike,
               tracks: os.PathLike,
               ntracks: int,
               seed_gmwmi: os.PathLike=None,
               act: os.PathLike=None,
               unidirectional: bool=True,
               maxlength: float=250.0,
               step: float=0.5,
               ):
    args = [
        tckgen.exe, source, tracks,
        tckgen.Flags.number, ntracks,
        tckgen.Flags.maxlength, maxlength,
        tckgen.Flags.step, step
    ]
    if unidirectional:
        args += [tckgen.Flags.unidirectional]

    if act:
        args += [tckgen.Flags.act, act]
    if seed_gmwmi:
        args += [tckgen.Flags.seed_gmwmi, seed_gmwmi]

    return args


def run_tcksift(in_tracks: os.PathLike,
                in_fod: os.PathLike,
                out_tracks: os.PathLike,
                term_number: int,
                act: os.PathLike=None
                ):
    args = [
        tcksift.exe, in_tracks, in_fod, out_tracks,
        tcksift.Flags.term_number, term_number
    ]
    if act:
        args += [tcksift.Flags.act, act]

    return args


def merge_trackfiles(tracks_a: os.PathLike,
                     tracks_b: os.PathLike,
                     tracks_merged: os.PathLike):

    return [tckedit.exe, tracks_a, tracks_b, tracks_merged]


def dump_streamlines_length(tracks: os.PathLike,
                            lengths: os.PathLike):
    return [tckstats.exe, tracks, tckstats.Flags.dump, lengths]


def run_labelconvert(image_in: os.PathLike,
                     lut_in: os.PathLike,
                     lut_out: os.PathLike,
                     image_out: os.PathLike):

    return [labelconvert.exe, image_in, lut_in, lut_out, image_out]


def run_tck2connectome(track_in: os.PathLike,
                       nodes_in: os.PathLike,
                       connectome_out: os.PathLike,
                       assignment: tck2connectome.Assignment=None,
                       scale: tck2connectome.Scale=None,
                       stat_edge: tck2connectome.stat_edge=tck2connectome.stat_edge.sum,
                       out_assignments: os.PathLike=None
                       ):
    args = [
        tck2connectome.exe, track_in, nodes_in, connectome_out,
        tck2connectome.Flags.stat_edge, stat_edge
    ]
    if assignment:
        args += assignment.to_args()
    if scale:
        args += scale.to_args()
    if out_assignments:
        args += [tck2connectome.Flags.out_assignments, out_assignments]

    return args
