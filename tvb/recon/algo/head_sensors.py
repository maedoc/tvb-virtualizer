# -*- coding: utf-8 -*-

"""
Generates suitable resolution head surf and EEG/MEG sensors descriptions.

"""

# imports
from __future__ import absolute_import
from __future__ import print_function
import os
import os.path
import numpy
import scipy.cluster.vq
from tvb.recon.model.surface import Surface
from pyqtgraph import mkQApp
import pyqtgraph.opengl
from nibabel.freesurfer import read_geometry
from six.moves import range


def mask_mesh(v, f, mask):
    "Apply vertex-wise mask to mesh."
    nv = v.shape[0]
    idx = numpy.r_[:nv][mask]
    faces = []
    for i, j, k in f:
        if (i in idx) and (j in idx) and (k in idx):
            faces.append([i, j, k])
    faces = numpy.array(faces)
    verts = v[mask]
    face_map = numpy.r_[:f.max() + 1]
    face_map[idx] = numpy.r_[:verts.shape[0]]
    faces = face_map[faces]
    return verts, faces


def write_off(fname, v, f, overwrite=False):
    """Check if file name exists with overwrite off
       if it dos'nt create one and write a echo (print)"""
    if not os.path.exists(fname) or overwrite:
        nv = v.shape[0]
        nf = f.shape[0]
        with open(fname, 'w') as fd:
            fd.write('OFF\n%d %d 0\n' % (nv, nf))
            for x, y, z in v:
                fd.write('%f %f %f\n' % (x, y, z))
            for i, j, k in f:
                fd.write('3 %d %d %d\n' % (i, j, k))
        print(('%s written' % (fname, )))
    else:
        print(('%s exists, use overwrite=True to overwrite.' % (fname, )))


def remesh_off(remesher_path, ref_fname, out_fname, overwrite=False):
    "Run remesher on mesh in OFF format."
    if not os.path.exists(out_fname) or overwrite:
        os.system('%s %s %s' % (remesh_path, ref_fname, out_fname))
    else:
        print(('%s exists, use overwrite=True to overwrite.' % (out_fname, )))


def read_off(fname):
    "Read mesh in from OFF format file."
    vl, fl = [], []
    with open(fname, 'r') as fd:
        fd.readline()
        nv, nf, _ = [int(i) for i in fd.readline().strip().split()]
        for _ in range(nv):
            vl.append([float(f) for f in fd.readline().strip().split()])
        for _ in range(nf):
            fl.append([int(i) for i in fd.readline().strip().split()[1:]])
    vl = numpy.array(vl)
    fl = numpy.array(fl)
    return vl, fl


def make_cap_mask(vl, a=0.8, s=1.3, thresh=-0.3):
    "Make vertex-wise mask for cap assuming RAS coordinates."
    nvl = (vl - vl.min(axis=0)) / vl.ptp(axis=0)
    capmask = (nvl[:, 1] * a - nvl[:, 2] * s) < thresh
    return capmask


def xyz2rgb(vl):
    "Map XYZ coordinates to RGB space."
    nv = vl.shape[0]
    nvl = (vl - vl.min(axis=0)) / vl.ptp(axis=0)
    vcrgb = numpy.c_[nvl, numpy.ones((nv, 1))]
    return vcrgb


def sens_xyz_ori(v, f, l):
    "Sens XYZ origin to vertex normal by using numpy"
    surface = Surface(v, f, [], None)
    vn = surface.vertex_normals()
    pos = numpy.zeros((n_sens, 6))
    numpy.add.at(pos, l, numpy.c_[v, vn])
    return pos / numpy.bincount(l)[:, numpy.newaxis]


# config
seghead = 'lh.seghead'
ctx = 'lh.pial.fsaverage5'
ref_fname = 'head-ref.off'
low_fname = 'head-low.off'
plot = True
n_sens = 128
eeg_scl = 1.1
meg_scl = 1.3
eeg_fname = 'eeg.xyz'
meg_fname = 'meg.squid'

# read FS high-res head surf
vh, fh = read_geometry('lh.seghead')

# make new head surf with remesher
write_off(ref_fname, vh, fh)
remesh_path = '../scripts/remesher-mac/cmdremesher/cmdremesher'
remesh_off(remesh_path, ref_fname, low_fname)

# read new head surf
vl, fl = read_off(low_fname)

# mask for cap
vc, fc = mask_mesh(vl, fl, make_cap_mask(vl))

# cluster vertices on cap 128 ways
_, vcl = scipy.cluster.vq.kmeans2(vc, n_sens, minit='points', missing='raise')
assert numpy.unique(vcl).size == n_sens

# TODO label sensor by nearest aparc name

# on EEG cap and MEG helmet, avg pos and vtx norm to get sensor positions
# and normals
eegpo = sens_xyz_ori(vc * eeg_scl, fc, vcl)
megpo = sens_xyz_ori(vc * meg_scl, fc, vcl)

# write sensor files for OpenMEEG
numpy.savetxt(eeg_fname, eegpo[:3])
numpy.savetxt(meg_fname, megpo)

# visualize results
if plot:
    app = mkQApp()
    gvw = pyqtgraph.opengl.GLViewWidget()
    hs = pyqtgraph.opengl.GLMeshItem(meshdata=pyqtgraph.opengl.MeshData(
        vl, fl, vertexColors=xyz2rgb(vl)), drawEdges=True)
    cap = pyqtgraph.opengl.GLMeshItem(meshdata=pyqtgraph.opengl.MeshData(
        vc * eeg_scl, fc), color=(0, 0, 1.0, 1.0), drawEdges=True)
    hc = numpy.c_[numpy.random.rand(n_sens, 3), numpy.ones((n_sens, 1))][vcl]
    helmet = pyqtgraph.opengl.GLMeshItem(meshdata=pyqtgraph.opengl.MeshData(vc * meg_scl, fc, vertexColors=hc),  # color=(1, 0, 0.0, 1.0),
                                         drawEdges=True)
    lh = pyqtgraph.opengl.GLMeshItem(meshdata=pyqtgraph.opengl.MeshData(
        *read_geometry(ctx)), drawEdges=True, drawFaces=False)
    for item in [hs, cap, helmet, lh]:
        gvw.addItem(item)
    for po in (megpo, eegpo):
        gvw.addItem(pyqtgraph.opengl.GLScatterPlotItem(pos=po[:, :3], size=7))
        gvw.addItem(pyqtgraph.opengl.GLScatterPlotItem(
            pos=po[:, :3] + 8 * po[:, 3:], size=4, color=(1, 0, 0, 1)))
    gvw.show()
    gvw.readQImage().save('head_sensors.png')
    app.exec_()
