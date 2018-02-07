# -*- encoding: utf-8 -*-

"""
Plot a slice of the T1.mgz with vertices from the pial surfaces.

"""

import os
import os.path
import numpy as np
import pylab as pl
import nibabel.freesurfer as fs


# assuming cp -r $FREESURFER_HOME/subjects/fsaverage5 data/ folder,
here = os.path.dirname(os.path.abspath(__file__))
fname = lambda fn: os.path.join(here, '../data/fsaverage5', fn)

# load FS T1 (talairach.xfm is from -i vol.nii to T1.mgz ?)
img = fs.load(fname('mri/T1.mgz'))  # type: fs.MGHImage
vol = img.get_data().transpose((0, 2, 1))
aff = img.affine
inv_aff = np.linalg.inv(aff)

# load left pial surface
verts, faces = fs.read_geometry(fname('surf/lh.pial'))

# choose sagittal slice by X coord
x = -32.0
i = int(inv_aff.dot(np.r_[x, 0.0, 0.0, 1.0])[0])

# mask vertices around chosen coord
vert_mask = np.c_[verts[:, 0] > (x - 2), verts[:, 0] < (x + 2)].all(axis=1)
in_slice_verts = isv_y, isv_z = verts[vert_mask, 1:].T

# plot slice & vertices in mask
fig = pl.figure(figsize=(15, 5))
pl.subplot(131)
pl.imshow(vol[i].T, cmap='gray', aspect='equal', extent=[-128.0, 128, -128.0, 128.0])
pl.plot(isv_y, isv_z, 'y.')
pl.xlabel('+Y Anterior')
pl.ylabel('+Z Superior')

# again for y
pl.subplot(132)
y = -10.0
j = int(inv_aff.dot(np.r_[0.0, y, 0.0, 1.0])[1])
vert_mask = np.c_[verts[:, 1] > (y - 2), verts[:, 1] < (y + 2)].all(axis=1)
isv_x, isv_y, isv_z = verts[vert_mask].T
pl.imshow(vol[:, j].T, cmap='gray', aspect='equal', extent=[-128.0, 128, -128.0, 128.0])
pl.plot(isv_x, isv_z, 'y.')
pl.xlabel('+X Right')
pl.ylabel('+Z Superior')

# & z
pl.subplot(133)
z = 0.0
k = int(inv_aff.dot(np.r_[0.0, 0.0, z, 1.0])[2])
vert_mask = np.c_[verts[:, 2] > (z - 2), verts[:, 2] < (z + 2)].all(axis=1)
isv_x, isv_y, isv_z = verts[vert_mask].T
pl.imshow(vol[:, ::-1, k].T, cmap='gray', aspect='equal', extent=[-128.0, 128, -128.0, 128.0])
pl.plot(isv_x, isv_y, 'y.')
pl.xlabel('+X Right')
pl.ylabel('+Y Anterior')

fig.suptitle('lh.pial on T1 @ (%d, %d, %d) (%0.1f, %0.1f %0.1f)' % (i, j, k, x, y, z))
pl.tight_layout()
pl.show()
