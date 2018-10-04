from enum import Enum
from tvb.recon.logger import get_logger

LOGGER = get_logger(__name__)


class ConfigKey(Enum):
    """
    Flow parameters --> These will influence the DAX generation
    """
    SUBJECT = "subject"
    OVERWRITE_RECONALL_FLAG = "overwrite_reconall_flag"
    T1_FRMT = "t1.format"
    T2_FLAG = "t2.flag"
    T2_FRMT = "t2.format"
    FLAIR_FLAG = "flair.flag"
    FLAIR_FRMT = "flair.format"
    OPENMP_THRDS = "openmp.threads"
    ATLAS = "parcelation.atlas"
    DWI_IS_REVERSED = "dwi.is.reversed"
    DWI_FRMT = "dwi.format"
    DWI_ADD_GRADIENT = "dwi.add.gradient"
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
    PROCESS_SENSORS = "process.sensors"
    MRIELEC_FLAG = "mrielec.flag"
    MRIELEC_FRMT = "mrielec.format"
    MRIELEC_BIN_DILATE = "mrielec.bin_dilate"
    MRIELEC_BIN_ERODE = "mrielec.bin_erode"
    SAME_SPACE_VOL_POM = "same.space.vol.pom"
    CT_FLAG = "ct.flag"
    CT_FRMT = "ct.format"
    BEM_SURFACES = "bem.surfaces"
    USE_OPENMEEG = "use.openmeeg"
    CT_ELEC_INTENSITY_TH = "ct.elec.intensity.th"
    SEEG_FLAG = "seeg.flag"
    EEG_FLAG = "eeg.flag"
    MEG_FLAG = "meg.flag"
    SENSOR_GAIN_USE_DIPOLE = "sensor.gain.use.dipole"
    SENSOR_GAIN_USE_DISTANCE = "sensor.gain.use.distance"
    SENSOR_GAIN_USE_REGIONS_DISTANCE = "sensor.gain.use.regions_distance"
    RESAMPLE_FLAG = "resample.flag"
    TRGSUBJECT = "trgsubject"
    DECIM_FACTOR = "decim.factor"
    OS="os"


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


class SensorsType(Enum):
    SEEG = "seeg"
    EEG = "eeg"
    MEG = "meg"
