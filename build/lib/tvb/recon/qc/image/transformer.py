# -*- coding: utf-8 -*-

import os
import subprocess
from os.path import basename
from tvb.recon.logger import get_logger
from tvb.recon.model.constants import GIFTI_EXTENSION


class ImageTransformer(object):
    use_ras_transform = False
    use_center_surface = False
    use_cc_point = False
    converted_files_directory = "converted_files"
    created_files = []
    logger = get_logger(__name__)

    def __init__(self, path):
        self.converted_files_directory_path = os.path.join(
            path, self.converted_files_directory)
        if not os.path.exists(self.converted_files_directory_path):
            os.makedirs(self.converted_files_directory_path)

    def apply_transform(self, volume_path):
        if not self.use_ras_transform:
            return volume_path

        output_volume_path = os.path.join(
            self.converted_files_directory_path, 'ras' + basename(volume_path))

        try:
            x = subprocess.call(
                ['mri_convert', '--out_orientation', 'RAS', '--out_type', 'nii', '--input_volume', volume_path,
                 '--output_volume', output_volume_path])
            print(x)
            self.created_files.append(output_volume_path)
            return output_volume_path
        except subprocess.CalledProcessError:
            self.logger.error("Error converting volume")

    def center_surface(self, surface):
        if not self.use_center_surface:
            return surface

        surface_new_path = os.path.join(
            self.converted_files_directory_path, 'centered' + basename(surface))

        try:
            x = subprocess.call(
                ['mris_convert', '--to-scanner', surface, surface_new_path])
            print(x)
            self.created_files.append(surface_new_path)
            return surface_new_path
        except subprocess.CalledProcessError:
            self.logger.error("Error converting surface")

    def transform_single_volume(self, volume_path):
        return self.apply_transform(volume_path)

    def transform_2_volumes(self, background_path, overlay_path):
        return self.apply_transform(
            background_path), self.apply_transform(overlay_path)

    def transform_3_volumes(self, background_path,
                            overlay_1_path, overlay_2_path):
        return self.apply_transform(background_path), self.apply_transform(overlay_1_path), self.apply_transform(
            overlay_2_path)

    def transform_volume_surfaces(self, background_path, surfaces_list):
        new_surfaces_list = [self.center_surface(
            os.path.expandvars(surf)) for surf in surfaces_list]
        return self.apply_transform(background_path), new_surfaces_list

    def transform_volume_white_pial(
            self, background_path, resampled_surface, surfaces_path, use_gifti):
        if resampled_surface is not "":
            resampled_surface = "-" + resampled_surface

        gii = ""
        if use_gifti:
            gii = GIFTI_EXTENSION

        white_pial_surfaces_path = [hemi + "." + surface_type + resampled_surface + gii for hemi in ("rh", "lh") for
                                    surface_type in ("pial", "white")]

        new_surfaces_list = [self.center_surface(os.path.expandvars(os.path.join(surfaces_path, surface))) for surface
                             in white_pial_surfaces_path]
        return self.apply_transform(background_path), new_surfaces_list
