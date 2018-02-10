# -*- coding: utf-8 -*-

import os

import numpy

from tvb.recon.algo.service.volume import VolumeService
from tvb.recon.io.factory import IOUtils
from tvb.recon.model.volume import Volume
from tvb.recon.tests.base import get_temporary_files_path, remove_temporary_test_files


def teardown_module():
    remove_temporary_test_files()


def test_label_vol_from_tdi():
    service = VolumeService()
    data = numpy.array([[[0, 0, 1], [1, 2, 0]], [[2, 1, 3], [3, 1, 0]], [
                       [0, 0, 1], [1, 2, 0]], [[2, 1, 3], [3, 1, 0]]])
    volume = Volume(data, [], None)
    labeled_volume = service._label_volume(volume, 0.5)
    assert numpy.array_equal(labeled_volume.data,
                             [[[0, 0, 1], [2, 3, 0]], [[4, 5, 6], [7, 8, 0]], [[0, 0, 9], [10, 11, 0]],
                              [[12, 13, 14], [15, 16, 0]]])


def test_simple_label_config():
    service = VolumeService()
    data = numpy.array(
        [[[0, 0, 1], [1, 2, 0]], [[2, 1, 1000], [1000, 1, 0]], [[0, 0, 1], [1, 2, 0]], [[2, 1, 1000], [3, 1, 0]]])
    in_volume = Volume(data, [], None)
    out_volume = service._label_config(in_volume)
    assert numpy.array_equal(out_volume.data, [[[0, 0, 1], [1, 2, 0]], [[2, 1, 4], [4, 1, 0]], [[0, 0, 1], [1, 2, 0]],
                                               [[2, 1, 4], [3, 1, 0]]])


def test_label_with_dilation():
    service = VolumeService()

    ct_mask_data = numpy.array(
        [[[0, 0, 0], [0, 1, 0], [0, 1, 0]], [[1, 1, 1], [0, 0, 0], [0, 0, 0]], [[0, 0, 1], [0, 0, 0], [0, 0, 1]]])
    ct_mask_volume = Volume(ct_mask_data, [[1, 0, 0, 0], [0, 1, 0, 0], [
                            0, 0, 1, 0], [0, 0, 0, 1]], None)
    ct_mask_path = get_temporary_files_path("ct_mask.nii.gz")
    IOUtils.write_volume(ct_mask_path, ct_mask_volume)

    ct_dil_mask_data = numpy.array(
        [[[0, 0, 0], [1, 1, 1], [0, 1, 0]], [[1, 1, 1], [0, 0, 0], [0, 0, 0]], [[0, 1, 1], [0, 0, 0], [0, 1, 1]]])
    ct_dil_mask_volume = Volume(ct_dil_mask_data, [[1, 0, 0, 0], [
                                0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], None)
    ct_dil_mask_path = get_temporary_files_path("ct_dil_mask.nii.gz")
    IOUtils.write_volume(ct_dil_mask_path, ct_dil_mask_volume)

    ct_result = get_temporary_files_path("ct_res.nii.gz")

    service.label_with_dilation(ct_mask_path, ct_dil_mask_path, ct_result)

    assert os.path.exists(ct_mask_path)
    assert os.path.exists(ct_dil_mask_path)
    assert os.path.exists(ct_result)

    vol = IOUtils.read_volume(ct_result)
    assert numpy.array_equal(numpy.unique(vol.data), [0, 1, 2, 3])


def test_remove_zero_connectivity():
    service = VolumeService()

    data = numpy.array([[[0, 0, 1], [2, 3, 0]], [[4, 0, 0], [0, 0, 0]]])
    volume = Volume(data, [[1, 0, 0, 0], [0, 1, 0, 0],
                           [0, 0, 1, 0], [0, 0, 0, 1]], None)
    volume_path = get_temporary_files_path("tdi_lbl.nii.gz")

    IOUtils.write_volume(volume_path, volume)

    in_connectivity = numpy.array(
        [[10, 1, 0, 3], [0, 10, 0, 2], [0, 0, 0, 0], [0, 0, 0, 10]])
    connectivity_path = get_temporary_files_path("conn.csv")
    numpy.savetxt(connectivity_path, in_connectivity, fmt='%1d')

    tract_lengths_path = get_temporary_files_path("tract_lengths.csv")
    numpy.savetxt(tract_lengths_path, in_connectivity, fmt='%1d')

    service.remove_zero_connectivity_nodes(
        volume_path, connectivity_path, tract_lengths_path)

    assert os.path.exists(os.path.splitext(connectivity_path)[0] + ".npy")
    assert os.path.exists(os.path.splitext(tract_lengths_path)[0] + ".npy")

    vol = IOUtils.read_volume(volume_path)
    assert len(numpy.unique(vol.data)) == 4

    conn = numpy.array(numpy.genfromtxt(connectivity_path, dtype='int64'))
    assert numpy.array_equal(conn, [[20, 1, 3], [1, 20, 2], [3, 2, 20]])
