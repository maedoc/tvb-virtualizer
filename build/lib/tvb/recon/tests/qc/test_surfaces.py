# -*- coding: utf-8 -*-

import os

import pytest
from nibabel.py3k import FileNotFoundError

from tvb.recon.io.factory import IOUtils
from tvb.recon.tests.base import get_data_file, get_temporary_files_path, remove_temporary_test_files

TEST_FS_SUBJECT = "freesurfer_fsaverage"
TEST_MODIF_SUBJECT = "fsaverage_modified"
TEST_SURFACE_FOLDER = "surf"


def teardown_module():
    remove_temporary_test_files()


def test_parse_fs_surface():
    file_path = get_data_file(TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    surf = IOUtils.read_surface(file_path, False)
    assert len(surf.triangles) == 327680


def test_parse_fs_centered_surface():
    file_path = get_data_file(TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    surf = IOUtils.read_surface(file_path, True)
    assert len(surf.triangles) == 327680


def test_parse_centered_fs_surface():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh-centered.pial")
    surf = IOUtils.read_surface(file_path, False)
    assert surf.center_ras == [0, 0, 0]


def test_parse_not_existing_fs_surface():
    file_path = "not_existing_surface.pial"
    with pytest.raises(IOError):
        IOUtils.read_surface(file_path, False)


def test_parse_not_surface():
    file_path = get_data_file(TEST_FS_SUBJECT, "label", "lh.aparc.annot")
    with pytest.raises(ValueError):
        IOUtils.read_surface(file_path, False)


def test_parse_gifti_surface():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial.gii")
    surf = IOUtils.read_surface(file_path, False)
    assert len(surf.triangles) == 327680


def test_parse_gifti_centered_surface():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial.gii")
    surf = IOUtils.read_surface(file_path, True)
    assert len(surf.triangles) == 327680


def test_parse_not_existing_gifti_surface():
    file_path = "not_existing_surface.gii"
    with pytest.raises(FileNotFoundError):
        IOUtils.read_surface(file_path, False)


def test_parse_h5_surface():
    h5_path = get_data_file('head2', 'SurfaceCortical.h5')
    surface = IOUtils.read_surface(h5_path, False)
    assert len(surface.vertices) == 16
    assert len(surface.triangles) == 24


def test_write_fs_surface():
    file_path = get_data_file(TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    original_surface = IOUtils.read_surface(file_path, False)
    triangles_number = len(original_surface.triangles)

    output_file_path = get_temporary_files_path("lh-test.pial")
    IOUtils.write_surface(output_file_path, original_surface)

    new_surface = IOUtils.read_surface(output_file_path, False)
    assert triangles_number == len(new_surface.triangles) == 327680


def test_write_gifti_surface():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial.gii")
    original_surface = IOUtils.read_surface(file_path, False)
    triangles_number = len(original_surface.triangles)

    output_file_path = get_temporary_files_path("lh-test.pial.gii")
    IOUtils.write_surface(output_file_path, original_surface)

    new_surface = IOUtils.read_surface(output_file_path, False)
    assert triangles_number == len(new_surface.triangles) == 327680


def test_read_transformation_matrix_from_fs_metadata():
    file_path = get_data_file(TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    surface_io = IOUtils.surface_io_factory(file_path)
    surf = surface_io.read(file_path, False)
    matrix = surface_io.read_transformation_matrix_from_metadata(
        surf.get_main_metadata())
    assert matrix.tolist() == [[-1, 0, 0, 0],
                               [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]


def test_write_transformation_matrix_fs_metadata():
    file_path = get_data_file(TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    surface_io = IOUtils.surface_io_factory(file_path)
    surf = surface_io.read(file_path, False)
    surface_io.write_transformation_matrix(surf.get_main_metadata())
    matrix = surface_io.read_transformation_matrix_from_metadata(
        surf.get_main_metadata())
    assert matrix.tolist() == [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [
        0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def test_read_transformation_matrix_from_gifti_metadata():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial.gii")
    surface_io = IOUtils.surface_io_factory(file_path)
    surf = surface_io.read(file_path, False)
    matrix = surface_io.read_transformation_matrix_from_metadata(
        surf.get_main_metadata())
    assert matrix == [[-1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]


def test_write_transformation_matrix_gifti_metadata():
    file_path = get_data_file(
        TEST_MODIF_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial.gii")
    surface_io = IOUtils.surface_io_factory(file_path)
    surf = surface_io.read(file_path, False)
    surface_io.write_transformation_matrix(surf.get_main_metadata())
    matrix = surface_io.read_transformation_matrix_from_metadata(
        surf.get_main_metadata())
    assert matrix == [[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [
        0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]]


def test_write_write_brain_visa_surf():
    surface_path = get_data_file(
        TEST_FS_SUBJECT, TEST_SURFACE_FOLDER, "lh.pial")
    out_path = get_temporary_files_path("lh.pial.tri")

    surface = IOUtils.read_surface(surface_path, False)
    IOUtils.write_surface(out_path, surface)

    assert os.path.exists(out_path)
