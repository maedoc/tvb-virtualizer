
"""
CLI information for fsl.

"""

import enum
import typing
from .core import BaseCLI


class BaseFslCLI(BaseCLI):
    """
    Base CLI for fsl commands.

    """

    class Flags(BaseCLI.Flags):
        pass

    class Env(BaseCLI.Env):
        output_type = 'FSLOUTPUTTYPE'

    class OutputTypes(enum.Enum):
        nifti_gz = 'NIFTI_GZ'


class convert_xfm(BaseFslCLI):
    """
    The convert_xfm command from the fsl package.

    """
    exe = 'convert_xfm', 'fsl5.0-convert_xfm'

    class Flags(BaseFslCLI.Flags):
        omat = '-omat'
        inverse = '-inverse'  # TODO ref img must be one originally used?


class flirt(BaseFslCLI):
    """
    FSL's image registration tool.

    """
    exe = 'flirt', 'fsl5.0-flirt'

    class Flags(BaseFslCLI.Flags):
        "Some of flirt's command line flags."
        in_ = '-in'
        ref = '-ref'
        out = '-out'
        omat = '-omat'
        init = '-init'
        interp = '-interp'
        dof = '-dof'
        cost = '-cost'
        searchrx = '-searchrx'
        searchry = '-searchry'
        searchrz = '-searchrz'
        apply_xfm = '-applyxfm'

    class dof(enum.Enum):
        "Degrees of freedom determine the type of transform."
        affine = 12
        rigid = 6

    class cost(enum.Enum):
        "Cost funciton used to guide registration."
        mutual_info = 'mutualinfo'
        corr_ratio = 'corrratio'

    class interp(enum.Enum):
        "Interpolation used when resampling input image in output space."
        nearest = 'nearestneighbour'
        trilinear = 'trilinear'

    # rotational search is constrained by pair of angles.
    searchr = typing.Tuple[int, int]


class fslreorient2std(BaseFslCLI):
    """
    The fslreorient2std command from the fsl package.

    """
    exe = 'fslreorient2std', 'fsl5.0-fslreorient2std'


def register(in_, ref, omat, out=None,
             searchrx: flirt.searchr=(-180, 180),
             searchry: flirt.searchr=(-180, 180),
             searchrz: flirt.searchr=(-180, 180),
             dof: flirt.dof=flirt.dof.affine,
             cost: flirt.cost=flirt.cost.mutual_info,
             interp: flirt.interp=flirt.interp.nearest,
             ):
    """
    Register an input image with a reference image.

    Parameters
    ----------
    in_ : os.PathLike
        input image to move.
    ref : os.PathLike
        image to move in_ to.
    omat : os.PathLike

    out
    searchrx
    searchry
    searchrz
    dof
    cost
    interp

    Returns
    -------

    """
    args = [
        flirt.exe,
        flirt.Flags.in_, in_,
        flirt.Flags.ref, ref,
        flirt.Flags.omat, omat,
        flirt.Flags.dof, dof,
        flirt.Flags.searchrx, searchrx[0], searchrx[1],
        flirt.Flags.searchry, searchry[0], searchry[1],
        flirt.Flags.searchrz, searchrz[0], searchrz[1],
        flirt.Flags.cost, cost,
        flirt.Flags.interp, interp
    ]
    if out:
        args += [flirt.Flags.out, out]
    return args


def apply_xfm(in_, ref, out, mat,
              interp: flirt.interp=flirt.interp.nearest):
    """
    Apply a flirt-generated transform to an image.

    Parameters
    ----------
    in_
    ref
    out
    mat
    interp

    Returns
    -------

    """
    return [
        flirt.exe, flirt.Flags.apply_xfm,
        flirt.Flags.in_, in_,
        flirt.Flags.ref, ref,
        flirt.Flags.out, out,
        flirt.Flags.init, mat,
        flirt.Flags.interp, interp
    ]


def reorient(in_, out=None):
    """
    Reorient an image with fslreorient2std.

    Parameters
    ----------
    in_
    out

    Returns
    -------

    """
    args = [fslreorient2std.exe, in_]
    if out:
        args.append(out)
    return args


def invert_transform(in_mat, out_mat):
    return [
        convert_xfm.exe,
        convert_xfm.Flags.omat, out_mat,
        convert_xfm.Flags.inverse, in_mat
    ]
