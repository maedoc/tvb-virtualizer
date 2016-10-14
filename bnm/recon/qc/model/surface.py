# -*- coding: utf-8 -*-
import meshcut
import numpy

from bnm.recon.snapshot.model.constants import sagittal, coronal, axial


class Surface(object):

    vertices = None
    triangles = None
    center_value = 128
    vol_geom_center_ras = None
    gii_reference = None
    contour_color = None
    show_all = False

    plane_normals = {
        sagittal : (1,0,0),
        coronal : (0,1,0),
        axial : (0,0,1)
    }

    x_y_index = {
        sagittal : [1, 2],
        coronal : [0, 2],
        axial : [0, 1]
    }

    def __init__(self, vertices, triangles, vol_geom_center_ras):
        self.vertices = vertices
        self.triangles = triangles
        self.vol_geom_center_ras = vol_geom_center_ras


    def get_plane_origin(self, ras):
        plane_origin = numpy.subtract(ras, self.vol_geom_center_ras)
        return list(plane_origin)


    def get_x_array(self, projection, ras):
        contours = meshcut.cross_section(self.vertices, self.triangles, plane_orig=self.get_plane_origin(ras), plane_normal=self.plane_normals[projection])
        mat = [0 for x in range(len(contours))]
        for s in range(0, len(contours)):
            mat[s] = self.center_value + contours[s][:, self.x_y_index[projection][0]]
        return mat


    def get_y_array(self, projection, ras):
        contours = meshcut.cross_section(self.vertices, self.triangles, plane_orig=self.get_plane_origin(ras), plane_normal=self.plane_normals[projection])
        mat = [0 for x in range(len(contours))]
        for s in range(0, len(contours)):
            mat[s] = self.center_value - contours[s][:, self.x_y_index[projection][1]]
        return mat

