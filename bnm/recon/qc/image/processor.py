# -*- coding: utf-8 -*-

import os

from bnm.recon.snapshot.image.writer import ImageWriter
from bnm.recon.snapshot.parser.annotation import AnnotationParser
from bnm.recon.snapshot.parser.generic import GenericParser
from bnm.recon.snapshot.parser.surface import SurfaceParser
from bnm.recon.snapshot.parser.volume import VolumeParser
from bnm.recon.snapshot.model.constants import projections


class ImageProcessor(object):
    snapshot_name = "snapshot"
    snapshot_extension = ".png"

    def __init__(self):
        self.parser_volume = VolumeParser()
        self.parser_surface = SurfaceParser()
        self.generic_parser = GenericParser()
        self.annotation_parser = AnnotationParser()
        self.writer = ImageWriter()
        self.snapshot_count = int(os.environ['SNAPSHOT_NUMBER'])


    def _new_name(self, current_projection):
        file_name = self.snapshot_name + str(self.snapshot_count) + current_projection + self.snapshot_extension
        return file_name


    def overlap_2_volumes(self, background_path, overlay_path):

        volume_background = self.parser_volume.parse(background_path)
        volume_overlay = self.parser_volume.parse(overlay_path)
        ras = self.generic_parser.get_ras_coordinates()

        for i in projections:
            background_matrix = volume_background.align(i, ras)
            overlay_matrix = volume_overlay.align(i, ras)
            self.writer.write_2_matrices(background_matrix, overlay_matrix, self._new_name(i))


    def overlap_3_volumes(self, background_path, overlay_1_path, overlay_2_path):

        volume_background = self.parser_volume.parse(background_path)
        volume_overlay_1 = self.parser_volume.parse(overlay_1_path)
        volume_overlay_2 = self.parser_volume.parse(overlay_2_path)

        ras = self.generic_parser.get_ras_coordinates()

        for i in projections:
            background_matrix = volume_background.align(i, ras)
            overlay_1_matrix = volume_overlay_1.align(i, ras)
            overlay_2_matrix = volume_overlay_2.align(i, ras)
            self.writer.write_3_matrices(background_matrix, overlay_1_matrix, overlay_2_matrix, self._new_name(i))


    def overlap_surface_annotation(self, surface_path, annotation):
        annot = self.annotation_parser.parse(annotation)
        surface = self.parser_surface.parse(surface_path)
        self.writer.write_surface_with_annotation(surface, annot, self._new_name('surf'))


    def overlap_volume_surface(self, volume_background, surface_path):
        # TODO surface contour is a little lower than it should be
        # TODO the image and the contour are reversed (compared to freeview)
        volume = self.parser_volume.parse(volume_background)
        surface = self.parser_surface.parse(surface_path)
        ras = self.generic_parser.get_ras_coordinates()
        for i in projections:
            background_matrix = volume.align(i, ras)
            x_array, y_array = surface.get_x_y_array(i, ras)
            self.writer.write_matrix_and_surface(background_matrix, x_array, y_array, self._new_name(i))


    def overlap_volume_surfaces(self, volume_background, surfaces_path, resampled_name):
        if resampled_name != '':
            resampled_name = '.' + resampled_name
        volume = self.parser_volume.parse(volume_background)
        ras = self.generic_parser.get_ras_coordinates()
        print ras
        for i in projections:
            clear_flag = 'true'
            background_matrix = volume.align(i, ras)
            for k in ('rh', 'lh'):
                for j in ('pial', 'white'):
                    current_surface = self.parser_surface.parse(surfaces_path + '/' + k + '.' + j + resampled_name + '.gii')
                    surf_x_array, surf_y_array = current_surface.get_x_y_array(i, ras)
                    self.writer.write_matrix_and_surfaces(background_matrix, surf_x_array, surf_y_array, clear_flag, j, self._new_name(i))
                    clear_flag = 'false'

