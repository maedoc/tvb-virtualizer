# -*- coding: utf-8 -*-

from Pegasus.DAX3 import Job, Link
from bnm.recon.pegasus.config import SubtypeConfiguration
from bnm.recon.pegasus.utils import get_logger

LOGGER = get_logger(__name__)


def _step_recon_all(main_dax, previous_job, main_config, subtype_config):
    LOGGER.info("Adding steps for image type: " + subtype_config.prefix.upper())
    if subtype_config.is_dicom:
        LOGGER.info("DICOM identified for " + subtype_config.prefix.upper())
        job1 = Job(name="mri_convert", node_label="DICOM input pre-processing for " + subtype_config.prefix.upper())
        job1.addArguments(subtype_config.folder, subtype_config.raw_nii_file, "--out_orientation", "RAS", "-rt",
                          "nearest")
        job1.uses(subtype_config.folder, link=Link.INPUT)
        job1.uses(subtype_config.raw_nii_file, link=Link.OUTPUT, transfer=True, register=False)
        subtype_config.main_data = subtype_config.raw_nii_file

        main_dax.addJob(job1)
        if previous_job is not None:
            LOGGER.debug("Job dependency %s - %s" % (job1, previous_job))
            main_dax.depends(job1, previous_job)
        previous_job = job1

    job2 = Job(name="recon-all", node_label="Call 'recon-all' for " + subtype_config.prefix.upper())
    if subtype_config.prefix == SubtypeConfiguration.T1:
        LOGGER.debug("T1 branch..")
        job2.addArguments("-s", main_config.subject_name, "-i", subtype_config.main_data, "-all",
                          "-parallel", "-openmp", main_config.number_of_threads)
        # TODO see if these can work for implicit job dependency generation
        job2.uses(main_config.mri.aseg_mgz_file, link=Link.OUTPUT, transfer=True)
        job2.uses(main_config.mri.t1_mgz_file, link=Link.OUTPUT, transfer=True)
    else:
        LOGGER.debug("recon-all steps for " + subtype_config.prefix)
        job2.addArguments("-s", main_config.subject_name, "-" + subtype_config.prefix.upper(), subtype_config.main_data,
                          "-" + subtype_config.prefix.upper() + "pial", "-autorecon3",
                          "-parallel", "-openmp", main_config.number_of_threads)

    job2.uses(subtype_config.main_data, link=Link.INPUT)
    main_dax.addJob(job2)

    if previous_job is not None:
        LOGGER.debug("Job dependency %s - %s" % (job2, previous_job))
        main_dax.depends(job2, previous_job)
    return job2


def steps_recon_all(main_dax, config):
    last_job = _step_recon_all(main_dax, None, config, config.t1)
    return_job = last_job
    if config.t2.not_empty:
        last_job = _step_recon_all(main_dax, last_job, config, config.t2)
    if config.flair.not_empty:
        last_job = _step_recon_all(main_dax, last_job, config, config.flair)

    mri_job = Job(name="mri_convert", node_label="Generate APARC-ASEG nifti file with good orientation")
    mri_job.addArguments(config.mri.aseg_mgz_file, config.mri.aseg_nii_file, "--out_orientation", "RAS",
                         "-rt", "nearest")
    mri_job.uses(config.mri.aseg_mgz_file, link=Link.INPUT)
    mri_job.uses(config.mri.aseg_nii_file, link=Link.OUTPUT, transfer=True, register=False)

    main_dax.addJob(mri_job)
    main_dax.depends(mri_job, last_job)
    return return_job
