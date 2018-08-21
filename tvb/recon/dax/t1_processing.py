from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax import AtlasSuffix
from tvb.recon.dax.mappings import T1JobNames, Inputs, T1Files
from tvb.recon.dax.qc_snapshots import QCSnapshots


class T1Processing(object):
    def __init__(self, subject, overwrite_reconall_flag=False, t1_frmt="nii", use_t2=False, t2_frmt="nii", use_flair=False, flair_frmt="nii",
                 openmp_thrds="4", atlas_suffixes=[AtlasSuffix.DEFAULT]):
        self.subject = subject
        self.overwrite_reconall_flag = str(overwrite_reconall_flag)
        print(self.overwrite_reconall_flag)
        self.t1_format = t1_frmt
        self.t2_flag = use_t2
        self.t2_format = t2_frmt
        self.flair_flag = use_flair
        self.flair_format = flair_frmt
        self.openmp_threads = openmp_thrds
        self.qc_snapshots = QCSnapshots.get_instance()
        self.atlas_suffixes = atlas_suffixes

    def _ensure_input_format(self, file_format, input_name, output_name, dax):
        input_file = File(input_name)
        output_file = None
        job = None

        if file_format == "dicom":
            output_file = File(output_name)
            job = Job(T1JobNames.MRI_CONVERT.value, node_label="mri_convert t1 dicom->nii.gz")
            job.addArguments("-it", "dicom", input_file, output_file)
            job.uses(input_file, link=Link.INPUT)
            job.uses(output_file, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job)

        if output_file is None:
            output_file = input_file

        return output_file, job

    def _add_output_files(self, job, out_files):
        for out_file in out_files:
            job.uses(out_file, link=Link.OUTPUT, transfer=True, register=True)

    def add_t1_processing_steps(self, dax, resamp_flag):
        t1_input = Inputs.T1_INPUT.value
        t1_converted = T1Files.T1_INPUT_CONVERTED.value
        t1_output, job1 = self._ensure_input_format(self.t1_format, t1_input, t1_converted, dax)

        lh_pial = File(T1Files.LH_PIAL.value)
        rh_pial = File(T1Files.RH_PIAL.value)
        lh_white = File(T1Files.LH_WHITE.value)
        rh_white = File(T1Files.RH_WHITE.value)
        aparc_aseg_mgz_vols = []
        lh_aparc_annots = []
        rh_aparc_annots = []
        for atlas_suffix in self.atlas_suffixes:
            aparc_aseg_mgz_vols.append(File(T1Files.APARC_ASEG_MGZ.value % atlas_suffix))
            lh_aparc_annots.append(File(T1Files.LH_APARC_ANNOT.value % atlas_suffix))
            rh_aparc_annots.append(File(T1Files.RH_APARC_ANNOT.value % atlas_suffix))

        out_files_list = aparc_aseg_mgz_vols + \
                         [lh_pial, rh_pial, lh_white, rh_white] + \
                         lh_aparc_annots + rh_aparc_annots

        t1_mgz_output = File(T1Files.T1_MGZ.value)
        norm_mgz_vol = File(T1Files.NORM_MGZ.value)
        brain_mgz_vol = File(T1Files.BRAIN_MGZ.value)
        aseg_mgz_vol = File(T1Files.ASEG_MGZ.value)
        job2 = Job(T1JobNames.RECON_ALL.value, node_label="Recon-all for T1")
        job2.addArguments(self.subject, t1_output, self.openmp_threads,
                          "_".join(self.atlas_suffixes), self.overwrite_reconall_flag)
        job2.uses(t1_output, link=Link.INPUT)
        job2.uses(t1_mgz_output, link=Link.OUTPUT, transfer=True, register=True)
        job2.uses(norm_mgz_vol, link=Link.OUTPUT, transfer=True, register=True)
        job2.uses(brain_mgz_vol, link=Link.OUTPUT, transfer=True, register=True)
        job2.uses(aseg_mgz_vol, link=Link.OUTPUT, transfer=True, register=True)

        if self.t2_flag != "True":
            self._add_output_files(job2, out_files_list)

        dax.addJob(job2)

        if job1 is not None:
            dax.depends(job2, job1)

        last_job = job2

        if self.t2_flag == "True":
            t2_in = Inputs.T2_INPUT.value
            t2_converted = T1Files.T2_CONVERTED.value
            t2_input, job_convert = self._ensure_input_format(self.t2_format, t2_in, t2_converted, dax)

            job = Job(T1JobNames.AUTORECON3_T2.value, node_label="autorecon3 for T2")
            job.addArguments(self.subject, t2_input, self.openmp_threads)
            job.uses(t2_input, link=Link.INPUT)

            self._add_output_files(job, out_files_list)

            dax.addJob(job)

            if job_convert is not None:
                dax.depends(job, job_convert)
            dax.depends(job, last_job)

            last_job = job

        if self.flair_flag == "True":
            flair_in = Inputs.FLAIR_INPUT.value
            flair_converted = T1Files.FLAIR_CONVERTED.value
            flair_input, job_convert = self._ensure_input_format(self.flair_format, flair_in, flair_converted, dax)

            job = Job(T1JobNames.AUTORECON3_FLAIR.value, node_label="autorecon3 for flair")
            job.addArguments(self.subject, flair_input, self.openmp_threads)
            job.uses(flair_input, link=Link.INPUT)

            self._add_output_files(job, out_files_list)

            dax.addJob(job)

            if job_convert is not None:
                dax.depends(job, job_convert)
            dax.depends(job, last_job)

            last_job = job

        t1_nii_gz_vol = File(T1Files.T1_NII_GZ.value)
        job3 = Job(T1JobNames.MRI_CONVERT.value, node_label="Convert T1 to NIFTI in RAS")
        job3.addArguments(t1_mgz_output, t1_nii_gz_vol, "--out_orientation", "RAS")
        job3.uses(t1_mgz_output, link=Link.INPUT)
        job3.uses(t1_nii_gz_vol, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job3)

        dax.depends(job3, last_job)

        jobs4 = []
        aparc_aseg_nii_gz_vol = []
        for atlas_suffix, aparc_aseg_mgz_vol in zip(self.atlas_suffixes, aparc_aseg_mgz_vols):
            aparc_aseg_nii_gz_vol.append(File(T1Files.APARC_ASEG_NII_GZ.value % atlas_suffix))
            if len(atlas_suffix) == 0:
                atlas_name = "default"
            else:
                atlas_name = atlas_suffix[1:]
            jobs4.append(Job(T1JobNames.MRI_CONVERT.value,
                             node_label="Convert APARC+ASEG to NIFTI in RAS for %s atlas " % atlas_name))
            jobs4[-1].addArguments(aparc_aseg_mgz_vol, aparc_aseg_nii_gz_vol[-1],
                                  "--out_orientation", "RAS", "-rt", "nearest")
            jobs4[-1].uses(aparc_aseg_mgz_vol, link=Link.INPUT)
            jobs4[-1].uses(aparc_aseg_nii_gz_vol[-1], link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(jobs4[-1])

            dax.depends(jobs4[-1], last_job)

        if resamp_flag != "True":
            lh_centered_pial = File(T1Files.LH_CENTERED_PIAL.value)
            job5 = Job(T1JobNames.MRIS_CONVERT.value, node_label="mris_convert to center lh.pial")
            job5.addArguments("--to-scanner", lh_pial, lh_centered_pial)
            job5.uses(lh_pial, link=Link.INPUT)
            job5.uses(lh_centered_pial, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job5)

            dax.depends(job5, last_job)

            rh_centered_pial = File(T1Files.RH_CENTERED_PIAL.value)
            job6 = Job(T1JobNames.MRIS_CONVERT.value, node_label="mris_convert to center rh.pial")
            job6.addArguments("--to-scanner", rh_pial, rh_centered_pial)
            job6.uses(rh_pial, link=Link.INPUT)
            job6.uses(rh_centered_pial, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job6)

            dax.depends(job6, last_job)

            self.qc_snapshots.add_vol_surf_snapshot_step(dax, [job3, job5, job6], t1_nii_gz_vol,
                                                         [lh_centered_pial, rh_centered_pial], "pialsurf_t1")

            for lh_aparc_annot, rh_aparc_annot, atlas_suffix in \
                    zip(lh_aparc_annots, rh_aparc_annots, self.atlas_suffixes):
                self.qc_snapshots.add_surf_annot_snapshot_step(dax, [last_job, job5, job6], lh_centered_pial,
                                                               lh_aparc_annot, "lh_pial%s" % atlas_suffix)
                self.qc_snapshots.add_surf_annot_snapshot_step(dax, [last_job, job5, job6], rh_centered_pial,
                                                               rh_aparc_annot, "rh_pial%s" % atlas_suffix)

        return last_job, job3, jobs4
