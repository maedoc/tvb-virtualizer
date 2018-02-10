# -*- coding: utf-8 -*-

import zipfile
from tvb.recon.io.generic import GenericIO, StringIO


class TVBWriter(object):
    # Write a surface to a TVB-format ZIP file.

    def write_surface_zip(self, zip_fname, surface):
        generic_io = GenericIO()
        sv = generic_io.np_save_strio(surface.vertices, '%f')
        sf = generic_io.np_save_strio(surface.triangles, '%d')
        szf = StringIO()
        zf = zipfile.ZipFile(szf, 'w')
        zf.writestr('vertices.txt', sv.getvalue())
        zf.writestr('triangles.txt', sf.getvalue())
        zf.close()
        with open(zip_fname, 'wb') as fd:
            fd.write(szf.getvalue())
