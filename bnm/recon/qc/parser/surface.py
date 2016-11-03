# -*- coding: utf-8 -*-

from nibabel.gifti import giftiio
from bnm.recon.snapshot.model.surface import Surface


class SurfaceParser(object):
    """
    This class reads content of a NIFTI file and returns a Volume Object
    """

    def parse(self, data_file):
        gifti_image = giftiio.read(data_file)
        data_arrays = gifti_image.darrays
        vertices = data_arrays[0].data
        triangles = data_arrays[1].data

        vol_geom_center_ras = [0, 0, 0]
        vol_geom_center_ras[0] = float(data_arrays[0].metadata['VolGeomC_R'])
        vol_geom_center_ras[1] = float(data_arrays[0].metadata['VolGeomC_A'])
        vol_geom_center_ras[2] = float(data_arrays[0].metadata['VolGeomC_S'])

        return Surface(vertices, triangles, vol_geom_center_ras)
