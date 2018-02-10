# -*- coding: utf-8 -*-
import tempfile
from zipfile import ZipFile

import nibabel
import numpy
import h5py
import os
from tvb.recon.logger import get_logger
from tvb.recon.model.surface import Surface
from tvb.recon.model.constants import CENTER_RAS_FS_SURF, CENTER_RAS_GIFTI_SURF
from nibabel.freesurfer.io import read_geometry, write_geometry
from nibabel.gifti import GiftiDataArray
from nibabel.gifti import GiftiImage
from nibabel.gifti import GiftiMetaData
from nibabel.gifti import giftiio


class ABCSurfaceIO(object):
    """
    This will define the behaviour needed for a surface io.
    """

    def read(self, data_file, use_center_surface):
        raise NotImplementedError()

    def write(self, surface_obj, file_path):
        raise NotImplementedError()

    def read_transformation_matrix_from_metadata(self, metadata):
        raise NotImplementedError()

    def write_transformation_matrix(self, metadata):
        raise NotImplementedError()


TRANSFORM_MATRIX_GIFTI_KEYS = [['VolGeomX_R', 'VolGeomY_R', 'VolGeomZ_R', CENTER_RAS_GIFTI_SURF[0]],
                               ['VolGeomX_A', 'VolGeomY_A', 'VolGeomZ_A',
                                CENTER_RAS_GIFTI_SURF[1]],
                               ['VolGeomX_S', 'VolGeomY_S', 'VolGeomZ_S', CENTER_RAS_GIFTI_SURF[2]]]


class GiftiSurfaceIO(ABCSurfaceIO):
    """
    This class reads content of GIFTI surface files
    """
    logger = get_logger(__name__)

    def read(self, data_file, use_center_surface):
        gifti_image = giftiio.read(data_file)
        image_metadata = gifti_image.meta.metadata
        self.logger.info(
            "From the file %s the extracted metadata is %s", data_file, image_metadata)

        data_arrays = gifti_image.darrays
        vertices = data_arrays[0].data
        triangles = data_arrays[1].data

        vol_geom_center_ras = [0, 0, 0]
        vertices_metadata = data_arrays[0].metadata
        self.logger.info(
            "The metadata from vertices data array is %s", vertices_metadata)
        vertices_coord_system = data_arrays[0].coordsys
        self.logger.info(
            "The coordinate system transform matrix from vertices data array is %s", vertices_coord_system)
        triangles_metadata = data_arrays[1].metadata
        self.logger.info(
            "The metadata from triangles data array is %s", triangles_metadata)

        if use_center_surface:
            vol_geom_center_ras = [0, 0, 0]
        else:
            vol_geom_center_ras[0] = float(
                vertices_metadata[CENTER_RAS_GIFTI_SURF[0]])
            vol_geom_center_ras[1] = float(
                vertices_metadata[CENTER_RAS_GIFTI_SURF[1]])
            vol_geom_center_ras[2] = float(
                vertices_metadata[CENTER_RAS_GIFTI_SURF[2]])

        return Surface(vertices, triangles, area_mask=None,
                       center_ras=vol_geom_center_ras, vertices_coord_system=vertices_coord_system,
                       generic_metadata=image_metadata, vertices_metadata=vertices_metadata,
                       triangles_metadata=triangles_metadata)

    def write(self, surface_obj, file_path):
        image_metadata = GiftiMetaData().from_dict(surface_obj.generic_metadata)
        vertices_metadata = GiftiMetaData().from_dict(surface_obj.vertices_metadata)
        triangles_metadata = GiftiMetaData().from_dict(surface_obj.triangles_metadata)

        gifti_image = GiftiImage()
        gifti_image.set_metadata(image_metadata)

        data = GiftiDataArray(
            surface_obj.vertices, datatype='NIFTI_TYPE_FLOAT32', intent='NIFTI_INTENT_POINTSET')
        data.meta = vertices_metadata
        data.coordsys = surface_obj.vertices_coord_system
        gifti_image.add_gifti_data_array(data)

        data = GiftiDataArray(
            surface_obj.triangles, datatype='NIFTI_TYPE_INT32', intent='NIFTI_INTENT_TRIANGLE')
        data.meta = triangles_metadata
        data.coordsys = None
        gifti_image.add_gifti_data_array(data)

        nibabel.save(gifti_image, file_path)

    def read_transformation_matrix_from_metadata(self, image_metadata):
        matrix_from_metadata = [[0, 0, 0, 0] for _ in range(4)]

        for i in range(3):
            for j in range(4):
                matrix_from_metadata[i][j] = float(
                    image_metadata[TRANSFORM_MATRIX_GIFTI_KEYS[i][j]])

        matrix_from_metadata[3] = [0.0, 0.0, 0.0, 1.0]
        return matrix_from_metadata

    def write_transformation_matrix(self, image_metadata):
        # we can temporary write the identity matrix to gifti meta to avoid
        # freeview rotations.

        identity_matrix = [[1.0, 0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0, 0.0],
                           [0.0, 0.0, 1.0, 0.0]]

        for i in range(3):
            for j in range(4):
                image_metadata[TRANSFORM_MATRIX_GIFTI_KEYS[
                    i][j]] = str(identity_matrix[i][j])


TRANSFORM_MATRIX_FS_KEYS = ['xras', 'yras', 'zras', CENTER_RAS_FS_SURF]


class FreesurferIO(ABCSurfaceIO):
    """
    This class reads content of Freesurfer surface files
    """
    logger = get_logger(__name__)

    def read(self, surface_path, use_center_surface):
        vertices, triangles, metadata = read_geometry(
            surface_path, read_metadata=True)
        self.logger.info(
            "From the file %s the extracted metadata is %s", surface_path, metadata)

        if use_center_surface:
            cras = [0, 0, 0]
            self.logger.info(
                "The --center_ras flag was specified, so the ras centering point is %s", cras)
        else:
            if CENTER_RAS_FS_SURF in metadata:
                cras = metadata[CENTER_RAS_FS_SURF]
                self.logger.info(
                    "The ras centering point for surface %s is %s", surface_path, cras)
            else:
                cras = [0, 0, 0]
                self.logger.warning("Could not read the ras centering point from surface %s header. "
                                    "The cras will be %s", surface_path, cras)

        return Surface(vertices, triangles, area_mask=None,
                       center_ras=cras, generic_metadata=metadata)

    def write(self, surface, surface_path):
        write_geometry(filepath=surface_path, coords=surface.vertices, faces=surface.triangles,
                       volume_info=surface.get_main_metadata())

    def read_transformation_matrix_from_metadata(self, image_metadata):
        matrix_from_metadata = [[0, 0, 0, 0]
                                for _ in range(4)]  # or numpy.zeros((4,4))

        for i, fs_key in enumerate(TRANSFORM_MATRIX_FS_KEYS):
            for j in range(3):
                matrix_from_metadata[i][j] = image_metadata[fs_key][j]
        matrix_from_metadata[3][3] = 1
        matrix_from_metadata = numpy.transpose(matrix_from_metadata)
        return matrix_from_metadata

    def write_transformation_matrix(self, image_metadata):
        """
        We write the identity matrix to FS meta to avoid freeview rotations.
        :param image_metadata: meta to be corrected
        :return: image_metadata after change
        """
        identity_matrix = [[1.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0],
                           [0.0, 0.0, 0.0]]
        for i, fs_key in enumerate(TRANSFORM_MATRIX_FS_KEYS):
            image_metadata[fs_key] = identity_matrix[i]


class BrainVisaIO(ABCSurfaceIO):
    def write(self, surface, file_path):
        vn = surface.vertex_normals()
        with open(file_path, 'w') as fd:
            fd.write('- %d\n' % len(vn))
            for (vx, vy, vz), (nx, ny, nz) in zip(surface.vertices, vn):
                fd.write('%f %f %f %f %f %f\n' % (vx, vy, vz, nx, ny, nz))
            fd.write('- %d %d %d\n' % ((len(surface.triangles),) * 3))
            for i, j, k in surface.triangles:
                fd.write('%d %d %d\n' % (i, j, k))


class H5SurfaceIO(ABCSurfaceIO):
    """
    This class reads content of H5 surface files
    """
    logger = get_logger(__name__)

    def read(self, h5_path, use_center_surface=False):
        h5_file = h5py.File(h5_path, 'r', libver='latest')
        vertices = h5_file['/vertices'][()]
        triangles = h5_file['/triangles'][()]
        h5_file.close()
        return Surface(vertices, triangles)


class ZipSurfaceIO(ABCSurfaceIO):
    """
    This writes contents of surface to txt files and zips them
    """
    logger = get_logger(__name__)

    def write(self, surface, filename):
        tmpdir = tempfile.TemporaryDirectory()

        file_vertices = os.path.join(tmpdir.name, 'vertices.txt')
        file_triangles = os.path.join(tmpdir.name, 'triangles.txt')
        file_normals = os.path.join(tmpdir.name, 'normals.txt')

        file_vox2ras = os.path.join(os.path.dirname(filename), 'vox2ras.txt')

        numpy.savetxt(file_vertices, surface.vertices, fmt='%.6f %.6f %.6f')
        numpy.savetxt(file_triangles, surface.triangles, fmt='%d %d %d')
        numpy.savetxt(file_normals, surface.vertex_normals(), fmt='%.6f %.6f %.6f')

        with ZipFile(filename, 'w') as zip_file:
            zip_file.write(file_vertices, os.path.basename(file_vertices))
            zip_file.write(file_triangles, os.path.basename(file_triangles))
            zip_file.write(file_normals, os.path.basename(file_normals))
            if os.path.exists(file_vox2ras):
                zip_file.write(file_vox2ras, os.path.basename(file_vox2ras))
            else:
                self.logger.warn("The %s file does not exist" % file_vox2ras)
