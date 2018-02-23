# -*- encoding: utf-8 -*-

import os
import numpy as np
from tvb.recon.io.factory import IOUtils
from tvb.recon.io.generic import GenericIO
from tvb.recon.logger import get_logger
from tvb.recon.model.constants import PROJECTIONS, SNAPSHOT_NAME, T1_RAS_VOLUME, MRI_DIRECTORY, \
    FS_TO_CONN_INDICES_MAPPING_PATH
from tvb.recon.qc.image.writer import ImageWriter


class ImageProcessor(object):

    def __init__(self, snapshots_directory, snapshot_count=0):
        self.generic_io = GenericIO()
        self.writer = ImageWriter(snapshots_directory)
        self.snapshot_count = snapshot_count
        self.logger = get_logger(__name__)

    def generate_file_name(self, current_projection,
                           snapshot_name=SNAPSHOT_NAME):
        file_name = snapshot_name + "_" + \
            current_projection + "_" + str(self.snapshot_count)
        return file_name

    def read_t1_affine_matrix(self):
        t1_volume = IOUtils.read_volume(os.path.join(
            os.environ[MRI_DIRECTORY], os.environ[T1_RAS_VOLUME]))
        return t1_volume.affine_matrix

    def show_single_volume(self, volume_path, use_cc_point,
                           snapshot_name=SNAPSHOT_NAME):

        volume = IOUtils.read_volume(volume_path)

        if use_cc_point:
            ras = self.generic_io.get_ras_coordinates(
                self.read_t1_affine_matrix())
        else:
            ras = volume.get_center_point()

        for projection in PROJECTIONS:
            try:
                x_axis_coords, y_axis_coords, volume_matrix = volume.slice_volume(
                    projection, ras)
            except IndexError:
                new_ras = volume.get_center_point()
                x_axis_coords, y_axis_coords, volume_matrix = volume.slice_volume(
                    projection, new_ras)
                self.logger.info("The volume center point has been used for %s snapshot of %s.", projection,
                                 volume_path)

            self.writer.write_matrix(x_axis_coords, y_axis_coords, volume_matrix,
                                     self.generate_file_name(projection, snapshot_name))

    def overlap_2_volumes(self, background_path, overlay_path,
                          use_cc_point, snapshot_name=SNAPSHOT_NAME):

        background_volume = IOUtils.read_volume(background_path)
        overlay_volume = IOUtils.read_volume(overlay_path)

        if use_cc_point:
            ras = self.generic_io.get_ras_coordinates(
                self.read_t1_affine_matrix())
        else:
            ras = background_volume.get_center_point()

        for projection in PROJECTIONS:
            try:
                x, y, background_matrix = background_volume.slice_volume(
                    projection, ras)
                x1, y1, overlay_matrix = overlay_volume.slice_volume(
                    projection, ras)
            except IndexError:
                new_ras = background_volume.get_center_point()
                x, y, background_matrix = background_volume.slice_volume(
                    projection, new_ras)
                x1, y1, overlay_matrix = overlay_volume.slice_volume(
                    projection, new_ras)
                self.logger.info("The volume center point has been used for %s snapshot of %s and %s.", projection,
                                 background_path, overlay_path)

            self.writer.write_2_matrices(x, y, background_matrix, x1, y1, overlay_matrix,
                                         self.generate_file_name(projection, snapshot_name))

    def overlap_3_volumes(self, background_path, overlay_1_path, overlay_2_path, use_cc_point,
                          snapshot_name=SNAPSHOT_NAME):

        volume_background = IOUtils.read_volume(background_path)
        volume_overlay_1 = IOUtils.read_volume(overlay_1_path)
        volume_overlay_2 = IOUtils.read_volume(overlay_2_path)

        if use_cc_point:
            ras = self.generic_io.get_ras_coordinates(
                self.read_t1_affine_matrix())
        else:
            ras = volume_background.get_center_point()

        for projection in PROJECTIONS:
            try:
                x, y, background_matrix = volume_background.slice_volume(
                    projection, ras)
                x1, y1, overlay_1_matrix = volume_overlay_1.slice_volume(
                    projection, ras)
                x2, y2, overlay_2_matrix = volume_overlay_2.slice_volume(
                    projection, ras)
            except IndexError:
                new_ras = volume_background.get_center_point()
                x, y, background_matrix = volume_background.slice_volume(
                    projection, new_ras)
                x1, y1, overlay_1_matrix = volume_overlay_1.slice_volume(
                    projection, new_ras)
                x2, y2, overlay_2_matrix = volume_overlay_2.slice_volume(
                    projection, new_ras)
                self.logger.info("The volume center point has been used for %s snapshot of %s, %s and %s.", projection,
                                 background_path, overlay_1_path, overlay_2_path)

            self.writer.write_3_matrices(x, y, background_matrix, x1, y1, overlay_1_matrix, x2, y2, overlay_2_matrix,
                                         self.generate_file_name(projection, snapshot_name))

    def overlap_surface_annotation(
            self, surface_path, annotation, snapshot_name=SNAPSHOT_NAME):
        annotation = IOUtils.read_annotation(annotation)
        surface = IOUtils.read_surface(surface_path, False)
        self.writer.write_surface_with_annotation(surface, annotation,
                                                  self.generate_file_name('surface_annotation', snapshot_name))

    def overlap_volume_surfaces(self, volume_background, surfaces_path, use_center_surface, use_cc_point,
                                snapshot_name=SNAPSHOT_NAME):
        volume = IOUtils.read_volume(volume_background)

        if use_cc_point:
            ras = self.generic_io.get_ras_coordinates(
                self.read_t1_affine_matrix())
        else:
            ras = volume.get_center_point()

        surfaces = [IOUtils.read_surface(os.path.expandvars(surface), use_center_surface) for surface in
                    surfaces_path]

        for projection in PROJECTIONS:
            try:
                x, y, background_matrix = volume.slice_volume(projection, ras)
            except IndexError:
                ras = volume.get_center_point()
                x, y, background_matrix = volume.slice_volume(projection, ras)
                self.logger.info("The volume center point has been used for %s snapshot of %s and %s.", projection,
                                 volume_background, surfaces_path)

            clear_flag = True
            for surface_index, surface in enumerate(surfaces):
                surf_x_array, surf_y_array = surface.cut_by_plane(
                    projection, ras)
                self.writer.write_matrix_and_surfaces(x, y, background_matrix, surf_x_array, surf_y_array,
                                                      surface_index, clear_flag)
                clear_flag = False
            self.writer.save_figure(
                self.generate_file_name(projection, snapshot_name))

    def show_aparc_aseg_with_new_values(
            self, aparc_aseg_volume_path, region_values_path,
            background_volume_path, use_cc_point,
            fs_to_conn_indices_mapping_path=FS_TO_CONN_INDICES_MAPPING_PATH,
            snapshot_name=SNAPSHOT_NAME):
        """

        Parameters
        ----------
        aparc_aseg_volume_path
        region_values_path
        background_volume_path
        use_cc_point
        fs_to_conn_indices_mapping_path
        snapshot_name

        Returns
        -------

        """

        aparc_aseg_volume = IOUtils.read_volume(aparc_aseg_volume_path)

        fs_to_conn_indices_mapping = {}
        with open(fs_to_conn_indices_mapping_path, 'r') as fd:
            for line in fd.readlines():
                key, _, val = line.strip().split()
                fs_to_conn_indices_mapping[int(key)] = int(val)

        len_fs_conn = len(fs_to_conn_indices_mapping)

        conn_measure = np.loadtxt(region_values_path)
        npad = len_fs_conn - conn_measure.size
        conn_measure = np.pad( conn_measure, (0, npad), 'constant')

        if use_cc_point:
            ras = self.generic_io.get_ras_coordinates(
                self.read_t1_affine_matrix())
        else:
            ras = aparc_aseg_volume.get_center_point()

        background_volume = None
        if background_volume_path:
            background_volume = IOUtils.read_volume(background_volume_path)

        for projection in PROJECTIONS:
            self._aparc_aseg_projection(
                aparc_aseg_volume, aparc_aseg_volume_path, projection, ras,
                fs_to_conn_indices_mapping,
                background_volume, background_volume_path,
                snapshot_name, conn_measure
            )

    def _aparc_aseg_projection(
            self, aparc_aseg_volume, aparc_aseg_volume_path, projection, ras,
            fs_to_conn_indices_mapping,
            background_volume, background_volume_path, snapshot_name,
            conn_measure):

        try:
            slice = aparc_aseg_volume.slice_volume(projection, ras)
        except IndexError:
            new_ras = aparc_aseg_volume.get_center_point()
            slice = aparc_aseg_volume.slice_volume( projection, new_ras)
            msg = "The volume center point has been used for %s snapshot of %s."
            self.logger.info(msg, projection, aparc_aseg_volume_path)

        x_axis_coords, y_axis_coords, aparc_aseg_matrix  = slice

        for i, row in enumerate(aparc_aseg_matrix):
            for j, el in enumerate(row):
                if el > 0:
                    if el in fs_to_conn_indices_mapping:
                        idx = fs_to_conn_indices_mapping.get(el)
                        new_val = conn_measure[int(idx)]
                        aparc_aseg_matrix[i, j] = new_val
                    else:
                        aparc_aseg_matrix[i, j] = -1

        if background_volume_path == '':
            self.writer.write_matrix(x_axis_coords, y_axis_coords, aparc_aseg_matrix,
                                     self.generate_file_name(projection, snapshot_name), 'hot')
        else:
            try:
                bx_axis_coords, by_axis_coords, bvolume_matrix = background_volume.slice_volume(
                    projection, ras)
            except IndexError:
                new_ras = aparc_aseg_volume.get_center_point()
                bx_axis_coords, by_axis_coords, bvolume_matrix = background_volume.slice_volume(
                    projection, new_ras)
                self.logger.info("The volume center point has been used for %s snapshot of %s and %s.", projection,
                                 aparc_aseg_volume_path, background_volume_path)

            self.writer.write_2_matrices(bx_axis_coords, by_axis_coords, bvolume_matrix, x_axis_coords,
                                         y_axis_coords,
                                         aparc_aseg_matrix,
                                         self.generate_file_name(projection, snapshot_name))
