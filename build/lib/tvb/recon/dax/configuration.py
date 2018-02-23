from enum import Enum
from tvb.recon.logger import get_logger

LOGGER = get_logger(__name__)


class ConfigKey(Enum):
    """
    Flow parameters --> These will influence the DAX generation
    """
    SUBJECT = "subject"
    T1_FRMT = "t1.format"
    T2_FLAG = "t2.flag"
    T2_FRMT = "t2.format"
    FLAIR_FLAG = "flair.flag"
    FLAIR_FRMT = "flair.format"
    OPENMP_THRDS = "openmp.threads"
    DWI_IS_REVERSED = "dwi.is.reversed"
    DWI_FRMT = "dwi.format"
    DWI_MULTI_SHELL = "dwi.multi.shell"
    MRTRIX_THRDS = "mrtrix.threads"
    DWI_SCAN_DIRECTION = "dwi.scan.direction"
    ASEG_LH_LABELS = "aseg_lh_labels"
    ASEG_RH_LABELS = "aseg_rh_labels"
    USE_FLIRT = "use_flirt"
    STRMLNS_NO = "strmlns_no"
    STRMLNS_SIFT_NO = "strmlns_sift_no"
    STRMLNS_LEN = "strmlns_len"
    STRMLNS_STEP = "strmlns_step"


class Configuration(object):
    def __init__(self, config_file):
        LOGGER.info("Parsing patient configuration file %s" % config_file)
        self.props = self._parse_properties(config_file)

    @staticmethod
    def _parse_properties(config_file):
        result_dict = dict()
        with open(config_file) as f:
            for line in f:
                if line.startswith("#") or len(
                        line) < 3 or line.index("=") < 0:
                    continue
                key_str, value = line.split("=")
                try:
                    key = ConfigKey(key_str)
                except KeyError:
                    raise Exception(
                        'Invalid property key %r in file %r.' % (key_str, config_file))
                result_dict[key] = value.strip()
            LOGGER.debug("Read patient configuration %s" % result_dict)
            return result_dict
