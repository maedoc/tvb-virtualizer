# -*- coding: utf-8 -*-

import os
from enum import Enum
from Pegasus.DAX3 import File
from bnm.recon.pegasus.utils import get_logger, OUTPUT_FOLDER


class Env(Enum):
    SUBJECT = "${SUBJECT_NAME}"
    THREADS = "${OPENMP_THRDS}"
    THREADS_MRTRIX = "{MRTRIX_THRDS}"


class ConfigKey(Enum):
    """
    Flow parameters --> These will influence the DAX generation
    """
    T1_INPUT_FRMT = "t1.format"
    T2_FLAG = "t2.flag"
    T2_INPUT_FRMT = "t2.format"
    FLAIR_FLAG = "flair.flag"
    FLAIR_INPUT_FRMT = "flair.format"
    DWI_IS_REVERSED = "dwi.is.reversed"
    DWI_INPUT_FRMT = "dwi.format"
    DWI_SCAN_DIRECTION = "dwi.scan.direction"


class RC(Enum):
    """
    Replica Catalog keys.
    Placeholders that need to be defined in rc.txt when execution submit will be done
    """
    T1 = "T1"
    T2 = "T2"
    FLAIR = "FLAIR"
    DWI = "DWI"


LOGGER = get_logger(__name__)


# TODO: see the rest of File(...) usages (output files not referenced towards rc.txt)

class SubtypeConfiguration(object):
    T1 = "t1"
    T2 = "t2"
    FLAIR = "flair"
    DWI = "dwi"

    def __init__(self, folder_path, file_format="", not_empty=True, prefix=T1):
        self.prefix = prefix
        self.folder_path = folder_path
        self.file_format = file_format
        self.not_empty = not_empty
        self.folder = File(folder_path)
        self.raw_nii_file = File(prefix + "-raw.nii.gz")
        self.main_data = self.folder

    @property
    def is_dicom(self):
        return self.file_format == "dicom"


class MRIConfiguration(object):
    def __init__(self):
        self.aseg_mgz_file = File("aparc+aseg.mgz")
        self.t1_mgz_file = File("t1.mgz")
        self.aseg_nii_file = File("aparc+aseg.nii.gz")
        self.t1_nii_file = File("t1-mri.nii.gz")
        self.d2t_file = File("d2t.mat")
        self.t2d_file = File("t2d.mat")
        self.b0_in_t1_file = File("b0-in-t1.nii.gz")
        self.t1_in_d_file = File("t1-in-d.nii.gz ")


class DiffusionConfiguration(SubtypeConfiguration):
    def __init__(self, folder_path, file_format="", is_reversed=False, scan_direction="ap", threads="2"):
        super(DiffusionConfiguration, self).__init__(folder_path, file_format=file_format,
                                                     prefix=SubtypeConfiguration.DWI)
        self.is_dwi_reversed = is_reversed
        self.scan_direction = scan_direction
        self.number_of_threads_mrtrix = threads
        self.dwi_raw_re_file = File("dwi_raw_re.mif")
        self.dwi_raw_mif_file = File("dwi_raw.mif")
        self.dwi_nii_re_file = File("dwi_raw_re.nii.gz")
        self.dwi_mif_file = File("dwi.mif")
        self.brain_mask = File("mask.mif")
        self.b0 = File("b0.nii.gz")


class Configuration(object):
    """
    A class holding all Workflow Configurations for a given patient.
    """
    main_dax_path = os.path.join(OUTPUT_FOLDER, "main_bnm.dax")

    def __init__(self, config_file):
        LOGGER.info("Parsing patient configuration file %s" % config_file)
        props = self._parse_properties(config_file)

        self.subject_name = Env.SUBJECT.value
        self.number_of_threads = Env.THREADS.value

        self.t1 = SubtypeConfiguration(RC.T1.value, props[ConfigKey.T1_INPUT_FRMT], prefix=SubtypeConfiguration.T1)
        self.t2 = SubtypeConfiguration(RC.T2.value, props[ConfigKey.T2_INPUT_FRMT],
                                       bool(props[ConfigKey.T2_FLAG]), SubtypeConfiguration.T2)
        self.flair = SubtypeConfiguration(RC.FLAIR.value, props[ConfigKey.FLAIR_INPUT_FRMT],
                                          bool(props[ConfigKey.FLAIR_FLAG]), SubtypeConfiguration.FLAIR)
        self.diffusion = DiffusionConfiguration(RC.DWI.value, props[ConfigKey.DWI_INPUT_FRMT],
                                                bool(props[ConfigKey.DWI_IS_REVERSED]),
                                                props[ConfigKey.DWI_SCAN_DIRECTION], Env.THREADS_MRTRIX.value)
        self.mri = MRIConfiguration()

    @staticmethod
    def _parse_properties(config_file):
        result_dict = dict()
        with open(config_file) as f:
            for line in f:
                if line.startswith("#") or len(line) < 3 or line.index("=") < 0:
                    continue
                key_str, value = line.split("=")
                try:
                    key = ConfigKey(key_str)
                except KeyError:
                    raise Exception('Invalid property key %r in file %r.' % (key_str, config_file))
                result_dict[key] = value.strip()
        LOGGER.debug("Read patient configuration %s" % result_dict)
        return result_dict
