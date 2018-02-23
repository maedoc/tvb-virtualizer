#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# imports
import os
import sys
import argparse
import logging
import nibabel as nb
import numpy as np

def label_volume_centers(label_volume):
    """Generate tuples (label, x, y, z) """

    log = logging.getLogger('label_volume_centers')
    vol = label_volume.get_data()
    aff = label_volume.affine
    for val in np.unique(vol):
        vox_idx = np.argwhere(vol == val)
        xyz = aff.dot(np.c_[vox_idx, np.ones(vox_idx.shape[0])].T)[:3].T
        x, y, z = xyz.mean(axis=0)
        log.debug('unique value %d has center (%f, %f, %f)',
                  val, x, y, z)
        yield val, (x, y, z)
    

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


def write_results(centers, output_tsv, label_map=None):
    """ Writing results to output_tsv file."""
    with open(output_tsv, 'w') as fd:
        for val, (x, y, z) in centers:
            val_ = label_map[val] if label_map else val
            fd.write('%f\t%f\t%f\t%s\n' % (x, y, z, val_))
        

def build_argparser():
    """building using argparse terminal interface library."""
    parser = argparse.ArgumentParser()
    parser.add_argument("label_volume", help="nibabel-loadable label volume to analyze")
    parser.add_argument("output_tsv", help="tab-separated file to write")
    parser.add_argument("--loglevel", help="set logging level", default="INFO")
    parser.add_argument("--fs-names", help="save FS parcel names", action="store_true")
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
    
    log.info('computing centers')
    centers = list(label_volume_centers(vol))
    
    lut_map = None
    if parse.fs_names:
        log.info('loading FS LUT')
        lut_path = parse.fs_lut or (
            os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt'))
        lut_map = build_fs_label_name_map(lut_path)
    
    log.info('writing results to %r', parse.output_tsv)
    write_results(centers, parse.output_tsv, label_map=lut_map)
    

if __name__ == '__main__':
    main()
