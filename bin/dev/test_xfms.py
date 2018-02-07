# -*- coding: utf-8 -*-
# Tools for building full brain network models from standard structural MR scans.
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2017, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

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

