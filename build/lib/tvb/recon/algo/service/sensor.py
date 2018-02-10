# -*- coding: utf-8 -*-

import glob
import numpy
import os
import matplotlib

# ensure default behavior is headless. If you want, e.g. Qt5Agg, use the
# MPLBACKEND environment variable.
# cf. http://matplotlib.org/faq/environment_variables_faq.html
matplotlib.use(os.environ.get('MPLBACKEND', 'Agg'))

import pylab
from tvb.recon.model.surface import Surface


class SensorService(object):

    def gen_head_model(self, subjects_dir, subject):
        surfs_glob = '%s/%s/bem/watershed/*_surface-low.tri' % (
            subjects_dir, subject)
        surfs = glob.glob(surfs_glob)

        if len(surfs) == 0:
            raise Exception('tri surfaces not found!')

        hm_base = '%s/%s/bem/head_model' % (subjects_dir, subject)
        hm_temp = """# Domain Description 1.1

    Interfaces 3

    Interface Skull: "{0}_outer_skull_surface-low.tri"
    Interface Cortex: "{0}_inner_skull_surface-low.tri"
    Interface Head: "{0}_outer_skin_surface-low.tri"

    Domains 4

    Domain Scalp: Skull -Head
    Domain Brain: -Cortex
    Domain Air: Head
    Domain Skull: Cortex -Skull
    """.format('%s/%s/bem/watershed/%s' % (subjects_dir, subject, subject))

        hm_geom = hm_base + '.geom'
        with open(hm_geom, 'w') as fd:
            fd.write(hm_temp)
        print(('%s written.' % (hm_geom,)))

        hm_cond = hm_base + '.cond'
        with open(hm_cond, 'w') as fd:
            fd.write("""# Properties Description 1.0 (Conductivities)

    Air         0.0
    Scalp       1
    Brain       1
    Skull       0.03
    """)
        print(('%s written.' % (hm_cond,)))

    def gen_dipole_triplets(self, pos):
        pos3 = numpy.repeat(pos, 3, axis=0)
        ori3 = numpy.tile(numpy.eye(3), (len(pos), 1))
        return pos3, ori3

    def gen_dipoles(self, pos, ori_or_face=None, out_fname=None):
        "Generate dipoles (or equiv. file) for OpenMEEG."
        if ori_or_face is None:
            pos, ori = self.gen_dipole_triplets(pos)
        else:
            if ori_or_face.dtype in numpy.floattypes:
                ori = ori_or_face
            else:
                surface = Surface(pos, ori_or_face, [], None)
                ori = surface.vertex_normals()
        numpy.savetxt(out_fname, numpy.c_[pos, ori], fmt='%f')

    def periodic_xyz_for_object(self, lab, val, aff, bw=0.1, doplot=False):
        "Find blob centers for object in lab volume having value val."
        # TODO handle oblique with multiple spacing
        # vox coords onto first mode
        vox_idx = numpy.argwhere(lab == val)
        xyz = aff.dot(numpy.c_[vox_idx, numpy.ones(vox_idx.shape[0])].T)[:3].T
        xyz_mean = xyz.mean(axis=0)
        xyz -= xyz_mean
        u, s, vt = numpy.linalg.svd(xyz, 0)
        xi = u[:, 0] * s[0]
        # histogram and ft to find spacing and offset
        bn, bxi_ = numpy.histogram(
            xi, numpy.r_[min(xi) - 0.5: max(xi) + 0.5: bw])
        bxi = bxi_[:-1] + bw / 2.0
        w = numpy.r_[2.0: 6.0: 1000j]
        f = (1.0 / w)[:, None]
        Bf = (numpy.exp(-2 * numpy.pi * 1j * bxi * f) * bn * bw).sum(axis=-1)
        i_peak = numpy.argmax(numpy.abs(Bf))
        theta = numpy.angle(Bf[i_peak])
        print(("[periodic_xyz_for_object]", val, 1 / f[i_peak][0], theta))
        xi_o = -theta / (2 * numpy.pi * f[i_peak])
        xi_pos = numpy.r_[xi_o: xi.max(): w[i_peak]]
        xi_neg = numpy.r_[-xi_o: -xi.min(): w[i_peak]]
        xi_pos = numpy.sort(numpy.r_[-xi_neg, xi_pos[1:]])
        xyz_pos = numpy.c_[xi_pos, numpy.zeros(
            (len(xi_pos), 2))].dot(vt) + xyz_mean
        if doplot:
            pylab.figure()
            pylab.subplot(2, 1, 1)
            pylab.plot(bxi, bn)
            pylab.subplot(2, 1, 2)
            pylab.plot(w, numpy.abs(Bf))
            pylab.subplot(2, 1, 1)
            cos_arg = 2 * numpy.pi * f[i_peak] * bxi + theta
            pylab.plot(bxi, numpy.cos(cos_arg) * bn.std() +
                       bn.mean(), 'k--', alpha=0.5)
            [pylab.axvline(xp, color='r') for xp in xi_pos]
            pylab.show()
        return xyz_pos
