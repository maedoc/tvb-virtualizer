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
Prepare tvb Python package for setup Install.
"""

import shutil
from setuptools import setup, find_packages

requirements = (
    'numpy',
    'scipy',
    'scikit-learn',
    'matplotlib',
    'trimesh',
    'anytree',
    'Pegasus',
    'h5py',
    'pytest',
    'Cython',
    'gdist',
)

setup(
    name="tvb",
    description="Brain Network Models - Reconstruction tool from structural MR scans",
    packages=find_packages(),
    version="0.1",
    license="GPL",
    author="TVB_TEAM",
    author_email='tvb.admin@thevirtualbrain.org',
    url='http://www.thevirtualbrain.org',
    install_requires=requirements,
    downloa_url='https://github.com/the-virtual-brain/tvb-recon'

)

# Clean after install
shutil.rmtree('tvb.egg-info', True)
