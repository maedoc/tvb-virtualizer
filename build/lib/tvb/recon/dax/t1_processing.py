from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax.mappings import T1JobNames, Inputs, T1Files
from tvb.recon.dax.qc_snapshots import QCSnapshots


class T1Processing(object):
    def __init__(self, subject, t1_frmt="nii", use_t2=False, t2_frmt="nii", use_flair=False, flair_frmt="nii",
                 openmp_thrds="4"):
        self.subject = subject
        self.t1_format = t1_frmt
        self.t2_flag = use_t2
        self.t2_format = t2_frmt
        self.flair_flag = use_flair
        self.flair_format = flair_frmt
        self.openmp_threads = openmp_thrds
        self.qc_snapshots = QCSnapshots.get_instance()

    def _ensure_input_format(self, file_format, input_name, output_name, dax):
        input_file = File(input_name)
        output_file = None
        job = None

        if file_format == "dicom":
            output_file = File(output_name)
            job = Job(T1JobNames.MRI_CONVERT.value)
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

    def add_t1_processing_steps(self, dax):
        t1_input = Inputs.T1_INPUT.value
        t1_converted = T1Files.T1_INPUT_CONVERTED.value
        t1_output, job1 = self._ensure_input_format(self.t1_format, t1_input, t1_converted, dax)

        aparc_aseg_mgz_vol = File(T1Files.APARC_ASEG_MGZ.value)
        lh_pial = File(T1Files.LH_PIAL.value)
        rh_pial = File(T1Files.RH_PIAL.value)
        lh_aparc_annot = File(T1Files.LH_APARC_ANNOT.value)
        rh_aparc_annot = File(T1Files.RH_APARC_ANNOT.value)

        out_files_list = [aparc_aseg_mgz_vol, lh_pial, rh_pial, lh_aparc_annot, rh_aparc_annot]

        t1_mgz_output = File(T1Files.T1_MGZ.value)
        norm_mgz_vol = File(T1Files.NORM_MGZ.value)
        job2 = Job(T1JobNames.RECON_ALL.value, node_label="Recon-all for T1")
        job2.addArguments(self.subject, t1_output, self.openmp_threads)
        job2.uses(t1_output, link=Link.INPUT)
        job2.uses(t1_mgz_output, link=Link.OUTPUT, transfer=True, register=True)
        job2.uses(norm_mgz_vol, link=Link.OUTPUT, transfer=True, register=True)

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

            job = Job(T1JobNames.AUTORECON3_T2.value)
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

            job = Job(T1JobNames.AUTORECON3_FLAIR.value)
            job.addArguments(self.subject, flair_input, self.openmp_threads)
            job.uses(flair_input, link=Link.INPUT)

            self._add_output_files(job, out_files_list)

            dax.addJob(job)

            if job_convert is not None:
                dax.depends(job, job_convert)
            dax.depends(job, last_job)

            last_job = job

        t1_nii_gz_vol = File(T1Files.T1_NII_GZ.value)
        job3 = Job(T1JobNames.MRI_CONVERT.value, node_label="Convert T1 to NIFTI with good orientation")
        job3.addArguments(t1_mgz_output, t1_nii_gz_vol, "--out_orientation", "RAS")
        job3.uses(t1_mgz_output, link=Link.INPUT)
        job3.uses(t1_nii_gz_vol, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job3)

        dax.depends(job3, last_job)

        aparc_aseg_nii_gz_vol = File(T1Files.APARC_ASEG_NII_GZ.value)
        job4 = Job(T1JobNames.MRI_CONVERT.value, node_label="Convert APARC+ASEG to NIFTI with good orientation")
        job4.addArguments(aparc_aseg_mgz_vol, aparc_aseg_nii_gz_vol, "--out_orientation", "RAS", "-rt", "nearest")
        job4.uses(aparc_aseg_mgz_vol, link=Link.INPUT)
        job4.uses(aparc_aseg_nii_gz_vol, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job4)

        dax.depends(job4, last_job)

        lh_centered_pial = File(T1Files.LH_CENTERED_PIAL.value)
        job5 = Job(T1JobNames.MRIS_CONVERT.value)
        job5.addArguments("--to-scanner", lh_pial, lh_centered_pial)
        job5.uses(lh_pial, link=Link.INPUT)
        job5.uses(lh_centered_pial, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job5)

        dax.depends(job5, last_job)

        rh_centered_pial = File(T1Files.RH_CENTERED_PIAL.value)
        job6 = Job(T1JobNames.MRIS_CONVERT.value)
        job6.addArguments("--to-scanner", rh_pial, rh_centered_pial)
        job6.uses(rh_pial, link=Link.INPUT)
        job6.uses(rh_centered_pial, link=Link.OUTPUT, transfer=False, register=False)
        dax.addJob(job6)

        dax.depends(job6, last_job)

        self.qc_snapshots.add_vol_surf_snapshot_step(dax, [job3, job5, job6], t1_nii_gz_vol,
                                                     [lh_centered_pial, rh_centered_pial])
        self.qc_snapshots.add_surf_annot_snapshot_step(dax, [last_job, job5, job6], lh_centered_pial, lh_aparc_annot)
        self.qc_snapshots.add_surf_annot_snapshot_step(dax, [last_job, job5, job6], rh_centered_pial, rh_aparc_annot)

        return job3, job4
