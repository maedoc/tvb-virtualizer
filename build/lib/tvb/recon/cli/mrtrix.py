
"""
CLI information for mtrix.

"""

import enum
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
        assignment_radial_search = "-assignment_radial_search"
        assignment_end_voxels = "-assignment_end_voxels"
        scale_length = "-scale_length"
        stat_edge = "-stat_edge"

    class stat_edge(enum.Enum):
        sum = "sum"
        mean = "mean"
        min = "min"
        max = "max"

    exe = 'tck2connectome'


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


def extract_bzero(in_, out):
    return [dwiextract.exe, dwiextract.Flags.bzero, in_, out]
