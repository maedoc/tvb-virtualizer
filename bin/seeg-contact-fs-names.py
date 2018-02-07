#!/usr/bin/env python3
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

# imports
import os
import sys
import argparse
import logging
import nibabel as nb
import numpy as np
import subprocess


def load_aa_ras(aa_path):
    """Loading a aa_ras using aa_path on temfile while viewing any temporary
       file with exists with .nii.gz and reading it using nearest"""
    with tempfile.NamedTemporaryFile(suffix='.nii.gz') as tf:
        # TODO use cli wrapped commands
        subprocess.check_call([
            'mri_convert', aa_path, tf.name,
            '--out_orientation', 'RAS', '-rt', 'nearest'
        ])
        aa_img = nb.load(tf.name)
    return aa_img


def load_contacts(contact_path):
    """opening contact_path and reading them using three path x,y,z."""
    contacts = []
    with open(contact_path, 'r') as fd:
        for line in fd.readlines():
            name, x, y, z = line.strip().split()
            contacts.append((name, float(x), float(y), float(z)))
    return contacts


def contact_fs_names(aa_img, contacts, lut):
    """ Adding names to name,x,y,z to i,j,k to yield name and aa_name."""
    inv_aff = np.linalg.inv(aa_img.affine)
    aa_dat = aa_img.get_data()
    for name, x, y, z in contacts:
        i, j, k = ijk = inv_aff.dot(np.r_[x, y, z, 1])[:-1].astype('i')
        aa_val = aa_dat[i, j, k]
        aa_name = lut[aa_val]
        yield name, aa_name
    

def build_fs_label_name_map(lut_path):
    """ Reading file using lut_path and stripping lines to
        see if # exists on line one."""
    lut = {}
    with open(lut_path, 'r') as fd:
        for line in fd.readlines():
            if not line[0] == '#' and line.strip():
                val, name, _, _, _, _ = line.strip().split()
                lut[int(val)] = name
    return lut


def write_results(results, output_tsv):
    """ Writing results to output_tsv file."""
    with open(output_tsv, 'w') as fd:
        for name, aa_name in results:
            fd.write('%s\t%s\n' % (name, aa_name))


def build_argparser():
    """building using argparse terminal interface libarary."""
    parser = argparse.ArgumentParser()
    parser.add_argument("label_volume", help="nibabel-loadable label volume to analyze")
    parser.add_argument("contacts", help="file produced by seeg-ct.sh describing contact positions")
    parser.add_argument("output_tsv", help="tab-separated file to write")
    parser.add_argument("--loglevel", help="set logging level", default="INFO")
    parser.add_argument("--fs-lut", help="path to FreeSurferColorLUT.txt")
    return parser
   
    
def main():
    """ main library contains build_argparser() whith will echo
            all parser.add_argument() helps, print log.info() details and os path to
            FreeSurferColorLUT.txt."""
    parser = build_argparser()
    parse = parser.parse_args()
    print(parse)
    logging.basicConfig(level=getattr(logging, parse.loglevel))
    log = logging.getLogger(sys.argv[0])
    
    log.info('reading %r', parse.label_volume)
    vol = nb.load(parse.label_volume)
    
    log.info('loading FS LUT')
    lut_path = parse.fs_lut or (
        os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt'))
    lut_map = build_fs_label_name_map(lut_path)
    
    log.info('reading %r', parse.contacts)
    contacts = load_contacts(parse.contacts)
    
    log.info('computing contact names')
    results = list(contact_fs_names(vol, contacts, lut_map))
    
    log.info('writing results to %r', parse.output_tsv)
    write_results(results, parse.output_tsv)
    

if __name__ == '__main__':
    main()