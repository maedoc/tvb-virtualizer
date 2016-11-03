# -*- coding: utf-8 -*-

import nibabel
from bnm.recon.snapshot.model.volume import Volume


class VolumeParser(object):
    """
    This class reads content of a NIFTI file and returns a Volume Object
    """

    def parse(self, data_file):
        nifti_image = nibabel.load(data_file)
        nifti_affine_matrix = nifti_image.affine
        nifti_data = nifti_image.get_data()
        nifti_header = nifti_image.header
        nifti_dims = nifti_header.get_data_shape()

        return Volume(nifti_data, nifti_dims, nifti_affine_matrix)
