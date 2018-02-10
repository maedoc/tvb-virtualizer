from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax.mappings import TractsGenFiles, Inputs, OutputConvFiles, T1Files, AsegFiles


class OutputConversion(object):
    def add_conversion_steps(self, dax, job_aparc_aseg, job_aseg_lh, job_aseg_rh):
        weights_csv = File(TractsGenFiles.TRACT_COUNTS.value)
        lenghts_csv = File(TractsGenFiles.TRACT_LENGHTS.value)
        fs_lut = File(Inputs.FS_LUT.value)

        job = Job("convert_output")
        job.addArguments(weights_csv, lenghts_csv, fs_lut)

        job.uses(weights_csv, link=Link.INPUT)
        job.uses(lenghts_csv, link=Link.INPUT)
        job.uses(fs_lut, link=Link.INPUT)

        job.uses(File(OutputConvFiles.RM_CORT_TXT.value), link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.RM_SUBCORT_TXT.value), link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.SURF_CORT_ZIP.value), link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.SURF_SUBCORT_ZIP.value), link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.APARC_ASEG_COR_NII_GZ.value), link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.CONNECTIVITY_ZIP.value), link=Link.OUTPUT, transfer=True, register=False)

        job.uses(File(T1Files.T1_NII_GZ.value), link=Link.INPUT)
        job.uses(File(T1Files.APARC_ASEG_NII_GZ.value), link=Link.INPUT)
        job.uses(File(T1Files.LH_CENTERED_PIAL.value), link=Link.INPUT)
        job.uses(File(T1Files.RH_CENTERED_PIAL.value), link=Link.INPUT)
        job.uses(File(T1Files.LH_APARC_ANNOT.value), link=Link.INPUT)
        job.uses(File(T1Files.RH_APARC_ANNOT.value), link=Link.INPUT)
        job.uses(File(AsegFiles.LH_CENTERED_ASEG.value), link=Link.INPUT)
        job.uses(File(AsegFiles.RH_CENTERED_ASEG.value), link=Link.INPUT)
        job.uses(File(AsegFiles.LH_ASEG_ANNOT.value), link=Link.INPUT)
        job.uses(File(AsegFiles.RH_ASEG_ANNOT.value), link=Link.INPUT)

        dax.addJob(job)

        dax.depends(job, job_aparc_aseg)
        dax.depends(job, job_aseg_lh)
        dax.depends(job, job_aseg_rh)
