# -*- coding: utf-8 -*-

import numpy


class Annotation(object):
    """
    Hold annotation information as region mapping, color mapping and names of regions.

    Has a method to compute face colors using vertices_color_mapping .
    """
    def __init__(self, region_mapping, regions_color_table, region_names):
        self.region_mapping = region_mapping  # ndarray of region_names indices
        self.regions_color_table = regions_color_table  # ndarray matrix that contains a rgba color array for each region
        self.region_names = region_names  # list of region names

    def set_region_mapping(self, new_region_mapping):
        self.region_mapping = new_region_mapping

    def add_region_names_and_colors(self, new_region_names, new_region_colors):
        self.region_names.append(new_region_names)
        if self.regions_color_table is None:
            self.regions_color_table = numpy.array(new_region_colors)
        else:
            self.regions_color_table = numpy.concatenate((self.regions_color_table, new_region_colors), axis=0)

    def add_region_mapping(self, new_region_mapping):
        self.region_mapping.append(new_region_mapping)
        self.stack_region_mapping()

    def stack_region_mapping(self):
        self.region_mapping = numpy.hstack(self.region_mapping)

    def get_region_mapping_by_indices(self, indices):
        return self.region_mapping[indices]

    def compute_face_colors(self, triangles):
        face_colors = []
        converted_colors = self.regions_color_table[:, :4] / 255.0

        for triangle in triangles:
            vertex1_color = converted_colors[self.region_mapping[triangle[0]]] * 0.33
            vertex2_color = converted_colors[self.region_mapping[triangle[1]]] * 0.33
            vertex3_color = converted_colors[self.region_mapping[triangle[2]]] * 0.33
            face_colors.append(vertex1_color + vertex2_color + vertex3_color)

        return face_colors
