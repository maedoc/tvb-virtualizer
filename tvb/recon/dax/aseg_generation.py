from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax.mappings import AsegFiles, AsegGenJobNames, Inputs, T1Files, T1JobNames, ResamplingFiles


class AsegGeneration(object):
    def __init__(self, subject, lh_labels, rh_labels):
        self.subject = subject
        self.lh_labels = lh_labels
        self.rh_labels = rh_labels

    def add_aseg_generation_steps(self, dax, job_recon):
        lh_aseg = File(AsegFiles.LH_ASEG.value)
        lh_aseg_annot = File(AsegFiles.LH_ASEG_ANNOT.value)
        fs_lut = File(Inputs.FS_LUT.value)
        job5 = Job(AsegGenJobNames.ASEG_CONCAT.value, node_label="lh.aseg surface concatenation")
        job5.addArguments(lh_aseg, lh_aseg_annot, self.lh_labels, fs_lut, self.subject)
        job5.uses(fs_lut, link=Link.INPUT)
        job5.uses(lh_aseg, link=Link.OUTPUT, transfer=True, register=True)
        job5.uses(lh_aseg_annot, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job5)

        rh_aseg = File(AsegFiles.RH_ASEG.value)
        rh_aseg_annot = File(AsegFiles.RH_ASEG_ANNOT.value)
        fs_lut = File(Inputs.FS_LUT.value)
        job6 = Job(AsegGenJobNames.ASEG_CONCAT.value, node_label="rh.aseg surface concatenation")
        job6.addArguments(rh_aseg, rh_aseg_annot, self.rh_labels, fs_lut, self.subject)
        job6.uses(fs_lut, link=Link.INPUT)
        job6.uses(rh_aseg, link=Link.OUTPUT, transfer=True, register=True)
        job6.uses(rh_aseg_annot, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job6)

        lbl_list = map(int, self.lh_labels.strip('"').split() + self.rh_labels.strip('"').split())
        for aseg_label in lbl_list:
            norm_mgz = File(T1Files.NORM_MGZ.value)
            aseg_mgz = File(T1Files.ASEG_MGZ.value)
            aseg_per_region_mgz = File(AsegFiles.ASEG_MGZ.value % aseg_label)
            job1 = Job(AsegGenJobNames.MRI_PRETESS.value, node_label="mri_pretess_%s" % aseg_label)
            job1.addArguments(aseg_mgz, str(aseg_label), norm_mgz, aseg_per_region_mgz)
            job1.uses(aseg_mgz, link=Link.INPUT)
            job1.uses(norm_mgz, link=Link.INPUT)
            job1.uses(aseg_per_region_mgz, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job1)

            dax.depends(job1, job_recon)

            aseg_not_smooth = File(AsegFiles.ASEG_NOT_SMOOTH.value % aseg_label)
            job2 = Job(AsegGenJobNames.MRI_TESSELLATE.value, node_label="mri_tesselate_%s" % aseg_label)
            job2.addArguments(aseg_per_region_mgz, str(aseg_label), aseg_not_smooth)
            job2.uses(aseg_per_region_mgz, link=Link.INPUT)
            job2.uses(aseg_not_smooth, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job2)

            dax.depends(job2, job1)

            aseg_not_smooth_main = File(AsegFiles.ASEG_NOT_SMOOTH_MAIN.value % aseg_label)
            job3 = Job(AsegGenJobNames.MRIS_EXTRACT.value, node_label="mris_extract_%s" % aseg_label)
            job3.addArguments(aseg_not_smooth, aseg_not_smooth_main)
            job3.uses(aseg_not_smooth, link=Link.INPUT)
            job3.uses(aseg_not_smooth_main, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job3)

            dax.depends(job3, job2)

            lh_aseg_lbl = File(AsegFiles.ASEG_LBL_LH.value % aseg_label)
            job4 = Job(AsegGenJobNames.MRIS_SMOOTH.value, node_label="mris_smooth_%s" % aseg_label)
            job4.addArguments("-nw", aseg_not_smooth_main, lh_aseg_lbl)
            job4.uses(aseg_not_smooth_main, link=Link.INPUT)
            job4.uses(lh_aseg_lbl, link=Link.OUTPUT, transfer=False, register=False)
            dax.addJob(job4)

            dax.depends(job4, job3)

            aseg_lbl = File(AsegFiles.ASEG_LBL.value % aseg_label)
            job_rename = Job("mv", node_label="rename %s" % aseg_label)
            job_rename.addArguments(lh_aseg_lbl, aseg_lbl)
            job_rename.uses(lh_aseg_lbl, link=Link.INPUT)
            job_rename.uses(aseg_lbl, link=Link.OUTPUT, transfer=True, register=True)
            dax.addJob(job_rename)

            dax.depends(job_rename, job4)

            if aseg_label in map(int, self.lh_labels.strip('"').split()):
                # Includes cerebellum as a lh region
                job5.uses(aseg_lbl, link=Link.INPUT)
                dax.depends(job5, job_rename)
            else:
                job6.uses(aseg_lbl, link=Link.INPUT)
                dax.depends(job6, job_rename)

        lh_centered_aseg = File(AsegFiles.LH_CENTERED_ASEG.value)
        job7 = Job(T1JobNames.MRIS_CONVERT.value, node_label="mris_convert to center lh.aseg")
        job7.addArguments("--to-scanner", lh_aseg, lh_centered_aseg)
        job7.uses(lh_aseg, link=Link.INPUT)
        job7.uses(lh_centered_aseg, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job7)

        dax.depends(job7, job5)

        rh_centered_aseg = File(AsegFiles.RH_CENTERED_ASEG.value)
        job8 = Job(T1JobNames.MRIS_CONVERT.value, node_label="mris_convert to center rh.aseg")
        job8.addArguments("--to-scanner", rh_aseg, rh_centered_aseg)
        job8.uses(rh_aseg, link=Link.INPUT)
        job8.uses(rh_centered_aseg, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job8)

        dax.depends(job8, job6)

        return job7, job8
