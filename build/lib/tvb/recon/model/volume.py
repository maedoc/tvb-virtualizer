# -*- coding: utf-8 -*-

import numpy
import numpy.linalg
from tvb.recon.model.constants import *
from nibabel.affines import apply_affine


class Volume(object):
    """
    Hold volume data, dimensions and affine matrix.

    Has a method that cuts a slice from the volume.
    """

    def __init__(self, data, affine_matrix, header):
        self.data = data  # 3D array
        self.dimensions = data.shape  # array with the length of each data dimension
        # matrix containing voxel to ras transformation
        self.affine_matrix = affine_matrix
        self.header = header

    def get_center_point(self):
        a = numpy.array(self.affine_matrix)
        b = numpy.array(list(numpy.divide(self.dimensions, 2)) + [1])
        ras_vector = a.dot(b)

        return ras_vector[:3]

    def slice_volume(self, projection=SAGITTAL, ras=ORIGIN):
        """
        This determines slice colors and axes coordinates for the slice.
        :param projection: one of sagittal, axial or coronal
        :param ras: 3D point where to do the slicing
        :return: X, Y, 2D data matrix
        """

        affine_inverse = numpy.linalg.inv(self.affine_matrix)
        ijk_ras = numpy.round(apply_affine(affine_inverse, ras)).astype('i')

        slice_index_1, slice_index_2 = X_Y_INDEX[projection]

        slice_data = numpy.zeros(
            (self.dimensions[slice_index_1], self.dimensions[slice_index_2]))
        x_axis_coords = numpy.zeros_like(slice_data)
        y_axis_coords = numpy.zeros_like(slice_data)

        for i in range(self.dimensions[slice_index_1]):
            for j in range(self.dimensions[slice_index_2]):
                ijk_ras[slice_index_1] = i
                ijk_ras[slice_index_2] = j

                ras_coordinates = apply_affine(self.affine_matrix, ijk_ras)
                x_axis_coords[i, j] = ras_coordinates[slice_index_1]
                y_axis_coords[i, j] = ras_coordinates[slice_index_2]

                color = self.data[ijk_ras[0], ijk_ras[1], ijk_ras[2]]
                if isinstance(color, (list, numpy.ndarray)):
                    color = color[0]
                slice_data[i][j] = color

        return x_axis_coords, y_axis_coords, slice_data
