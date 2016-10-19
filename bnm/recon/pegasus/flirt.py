# -*- coding: utf-8 -*-

from Pegasus.DAX3 import Job, Link
from bnm.recon.pegasus.utils import get_logger

LOGGER = get_logger(__name__)


def step_coregister_t1_dwi(main_dax, config, relevant_t1_job, relevant_dwi_job):
    LOGGER.info("FLIRT co-registration of T1 with DWI...")

    job1 = Job(name="mri_convert", node_label="Convert T1 to NIFTI with good orientation")
    job1.addArguments(config.mri.t1_mgz_file, config.mri.t1_nii_file, "--out_orientation", "RAS", "-rt", "nearest")
    job1.uses(config.mri.t1_mgz_file, link=Link.INPUT)
    job1.uses(config.mri.t1_nii_file, link=Link.OUTPUT, transfer=True, register=False)

    job2 = Job(name="flirt", node_label="Register DWI to T1 and get the relevant transform")
    job2.addArguments("-in", config.diffusion.b0, "-ref", config.mri.t1_nii_file, "-omat", config.mri.d2t_file,
                      "-out", config.mri.b0_in_t1_file, "-dof", "12", "-searchrx", "-180", "180",
                      "-searchry", "-180", "180", "-searchrz", "-180", "180", "-cost", "mutualinfo")
    job2.uses(config.diffusion.b0, link=Link.INPUT)
    job2.uses(config.mri.t1_nii_file, link=Link.INPUT)
    job2.uses(config.mri.d2t_file, link=Link.OUTPUT, transfer=True, register=False)
    job2.uses(config.mri.b0_in_t1_file, link=Link.OUTPUT, transfer=True, register=False)

    job3 = Job(name="convert_xfm", node_label="Generate inverse transform from T1 to DWI")
    job3.addArguments("-omat", config.mri.t2d_file, "-inverse", config.mri.d2t_file)
    job3.uses(config.mri.d2t_file, link=Link.INPUT)
    job3.uses(config.mri.t2d_file, link=Link.OUTPUT, transfer=True, register=False)

    job4 = Job(name="flirt", node_label="Apply inverse transform from T1 to DWI")
    job4.addArguments("-applyxfm", "-in", config.mri.t1_nii_file, "-ref", config.diffusion.b0,
                      "-out", config.mri.t1_in_d_file, "-init", config.mri.t2d_file, "-interp", "nearestneighbour")
    job4.uses(config.mri.t1_nii_file, link=Link.INPUT)
    job4.uses(config.diffusion.b0, link=Link.INPUT)
    job4.uses(config.mri.t2d_file, link=Link.INPUT)
    job4.uses(config.mri.t1_in_d_file, link=Link.OUTPUT, transfer=True, register=False)

    main_dax.addJob(job1)
    main_dax.addJob(job2)
    main_dax.addJob(job3)
    main_dax.addJob(job4)
    main_dax.depends(job1, relevant_t1_job)
    main_dax.depends(job2, relevant_dwi_job)
    main_dax.depends(job2, job1)
    main_dax.depends(job3, job2)
    main_dax.depends(job4, job3)

    LOGGER.debug("FLIRT co-registration of T1 with DWI steps added.")
