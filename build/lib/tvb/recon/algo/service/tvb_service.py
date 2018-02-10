# -*- coding: utf-8 -*-

import os
import numpy
from tvb.recon.algo.service.surface import SurfaceService
from tvb.recon.io.factory import IOUtils
from tvb.recon.io.tvb_writer import TVBWriter


class TVBService(object):
    surface_service = SurfaceService()

    def convert_fs_subj_to_tvb_surf(self, subject=None):
        """
        Merge surfaces and roi maps. Write out in TVB format.
        """

        subjects_dir = os.environ['SUBJECTS_DIR']

        if subject is None:
            subject = os.environ['SUBJECT']

        lh_surf_path = os.path.join(subjects_dir, subject, 'surf', 'lh.pial')
        rh_surf_path = os.path.join(subjects_dir, subject, 'surf', 'rh.pial')
        lh_annot_path = os.path.join(
            subjects_dir, subject, 'label', 'lh.aparc.annot')
        rh_annot_path = os.path.join(
            subjects_dir, subject, 'label', 'rh.aparc.annot')

        lh_surface = IOUtils.read_surface(lh_surf_path, False)
        rh_surface = IOUtils.read_surface(rh_surf_path, False)

        lh_annot = IOUtils.read_annotation(lh_annot_path)
        rh_annot = IOUtils.read_annotation(rh_annot_path)

        surface, region_mapping = self.surface_service.merge_lh_rh(lh_surface, rh_surface, lh_annot.region_mapping,
                                                                   rh_annot.region_mapping)

        numpy.savetxt('%s_ctx_roi_map.txt' %
                      (subject,), region_mapping.flat[:], '%i')
        TVBWriter().write_surface_zip('%s_pial_surf.zip' % (subject,), surface)
