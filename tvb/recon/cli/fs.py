
"""
CLI information for fs.

"""

import os
import enum
from .core import BaseCLI, BaseEnv, BaseFlags


class Subj:
    """
    File path manager for a FreeSurfer subject.

    """

    class File(enum.Enum):
        T1 = 'mri/T1.mgz'
        aparc_aseg = 'mri/aparc+aseg.mgz'
        brain = 'mri/brain.mgz'

    def __init__(self, sdir: os.PathLike, subj: str):
        self.sdir = sdir
        self.subj = subj

    def fname(self, file: File):
        return os.path.join(self.sdir, self.subj, file.value)


class BaseFsFlags(BaseFlags):
    """
    Base flags for fs commands.

    """
    pass


class BaseFsEnv(BaseEnv):
    """
    Base environment variables for fs commands.

    """
    pass


class BaseFsCLI(BaseCLI):
    """
    Base CLI for fs commands.

    """

    class Flags(BaseFsFlags):
        pass

    class Env(BaseFsEnv):
        pass

    class FileFormats(enum.Enum):
        mgz = 'mgz'
        nii = 'nii'
        nii_gz = 'nii.gz'


class bbregister(BaseFsCLI):
    """
    The bbregister command from the fs package.

    """
    exe = 'bbregister'


class freeview(BaseFsCLI):
    """
    The freeview command from the fs package.

    """
    exe = 'freeview'


class mri_binarize(BaseFsCLI):
    """
    The mri_binarize command from the fs package.

    """
    exe = 'mri_binarize'


class mri_convert(BaseFsCLI):
    """
    The mri_convert command from the fs package.

    """
    exe = 'mri_convert'

    class Flags(BaseFsCLI.Flags):
        in_type = '--in_type'
        out_type = '--out_type'
        out_orientation = '--out_orientation'
        resample_type = '--resample_type'

    class OutOri(enum.Enum):
        RAS = 'RAS'

    class ResampleType(enum.Enum):
        nearest = 'nearest'
        interpolate = 'interpolate'


class mri_info(BaseFsCLI):
    """
    The mri_info command from the fs package.

    """
    exe = 'mri_info'


class mri_pretess(BaseFsCLI):
    """
    The mri_pretess command from the fs package.

    """
    exe = 'mri_pretess'


class mri_tessellate(BaseFsCLI):
    """
    The mri_tessellate command from the fs package.

    """
    exe = 'mri_tessellate'


class mri_vol2vol(BaseFsCLI):
    """
    The mri_vol2vol command from the fs package.

    """
    exe = 'mri_vol2vol'


class mri_surf2surf(BaseFsCLI):
    """
    The mri_surf2surf command from the fs package.

    """
    exe = 'mri_surf2surf'


class mri_surf2vol(BaseFsCLI):
    """
    The mri_surf2vol command from the fs package.

    """
    exe = 'mri_surf2vol'


class mri_aparc2aseg(BaseFsCLI):
    """
    The mri_aparc2aseg command from the fs package.

    """
    exe = 'mri_aparc2aseg'


class mris_calc(BaseFsCLI):
    """
    The mris_calc command from the fs package.

    """
    exe = 'mris_calc'


class mris_convert(BaseFsCLI):
    """
    The mris_convert command from the fs package.

    """
    exe = 'mris_convert'


class mris_extract_main_component(BaseFsCLI):
    """
    The mris_extract_main_component command from the fs package.

    """
    exe = 'mris_extract_main_component'


class mris_decimate(BaseFsCLI):
    """
    The mris_decimate command from the fs package.

    """
    exe = 'mris_decimate'


class mris_smooth(BaseFsCLI):
    """
    The mris_smooth command from the fs package.

    """
    exe = 'mris_smooth'


class recon_all(BaseFsCLI):
    """
    The recon_all command from the fs package.

    """
    exe = 'recon-all'

    class Flags(BaseFsCLI.Flags):
        subjid = '-subjid'
        input_ = '-i'
        all_ = '-all'
        parallel = '-parallel'
        openmp = '-openmp'


def reconstruct(subjid: str,
                input_,
                all_: bool=True,
                parallel: bool=False,
                openmp: int=4
                ):
    """
    Perform the FreeSurfer reconstruction process.

    """

    args = [
        recon_all.exe,
        recon_all.Flags.subjid, subjid,
        recon_all.Flags.input_, input_
    ]
    if all_:
        args += [recon_all.Flags.all_]
    if parallel:
        args += [recon_all.Flags.parallel]
        args += [recon_all.Flags.openmp, openmp]

    return args



def convert(in_, out,
            out_ori: mri_convert.OutOri=None,
            resamp_type: mri_convert.ResampleType=None):
    "Convert between image types using mri_convert."
    cmd = mri_convert
    _, in_ext = os.path.splitext(in_)
    in_type = cmd.FileFormats(in_ext[1:])
    _, out_ext = os.path.splitext(out)
    out_type = cmd.FileFormats(out_ext[1:])
    args = [
        cmd.exe,
        cmd.Flags.in_type, in_type,
        cmd.Flags.out_type, out_type,
    ]
    if out_ori:
        args += [cmd.Flags.out_orientation, out_ori]
    if resamp_type:
        args += [cmd.Flags.resample_type, resamp_type]
    args += [in_, out]
    return args
