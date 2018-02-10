import os
import sys
import time
from Pegasus.DAX3 import ADAG, Job, Link, File
from tvb.recon.dax.aseg_generation import AsegGeneration
from tvb.recon.dax.configuration import Configuration, ConfigKey
from tvb.recon.dax.coregistration import Coregistration
from tvb.recon.dax.dwi_processing import DWIProcessing
from tvb.recon.dax.output_conversion import OutputConversion
from tvb.recon.dax.t1_processing import T1Processing
from tvb.recon.dax.tracts_generation import TractsGeneration

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s DAXFILE\n" % (sys.argv[0]))
        sys.exit(1)
    daxfile = sys.argv[1]
    patient_file = sys.argv[2]

    dax = ADAG("TVB-PIPELINE")
    dax.metadata("created", time.ctime())

    config = Configuration(patient_file)

    t1_processing = T1Processing(config.props[ConfigKey.SUBJECT], config.props[ConfigKey.T1_FRMT],
                                 config.props[ConfigKey.T2_FLAG], config.props[ConfigKey.T2_FRMT],
                                 config.props[ConfigKey.FLAIR_FLAG], config.props[ConfigKey.FLAIR_FRMT],
                                 config.props[ConfigKey.OPENMP_THRDS])

    dwi_processing = DWIProcessing(config.props[ConfigKey.DWI_IS_REVERSED], config.props[ConfigKey.DWI_FRMT],
                                   config.props[ConfigKey.MRTRIX_THRDS], config.props[ConfigKey.DWI_SCAN_DIRECTION])

    coregistration = Coregistration(config.props[ConfigKey.SUBJECT], config.props[ConfigKey.USE_FLIRT])

    tracts_generation = TractsGeneration(config.props[ConfigKey.DWI_MULTI_SHELL], config.props[ConfigKey.MRTRIX_THRDS],
                                         config.props[ConfigKey.STRMLNS_NO], config.props[ConfigKey.STRMLNS_SIFT_NO],
                                         config.props[ConfigKey.STRMLNS_LEN], config.props[ConfigKey.STRMLNS_STEP])

    aseg_generation = AsegGeneration(config.props[ConfigKey.SUBJECT], config.props[ConfigKey.ASEG_LH_LABELS],
                                     config.props[ConfigKey.ASEG_RH_LABELS])

    output_conversion = OutputConversion()

    job_t1, job_aparc_aseg = t1_processing.add_t1_processing_steps(dax)
    job_b0, job_mask = dwi_processing.add_dwi_processing_steps(dax)
    job_t1_in_d, job_aparc_aseg_in_d = coregistration.add_coregistration_steps(dax, job_b0, job_t1,
                                                                               job_aparc_aseg)
    job_aseg_lh, job_aseg_rh, job_fs_custom = aseg_generation.add_aseg_generation_steps(dax, job_aparc_aseg)
    tracts_generation.add_tracts_generation_steps(dax, job_t1_in_d, job_mask, job_aparc_aseg_in_d, job_fs_custom)
    output_conversion.add_conversion_steps(dax, job_aparc_aseg, job_aseg_lh, job_aseg_rh)

    out_dir = os.path.dirname(daxfile)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    with open(daxfile, "w") as f:
        dax.writeXML(f)
