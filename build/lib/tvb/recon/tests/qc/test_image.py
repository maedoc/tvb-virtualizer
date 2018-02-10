# -*- coding: utf-8 -*-

import os
import unittest
import numpy
from tvb.recon.io.factory import IOUtils
from tvb.recon.model.constants import SNAPSHOTS_DIRECTORY, SNAPSHOT_NAME, AXIAL
from tvb.recon.qc.image.processor import ImageProcessor
from tvb.recon.qc.image.writer import ImageWriter
from tvb.recon.tests.base import get_data_file


class ImageTest(unittest.TestCase):

    def setUp(self):
        self.snapshot_number = 0
        self.subject_modif = "fsaverage_modified"
        self.subject = "freesurfer_fsaverage"
        self.head2 = "head2"
        self.mri_path = "mri"
        self.surf_path = "surf"
        self.annot_path = "label"
        self.T1 = "T1.nii.gz"
        self.brain = "brain.nii.gz"
        self.surf = "lh.pial"
        self.gifti_surf = "lh.pial.gii"
        self.annot = "lh.aparc.annot"
        self.processor = ImageProcessor(SNAPSHOTS_DIRECTORY,
                                        self.snapshot_number)
        os.environ["MRI"] = os.path.join("data",
                                         self.subject_modif,
                                         self.mri_path)
        os.environ["T1_RAS"] = self.T1
        os.environ["SUBJ_DIR"] = os.path.join("data", self.subject_modif)

    def tearDown(self):
        if not os.path.exists(SNAPSHOTS_DIRECTORY):
            return
        for file_path in os.listdir(SNAPSHOTS_DIRECTORY):
            os.remove(os.path.join(SNAPSHOTS_DIRECTORY, file_path))
        os.rmdir(SNAPSHOTS_DIRECTORY)

    def _assert_writer_path_exists(self, fname):
        self.assertTrue(
            os.path.exists(
                self.processor.writer.get_path(fname)))

    def _assert_snapshot_exists(self, view): pass

    def test_show_single_volume(self):
        volume_path = get_data_file(self.subject_modif, self.mri_path, self.T1)
        self.processor.show_single_volume(volume_path, False)
        resulted_file_name = self.processor.generate_file_name(
            AXIAL, SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_overlap_2_volumes(self):
        background_path = get_data_file(
            self.subject_modif, self.mri_path, self.T1)
        overlay_path = get_data_file(
            self.subject_modif, self.mri_path, self.brain)
        self.processor.overlap_2_volumes(background_path, overlay_path, False)
        resulted_file_name = self.processor.generate_file_name(AXIAL, SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_overlap_3_volumes(self):
        background_path = get_data_file(
            self.subject_modif, self.mri_path, self.T1)
        overlay1_path = get_data_file(
            self.subject_modif, self.mri_path, self.brain)
        overlay2_path = get_data_file(
            self.subject_modif, self.mri_path, self.brain)
        self.processor.overlap_3_volumes(
            background_path, overlay1_path, overlay2_path, False)
        resulted_file_name = self.processor.generate_file_name(AXIAL,
                                                            SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_overlap_surface_annotation(self):
        writer = ImageWriter(SNAPSHOTS_DIRECTORY)
        surface_path = get_data_file(self.head2, "SurfaceCortical.h5")
        surface = IOUtils.read_surface(surface_path, False)
        annot_path = get_data_file(self.head2, "RegionMapping.h5")
        annot = IOUtils.read_annotation(annot_path)
        annot.region_names = ['reg1', 'reg2']
        annot.regions_color_table = numpy.array(
            [[200, 200, 200, 255, 30567], [100, 150, 200, 255, 30568]])
        resulted_file_name = self.processor.generate_file_name(
            'surface_annotation', SNAPSHOT_NAME)
        writer.write_surface_with_annotation(surface, annot, resulted_file_name)
        fname = '%s0' % (resulted_file_name, )
        self._assert_writer_path_exists(fname)

    def test_overlap_volume_surface(self):
        volume_path = get_data_file(self.subject_modif, self.mri_path, self.T1)
        surface_path = get_data_file(self.subject, self.surf_path, self.surf)
        self.processor.overlap_volume_surfaces(
            volume_path, [surface_path], False, False)
        resulted_file_name = self.processor.generate_file_name(AXIAL,
                                                            SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_overlap_volume_centered_surface(self):
        volume_path = get_data_file(self.subject_modif, self.mri_path, self.T1)
        surface_path = get_data_file(self.subject, self.surf_path, self.surf)
        self.processor.overlap_volume_surfaces(
            volume_path, [surface_path], True, False)
        resulted_file_name = self.processor.generate_file_name(
            AXIAL, SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_overlap_volume_gifti_surface(self):
        volume_path = get_data_file(self.subject_modif, self.mri_path, self.T1)
        surface_path = get_data_file(
            self.subject_modif, self.surf_path, self.gifti_surf)
        self.processor.overlap_volume_surfaces(
            volume_path, [surface_path], False, False)
        resulted_file_name = self.processor.generate_file_name(
            AXIAL, SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)

    def test_show_aparc_aseg_with_new_values(self):
        volume_path = get_data_file(
            self.subject_modif, self.mri_path, "aparc+aseg.nii.gz")
        conn_measure_path = get_data_file("connectivity_measure.txt")
        self.processor.show_aparc_aseg_with_new_values(
            volume_path, conn_measure_path, '', False)
        resulted_file_name = self.processor.generate_file_name(
            AXIAL, SNAPSHOT_NAME)
        self._assert_writer_path_exists(resulted_file_name)
