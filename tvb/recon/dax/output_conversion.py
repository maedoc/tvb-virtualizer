from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax import AtlasSuffix
from tvb.recon.dax.mappings import TractsGenFiles, OutputConvFiles, T1Files, AsegFiles


class OutputConversion(object):
    def __init__(self, atlas_suffix=AtlasSuffix.DEFAULT):
        self.atlas_suffix = atlas_suffix

    def add_conversion_steps(self, dax, job_aparc_aseg, job_mapping_details, job_weights, job_lengths):

        weights_csv = File(TractsGenFiles.TRACT_COUNTS.value % self.atlas_suffix)
        lenghts_csv = File(TractsGenFiles.TRACT_LENGHTS.value % self.atlas_suffix)

        if len(self.atlas_suffix) == 0:
            atlas_name = "default"
        else:
            atlas_name = self.atlas_suffix[1:]
        job = Job("convert_output", node_label="convert_output of atlas " + atlas_name)
        job.addArguments(weights_csv, lenghts_csv, self.atlas_suffix)

        job.uses(weights_csv, link=Link.INPUT)
        job.uses(lenghts_csv, link=Link.INPUT)
        job.uses(File(AsegFiles.CENTERS_TXT.value % self.atlas_suffix), link=Link.INPUT)
        job.uses(File(AsegFiles.AREAS_TXT.value % self.atlas_suffix), link=Link.INPUT)
        job.uses(File(AsegFiles.ORIENTATIONS_TXT.value % self.atlas_suffix), link=Link.INPUT)
        job.uses(File(AsegFiles.CORTICAL_TXT.value % self.atlas_suffix), link=Link.INPUT)
        job.uses(File(AsegFiles.RM_TO_APARC_ASEG_TXT.value %self.atlas_suffix), link=Link.INPUT)

        job.uses(File(OutputConvFiles.APARC_ASEG_COR_NII_GZ.value % self.atlas_suffix),
                     link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.CONNECTIVITY_ZIP.value % self.atlas_suffix),
                     link=Link.OUTPUT, transfer=True, register=False)
        job.uses(File(OutputConvFiles.DONE_FILE.value % atlas_name),
                 link=Link.OUTPUT, transfer=True, register=False)

        job.uses(File(T1Files.T1_NII_GZ.value), link=Link.INPUT)
        job.uses(File(T1Files.APARC_ASEG_NII_GZ.value % self.atlas_suffix), link=Link.INPUT)

        dax.addJob(job)

        dax.depends(job, job_aparc_aseg)
        dax.depends(job, job_mapping_details)
        dax.depends(job, job_weights)
        dax.depends(job, job_lengths)

        return job
