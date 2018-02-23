# -*- coding: utf-8 -*-

import os
import numpy
from tvb.recon.algo.service.surface import SurfaceService
from tvb.recon.io.annotation import AnnotationIO
from tvb.recon.io.factory import IOUtils
from tvb.recon.io.surface import FreesurferIO, H5SurfaceIO
from tvb.recon.model.surface import Surface
from tvb.recon.tests.base import (
    get_data_file, get_temporary_files_path, data_path)
from ..base import BaseTest


class SurfaceTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.service = SurfaceService()

    def test_tri_area(self):
        h5_path = get_data_file('head2', 'SurfaceCortical.h5')
        h5_io = H5SurfaceIO()
        surface = h5_io.read(h5_path)
        rfi = numpy.array([0])
        area = self.service.tri_area(surface.vertices[surface.triangles[rfi]])
        self.assertEqual(5000, area[0])

    def test_merge_surfaces(self,):
        h5_surface_path = get_data_file("head2", "SurfaceCortical.h5")
        h5_surface = IOUtils.read_surface(h5_surface_path, False)

        vtx = h5_surface.vertices
        tri = h5_surface.triangles
        nv = vtx.size
        nt = tri.size
        nv2 = int(nv / 2)
        nt2 = int(nt / 2)

        lh_surface = Surface(vtx[:nv2], tri[:nt2])
        rh_surface = Surface(vtx[nv2:], tri[nt2:])

        # h5_region_mapping_path = get_data_file("head2", "RegionMapping.h5")
        # annotation = IOUtils.read_annotation(h5_region_mapping_path)
        #
        # lh_region_mapping = annotation.region_mapping[:len(annotation.region_mapping) / 2]
        # rh_region_mapping = annotation.region_mapping[len(annotation.region_mapping) / 2:]

        out_surface = self.service.merge_surfaces([lh_surface, rh_surface])
        self.assertEqual(len(out_surface.vertices),
                         len(lh_surface.vertices) + len(rh_surface.vertices))
        self.assertEqual(len(out_surface.triangles),
                         len(lh_surface.triangles) + len(rh_surface.triangles))
        #assert len(out_region_mapping) == len(lh_region_mapping) + len(rh_region_mapping)

    def test_extract_subsurf(self,):
        surface_parser = FreesurferIO()
        annot_parser = AnnotationIO()
        surface_file = get_data_file("freesurfer_fsaverage", "surf", "lh.pial")
        annot_file = get_data_file(
            "freesurfer_fsaverage", "label", "lh.aparc.annot")
        surface = surface_parser.read(surface_file, False)
        verts = surface.vertices
        annot = annot_parser.read(annot_file)
        labels = annot.region_mapping
        verts_mask = labels == 7
        subsurf_verts, subsurf_faces = self.service.extract_subsurf(
            surface, verts_mask, output='verts_triangls')[:2]
        self.assertEqual(subsurf_verts.all(),
                         verts[numpy.where(verts_mask)].all())
        subsurf = self.service.extract_subsurf(
            surface, verts_mask, output='surface')
        self.assertEqual(subsurf.vertices.all(),
                         verts[numpy.where(verts_mask)].all())

    def test_aseg_surf_conc_annot(self,):
        out_surf_path = get_temporary_files_path("out_aseg")
        out_annot_path = get_temporary_files_path("out_annot")
        labels = "10 11"
        colorLUT = get_data_file("colorLUT.txt")
        self.service.aseg_surf_conc_annot(
            data_path, out_surf_path, out_annot_path, labels, colorLUT)
        self.assertTrue(os.path.exists(out_surf_path))
        self.assertTrue(os.path.exists(out_annot_path))

        surface_parser = FreesurferIO()
        surface = surface_parser.read(out_surf_path, False)
        self.assertEqual(len(surface.vertices), 5714)
        self.assertEqual(len(surface.triangles), 11420)

        annotation = IOUtils.read_annotation(out_annot_path)
        self.assertTrue(
            numpy.array_equal(
                annotation.regions_color_table,
                [[0, 118, 14, 255, 947712], [122, 186, 220, 255, 14465658]]))

    def test_vertex_connectivity(self,):
        surf_path = get_data_file("head2", 'SurfaceCortical.h5')
        surface_parser = H5SurfaceIO()
        surface = surface_parser.read(surf_path)
        conn = self.service.vertex_connectivity(surface)
        self.assertEqual(conn.shape, (16, 16))
        self.assertEqual(conn[0, 1], 1)
        self.assertEqual(conn[0, 10], 0)

    def test_vertex_connectivity_2(self,):
        surf_path = get_data_file("head2", 'SurfaceCortical.h5')
        surface_parser = H5SurfaceIO()
        surface = surface_parser.read(surf_path)
        conn = self.service.vertex_connectivity(surface, metric='euclidean')
        self.assertEqual(conn.shape, (16, 16))
        self.assertEqual(conn[0, 1], 100)
        self.assertEqual(conn[0, 10], 0)
