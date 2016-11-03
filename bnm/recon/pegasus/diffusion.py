# -*- coding: utf-8 -*-

from Pegasus.DAX3 import Job, Link
from bnm.recon.pegasus.utils import get_logger

LOGGER = get_logger(__name__)


def steps_dwi_preproc(main_dax, dwi_config):
    """
    :param main_dax: Append to main DAX DWI steps
    :param dwi_config: Patient based configuration
    """
    LOGGER.info("DWI pre-processing %s" % (dwi_config.folder_path,))

    if dwi_config.is_dwi_reversed:
        LOGGER.info("Reversed DWI")

        if dwi_config.is_dicom:
            LOGGER.info("DICOM identified for DWI")
            job0 = Job(name="mrchoose",
                       node_label=dwi_config.prefix.upper() + " input pre-processing 0 (Reversed, DICOM)")
            job0.addArguments("0", "mrconvert", dwi_config.folder, dwi_config.dwi_raw_mif_file)
            job0.uses(dwi_config.folder, link=Link.INPUT)
            job0.uses(dwi_config.dwi_raw_mif_file, link=Link.OUTPUT, transfer=True, register=False)
            main_dax.addJob(job0)

            job1 = Job(name="mrchoose",
                       node_label=dwi_config.prefix.upper() + " input pre-processing 1 (Reversed, DICOM)")
            job1.addArguments("1", "mrconvert", dwi_config.folder, dwi_config.dwi_raw_re_file)
            job1.uses(dwi_config.folder, link=Link.INPUT)
            job1.uses(dwi_config.dwi_raw_re_file, link=Link.OUTPUT, transfer=True, register=False)
            main_dax.addJob(job1)
        else:
            LOGGER.info("Not DICOM %s" % dwi_config.file_format)

            job0 = Job(name="mrconvert", node_label=dwi_config.prefix.upper() + " input convert (Reversed, not-dicom)")
            job0.addArguments(dwi_config.raw_nii_file, dwi_config.dwi_raw_mif_file)
            job0.uses(dwi_config.raw_nii_file, link=Link.INPUT)
            job0.uses(dwi_config.dwi_raw_mif_file, link=Link.OUTPUT, transfer=True, register=False)
            main_dax.addJob(job0)

            job1 = Job(name="mrconvert",
                       node_label=dwi_config.prefix.upper() + " input convert RE (Reversed, not-dicom)")
            job1.addArguments(dwi_config.dwi_nii_re_file, dwi_config.dwi_raw_re_file)
            job1.uses(dwi_config.dwi_nii_re_file, link=Link.INPUT)
            job1.uses(dwi_config.dwi_raw_re_file, link=Link.OUTPUT, transfer=True, register=False)
            main_dax.addJob(job1)

        main_dax.depends(job1, job0)

        job2 = Job(name="dwipreproc", node_label="Preprocess with eddy correct (Reversed)")
        job2.addArguments(dwi_config.scan_direction, dwi_config.dwi_raw_mif_file, dwi_config.dwi_mif_file, "-rpe_pair",
                          dwi_config.dwi_raw_mif_file, dwi_config.dwi_raw_re_file,
                          "-nthreads", dwi_config.number_of_threads_mrtrix)
        job2.uses(dwi_config.dwi_raw_mif_file, link=Link.INPUT)
        job2.uses(dwi_config.dwi_mif_file, link=Link.OUTPUT, transfer=True, register=False)
        job2.uses(dwi_config.dwi_raw_re_file, link=Link.OUTPUT, transfer=True, register=False)
        main_dax.addJob(job2)

    else:
        LOGGER.info("Simple DWI (non-reversed)")
        job1 = Job(name="mrconvert", node_label="Convert dicoms or nifti to .mif (Non-Reversed)")
        job1.addArguments(dwi_config.folder, dwi_config.dwi_raw_mif_file)
        job1.uses(dwi_config.folder, link=Link.INPUT)
        job1.uses(dwi_config.dwi_raw_mif_file, link=Link.OUTPUT, transfer=True, register=False)
        main_dax.addJob(job1)

        job2 = Job(name="dwipreproc", node_label="Preprocess with eddy correct (Non-Reversed)")
        job2.addArguments(dwi_config.scan_direction, dwi_config.dwi_raw_mif_file, dwi_config.dwi_mif_file,
                          "-rpe_none", "-nthreads", dwi_config.number_of_threads_mrtrix)
        job2.uses(dwi_config.dwi_raw_mif_file, link=Link.INPUT)
        job2.uses(dwi_config.dwi_mif_file, link=Link.OUTPUT, transfer=True, register=False)
        main_dax.addJob(job2)

    job3 = Job(name="dwi2mask", node_label="Create Brain Mask")
    job3.addArguments(dwi_config.dwi_mif_file, dwi_config.brain_mask, "-nthreads", dwi_config.number_of_threads_mrtrix)
    job3.uses(dwi_config.dwi_mif_file, link=Link.INPUT)
    job3.uses(dwi_config.brain_mask, link=Link.OUTPUT, transfer=True, register=False)
    main_dax.addJob(job3)

    job4 = Job(name="dwiextract", node_label="Extract BZERO")
    job4.addArguments(dwi_config.dwi_mif_file, dwi_config.b0, "-bzero", "-nthreads",
                      dwi_config.number_of_threads_mrtrix)
    job4.uses(dwi_config.dwi_mif_file, link=Link.INPUT)
    job4.uses(dwi_config.b0, link=Link.OUTPUT, transfer=True, register=False)
    main_dax.addJob(job4)

    # Add control-flow dependencies
    main_dax.depends(job2, job1)
    main_dax.depends(job3, job2)
    main_dax.depends(job4, job3)
    LOGGER.debug("DWI pre-processing steps added %s" % job4)
    return job4
