# -*- coding: utf-8 -*-

"""
Created on Tue Nov 15 18:03:10 2016

@author: dionperd
"""

b0=nibabel.load(DMR+'/b0.nii.gz')
v2d=b0.get_affine()

b0ras=nibabel.load(DMR+'/b0-in-ras.nii.gz')
v2dras=b0ras.get_affine()

d2v=np.linalg.inv(v2d)
d2dras=np.dot(d2v,v2dras)

t2d=np.loadtxt(DMR+'/t2d.mat')

t2dras=np.dot(t2d,d2dras)

dras2t=np.linalg.inv(t2dras)

np.savetxt(DMR+'/t2dras.mat',t2dras)
np.savetxt(DMR+'/dras2t.mat',dras2t)

t1=nibabel.load(MRI+'/T1.nii.gz')
v2tras=t1.get_affine()

t1mgz=nibabel.load(MRI+'/T1mgz.nii.gz')
v2t=t1mgz.get_affine()

t2v=np.linalg.inv(v2t)
t2tras=np.dot(t2v,v2tras)

