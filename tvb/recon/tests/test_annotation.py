# -*- coding: utf-8 -*-

# imports
import os
import importlib
from collections import OrderedDict
from tvb.recon.io.factory import IOUtils
from tvb.recon.tests.base import BaseTest, get_data_file


_expected_region_names = [
    'unknown', 'bankssts', 'caudalanteriorcingulate', 'caudalmiddlefrontal',
    'corpuscallosum', 'cuneus', 'entorhinal', 'fusiform', 'inferiorparietal',
    'inferiortemporal', 'isthmuscingulate', 'lateraloccipital',
    'lateralorbitofrontal', 'lingual', 'medialorbitofrontal',
    'middletemporal', 'parahippocampal', 'paracentral', 'parsopercularis',
    'parsorbitalis', 'parstriangularis', 'pericalcarine', 'postcentral',
    'posteriorcingulate', 'precentral', 'precuneus',
    'rostralanteriorcingulate', 'rostralmiddlefrontal', 'superiorfrontal',
    'superiorparietal', 'superiortemporal', 'supramarginal', 'frontalpole',
    'temporalpole', 'transversetemporal', 'insula']

_expected_color_lut_names = [
    'Unknown', 'Left-Cerebral-Exterior', 'Left-Cerebral-White-Matter',
    'Left-Thalamus-Proper', 'Left-Caudate', 'ctx-lh-unknown', 'ctx-lh-bankssts',
    'ctx-rh-unknown', 'ctx-rh-bankssts'
]

_expected_color_lut_labels = [0, 1, 2, 10, 11, 1000, 1001, 2000, 2001]


class IOTests(BaseTest):
    """ iotests class."""

    def setUp(self):
        """set up contain the subject and annot path to label"""
        super().setUp()
        self.subject = 'freesurfer_fsaverage'
        self.annot_path = 'label'

    def test_parse_annotation(self):
        """ testing the annotation using get_date_file"""
        file_path = get_data_file(
            self.subject, self.annot_path, "lh.aparc.annot")
        annot = IOUtils.read_annotation(file_path)
        self.assertEqual(_expected_region_names, annot.region_names)

    def test_parse_not_existent_annotation(self):
        """ testing the annotation if not esistent create one using file_path"""
        file_path = "not_existent_annotation.annot"
        annotation_io = IOUtils.annotation_io_factory(file_path)
        self.assertRaises(IOError, annotation_io.read, file_path)

    def test_parse_not_annotation(self):
        file_path = get_data_file(self.subject, "surf", "lh.pial")
        annotation_io = IOUtils.annotation_io_factory(file_path)
        self.assertRaises(ValueError, annotation_io.read, file_path)

    def test_parse_h5_annotation(self):
        """ test h5 annotation using two get_data_file head2, RegionMapping.h5.'"""
        h5_path = get_data_file('head2', 'RegionMapping.h5')
        annotation = IOUtils.read_annotation(h5_path)
        self.assertEqual(annotation.region_mapping.size, 16)

    def test_write_annotation(self):
        """ writing the new annotation using file_path and output path to temp_file_path"""
        file_path = get_data_file(
            self.subject, self.annot_path, "lh.aparc.annot")
        annotation = IOUtils.read_annotation(file_path)
        out_annotation_path = self.temp_file_path("lh-test.aparc.annot")
        IOUtils.write_annotation(out_annotation_path, annotation)
        new_annotation = IOUtils.read_annotation(out_annotation_path)
        self.assertEqual(annotation.region_names, new_annotation.region_names)


class ServiceTests(BaseTest):
    """Service test class """

    def setUp(self):
        super().setUp()
        os.environ["FREESURFER_HOME"] = ""
        from tvb.recon.algo.service import annotation
        importlib.reload(annotation)
        self.annotation = annotation
        self.color_lut_name = "colorLUT.txt"
        self.subject = 'freesurfer_fsaverage'

    def test_read_lut_by_name(self,):
        lut_path = get_data_file(self.color_lut_name)
        service = self.annotation.AnnotationService()
        labels, names, colors = service.read_lut(
            lut_path=lut_path, key_mode='name')
        self.assertIsInstance(labels, OrderedDict)
        self.assertIsInstance(colors, OrderedDict)
        self.assertEqual(names, _expected_color_lut_names)
        self.assertEqual(list(labels.keys()), _expected_color_lut_names)
        self.assertEqual(list(colors.keys()), _expected_color_lut_names)

    def test_read_lut_by_label(self,):
        lut_path = get_data_file(self.color_lut_name)
        service = self.annotation.AnnotationService()
        labels, names, colors = service.read_lut(
            lut_path=lut_path, key_mode='label')
        self.assertIsInstance(names, OrderedDict)
        self.assertIsInstance(colors, OrderedDict)
        self.assertEqual(labels, _expected_color_lut_labels)
        self.assertEqual(list(names.keys()), _expected_color_lut_labels)
        self.assertEqual(list(colors.keys()), _expected_color_lut_labels)

    def test_rgb_to_fs_magic_number(self,):
        service = self.annotation.AnnotationService()
        fs_magic_number = service.rgb_to_fs_magic_number([100, 100, 100])
        self.assertEqual(fs_magic_number, 6579300)

    def test_annot_to_lut(self,):
        service = self.annotation.AnnotationService()
        lut_path = self.temp_file_path('colorLUT-temp.txt')
        service.annot_to_lut(
            get_data_file('freesurfer_fsaverage', 'label', 'lh.aparc.annot'),
            lut_path=lut_path,
            subject=self.subject
        )
        self.assertTrue(os.path.exists(lut_path))

    def test_lut_to_annot_names_ctab(self,):
        service = self.annotation.AnnotationService()
        lut_path = get_data_file(self.color_lut_name)
        names1, ctab1 = service.lut_to_annot_names_ctab(lut_path=lut_path)
        names2, ctab2 = service.lut_to_annot_names_ctab(
            lut_path=lut_path,
            labels=[0, 1, 2]
        )
        names3, ctab3 = service.lut_to_annot_names_ctab(
            lut_path=lut_path,
            labels="0 1 2"
        )
        expected = 'Unknown'
        self.assertEqual(expected, names1[0])
        self.assertEqual(expected, names2[0])
        self.assertEqual(expected, names3[0])
        expected = all([0, 0, 0, 0, service.rgb_to_fs_magic_number([0, 0, 0])])
        self.assertEqual(expected, all(ctab1[0]))
        self.assertEqual(expected, all(ctab2[0]))
        self.assertEqual(expected, all(ctab3[0]))

    def test_annot_names_to_labels(self,):
        service = self.annotation.AnnotationService()
        lut_path = get_data_file(self.color_lut_name)
        labels = service.annot_names_to_labels(['Unknown'], lut_path=lut_path)
        self.assertEqual(0, labels[0])
        labels = service.annot_names_to_labels(
            ['unknown'],
            add_string='ctx-lh-',
            lut_path=lut_path
        )
        self.assertEqual(1000, labels[0])
        labels = service.annot_names_to_labels(
            ['bankssts'],
            add_string='ctx-rh-',
            lut_path=lut_path
        )
        self.assertEqual(2001, labels[0])

    def test_read_input_labels(self,):
        service = self.annotation.AnnotationService()
        labels = '0 1'
        labels1 = service.read_input_labels(labels=labels, ctx='rh')
        labels2 = service.read_input_labels(labels=labels, ctx='lh')
        expect = 38
        self.assertEqual(expect, len(labels1))
        self.assertEqual(expect, len(labels2))
        labels = service.read_input_labels()
        self.assertEqual(0, len(labels))
