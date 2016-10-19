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

    # This method is not currently used.
    # Applies the rotation_matrix on every surface vertex.
    # Rotates surface contour and it is displayed similar to freeview.
    def apply_rotation_matrix(self, contour):
        # rotation_matrix should be read from .gii metadata
        rotation_matrix = numpy.array([[-1, 0, 0], [0, 0, -1], [0, 1, 0]])
        new_verts = [[0 for _ in xrange(3)] for _ in xrange(len(contour))]

        for i in xrange(0, len(contour)):
            new_verts[i] = rotation_matrix.dot(contour[i])

        return numpy.array(new_verts)

    def __init__(self, vertices, triangles, vol_geom_center_ras):
        self.vertices = vertices
        self.triangles = triangles
        self.vol_geom_center_ras = vol_geom_center_ras


    def get_plane_origin(self, ras):
        plane_origin = numpy.subtract(ras, self.vol_geom_center_ras)
        return list(plane_origin)


    def get_x_y_array(self, projection, ras):
        # TODO decimated surface contour is incomplete
        contours = meshcut.cross_section(self.vertices, self.triangles, plane_orig=self.get_plane_origin(ras), plane_normal=self.plane_normals[projection])
        x_array = [0 for _ in xrange(len(contours))]
        y_array = [0 for _ in xrange(len(contours))]
        for s in xrange(0, len(contours)):
            x_array[s] = self.center_value + contours[s][:, self.x_y_index[projection][0]]
            y_array[s] = self.center_value - contours[s][:, self.x_y_index[projection][1]]
        return x_array, y_array


    def compute_normals(self):
        normals = [[0 for _ in xrange(0, 3)] for _ in xrange(0, len(self.triangles))]

        for i, tri in enumerate(self.triangles):
            u = self.vertices[tri[1]] - self.vertices[tri[0]]
            v = self.vertices[tri[2]] - self.vertices[tri[0]]
            normals[i][0] = u[1] * v[2] - u[2] * v[1]
            normals[i][1] = u[2] * v[0] - u[0] * v[2]
            normals[i][2] = u[0] * v[1] - u[1] * v[0]

        return normals