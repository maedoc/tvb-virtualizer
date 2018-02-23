# -*- coding: utf-8 -*-

import os
from tvb.recon.io.annotation import H5AnnotationIO, AnnotationIO
from tvb.recon.io.surface import GiftiSurfaceIO, FreesurferIO, H5SurfaceIO, ZipSurfaceIO
from tvb.recon.io.volume import VolumeIO, H5VolumeIO
from tvb.recon.model.constants import GIFTI_EXTENSION, H5_EXTENSION


class IOUtils(object):

    @staticmethod
    def __get_extension(file_path):
        _, extension = os.path.splitext(file_path)
        return extension

    @staticmethod
    def surface_io_factory(surface_path):
        extension = IOUtils.__get_extension(surface_path)

        if extension == GIFTI_EXTENSION:
            return GiftiSurfaceIO()
        else:
            if extension == H5_EXTENSION:
                return H5SurfaceIO()
            elif extension == ".zip":
                return ZipSurfaceIO()
            else:
                return FreesurferIO()

    @staticmethod
    def read_surface(surface_path, use_center_surface):
        surface_io = IOUtils.surface_io_factory(surface_path)
        return surface_io.read(surface_path, use_center_surface)

    @staticmethod
    def write_surface(out_surface_path, surface):
        surface_io = IOUtils.surface_io_factory(out_surface_path)
        surface_io.write(surface, out_surface_path)

    @staticmethod
    def volume_io_factory(volume_path):
        extension = IOUtils.__get_extension(volume_path)

        if extension == H5_EXTENSION:
            return H5VolumeIO()
        else:
            return VolumeIO()

    @staticmethod
    def read_volume(volume_path):
        volume_io = IOUtils.volume_io_factory(volume_path)
        return volume_io.read(volume_path)

    @staticmethod
    def write_volume(out_volume_path, volume):
        volume_io = IOUtils.volume_io_factory(out_volume_path)
        volume_io.write(out_volume_path, volume)

    @staticmethod
    def annotation_io_factory(annotation_path):
        extension = IOUtils.__get_extension(annotation_path)

        if extension == H5_EXTENSION:
            return H5AnnotationIO()
        else:
            return AnnotationIO()

    @staticmethod
    def read_annotation(annotation_path):
        annotation_io = IOUtils.annotation_io_factory(annotation_path)
        return annotation_io.read(annotation_path)

    @staticmethod
    def write_annotation(out_annotation_path, annotation):
        annotation_io = IOUtils.annotation_io_factory(out_annotation_path)
        annotation_io.write(out_annotation_path, annotation)
