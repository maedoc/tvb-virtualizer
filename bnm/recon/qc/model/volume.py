# -*- coding: utf-8 -*-
from nibabel.affines import apply_affine
import numpy.linalg as nlp
import numpy

from bnm.recon.snapshot.model.constants import sagittal, coronal, axial


class Volume(object):
    dims = None
    ras_center_point = [128, 128, 128]
    data = None  # 3D matrix
    affine_matrix = None
    transparency = 1.0
    color_map = None  # Reference to ColorMap obj, or empty

    def __init__(self, nifti_data, dims, nifti_affine_matrix):
        self.data = nifti_data
        self.dims = dims
        self.affine_matrix = nifti_affine_matrix

    def get_axial(self, index):
        return self.data[:,index]

    def align(self, projection, ras):
        # TODO align diffusion images  which are smaller
        ras_current_point = [0 for x in range(3)]

        if projection == sagittal:
            ras_current_point[0] = ras[0]
            ras_index_1 = 1
            ras_index_2 = 2
        elif projection == coronal:
            ras_current_point[1] = ras[1]
            ras_index_1 = 0
            ras_index_2 = 2
        elif projection == axial:
            ras_current_point[2] = ras[2]
            ras_index_1 = 0
            ras_index_2 = 1

        volume_center_voxel = (numpy.array(self.dims[:3])) / 2
        ras_new_center = self.affine_matrix.dot(list(volume_center_voxel) + [1])
        ras_new_center = map(int, ras_new_center)
        aligned_data = [[0 for x in range(self.dims[ras_index_1])] for y in range(self.dims[ras_index_2])]

        imin = - self.ras_center_point[ras_index_1] + ras_new_center[ras_index_1]
        imax = self.ras_center_point[ras_index_1] + ras_new_center[ras_index_1]
        jmin = - self.ras_center_point[ras_index_2] + ras_new_center[ras_index_2]
        jmax = self.ras_center_point[ras_index_2] + ras_new_center[ras_index_2]

        inv = nlp.inv(self.affine_matrix)
        for i in range(imin, imax):
            for j in range(jmin, jmax):
                ras_current_point[ras_index_1] = i
                ras_current_point[ras_index_2] = j
                v = apply_affine(inv, ras_current_point)
                v = map(int, v)
                aligned_data[jmax - 1 - j][i - imin] = self.data[v[0], v[1], v[2]]

        return aligned_data

class ColorMap(object):
    # dict(VolumeValue : [r, g, b])
    colors = dict()
