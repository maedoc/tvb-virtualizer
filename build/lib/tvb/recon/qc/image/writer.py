# -*- coding: utf-8 -*-

import os
import numpy
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from mpl_toolkits.mplot3d import Axes3D
from tvb.recon.logger import get_logger
from tvb.recon.model.constants import SNAPSHOT_EXTENSION


class ImageWriter(object):
    logger = get_logger(__name__)

    contour_colors = ['y', 'r', 'b', 'g', 'm', 'c', 'w', 'k']
    volume_cmaps = ['gray', 'hot', 'jet']
    transparency = [0.3, 0.5]

    def __init__(self, snapshots_directory):
        self.snapshots_directory = snapshots_directory

        if not os.path.exists(self.snapshots_directory):
            os.mkdir(self.snapshots_directory)

    def get_path(self, result_name):
        return os.path.join(self.snapshots_directory,
                            result_name + SNAPSHOT_EXTENSION)

    def write_matrix(self, x, y, matrix, result_name, cmap=volume_cmaps[0]):
        pyplot.pcolormesh(x, y, matrix, cmap=cmap)
        pyplot.axes().set_aspect('equal', 'datalim')
        pyplot.axis('off')
        pyplot.savefig(self.get_path(result_name),
                       bbox_inches='tight', pad_inches=0.0)
        pyplot.clf()

    def write_2_matrices(self, x, y, matrix_background, x1,
                         y1, matrix_overlap, result_name):
        pyplot.pcolormesh(x, y, matrix_background, cmap=self.volume_cmaps[0])
        # masked = numpy.ma.masked_where(matrix_overlap < 0.9, matrix_overlap)
        pyplot.pcolormesh(x1, y1, matrix_overlap, cmap=self.volume_cmaps[
                          1], alpha=self.transparency[0])
        pyplot.axes().set_aspect('equal', 'datalim')
        pyplot.axis('off')
        pyplot.savefig(self.get_path(result_name),
                       bbox_inches='tight', pad_inches=0.0)
        pyplot.clf()

    def write_3_matrices(self, x, y, matrix_background, x1, y1, matrix_overlap_1, x2, y2, matrix_overlap_2,
                         result_name):
        pyplot.pcolormesh(x, y, matrix_background, cmap=self.volume_cmaps[0])
        pyplot.pcolormesh(x1, y1, matrix_overlap_1, cmap=self.volume_cmaps[
                          1], alpha=self.transparency[0])
        pyplot.pcolormesh(x2, y2, matrix_overlap_2, cmap=self.volume_cmaps[
                          2], alpha=self.transparency[1])
        pyplot.axes().set_aspect('equal', 'datalim')
        pyplot.axis('off')
        pyplot.savefig(self.get_path(result_name),
                       bbox_inches='tight', pad_inches=0.0)

    def write_surface_with_annotation(self, surface, annot, result_name,
                                      positions=[(0, 0), (0, 90), (0, 180), (0, 270), (90, 0), (270, 0)]):
        x = surface.vertices[:, 0]
        y = surface.vertices[:, 1]
        z = surface.vertices[:, 2]

        fig = pyplot.figure()

        ax = Axes3D(fig, aspect='equal')

        min = numpy.min([numpy.min(x), numpy.min(y), numpy.min(z)])
        max = numpy.max([numpy.max(x), numpy.max(y), numpy.max(z)])

        ax.set_xlim3d(min, max)
        ax.set_ylim3d(min, max)
        ax.set_zlim3d(min, max)

        if annot is not None:
            face_colors = annot.compute_face_colors(surface.triangles)
            normals = surface.compute_normals()
            face_colors = ax._shade_colors(face_colors, normals)

        poly_line = ax.plot_trisurf(x, y, z, triangles=surface.triangles)

        if annot is not None:
            poly_line.set_edgecolor(face_colors)
            poly_line.set_facecolor(face_colors)

        pyplot.axis('off')

        snapshot_index = 0
        for e, a in positions:
            ax.view_init(elev=e, azim=a)
            ax.dist = 6
            pyplot.savefig(self.get_path(
                result_name + str(snapshot_index)), dpi=fig.dpi)
            snapshot_index += 1

        self.logger.info("The 6 snapshots were generated")

    def save_figure(self, result_name):
        pyplot.axes().set_aspect('equal', 'datalim')
        pyplot.axis('off')
        pyplot.savefig(self.get_path(result_name),
                       bbox_inches='tight', pad_inches=0.0)

    def write_matrix_and_surfaces(self, x_axis_coords, y_axis_coords, matrix_background,
                                  surface_x_array, surface_y_array, surface_index, clear_flag):
        if clear_flag:
            pyplot.clf()
            pyplot.pcolormesh(x_axis_coords, y_axis_coords,
                              matrix_background, cmap=self.volume_cmaps[0])
        color_index = surface_index % len(self.contour_colors)
        for contour in range(len(surface_x_array)):
            pyplot.plot(surface_x_array[contour][:], surface_y_array[
                        contour][:], self.contour_colors[color_index])
