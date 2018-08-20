# -*- coding: utf-8 -*-
import argparse
import os
import numpy
import shutil
from tvb.recon.algo.service.volume import VolumeService
from tvb.recon.dax import AtlasSuffix
from tvb.recon.dax.mappings import OutputConvFiles, AsegFiles, T1Files
from tvb.recon.io.factory import IOUtils
from tvb.recon.io.generic import GenericIO


def create_tvb_dataset(atlas_suffix: AtlasSuffix, mri_direc: os.PathLike,
                       region_details_direc: os.PathLike,
                       weights_file: os.PathLike,
                       tracts_file: os.PathLike,
                       out_dir: os.PathLike,
                       bring_t1=False):
    weights_matrix = numpy.loadtxt(str(weights_file), dtype='i', delimiter=' ')
    weights_matrix += weights_matrix.T

    tracts_matrix = numpy.loadtxt(str(tracts_file), dtype='f', delimiter=' ')
    tracts_matrix += tracts_matrix.T

    is_cortical_rm = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.CORTICAL_TXT.value.replace("%s", atlas_suffix)), usecols=[0],
        dtype='i')
    region_names = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.CENTERS_TXT.value.replace("%s", atlas_suffix)), usecols=[0],
        dtype="str")
    region_centers = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.CENTERS_TXT.value.replace("%s", atlas_suffix)), usecols=[1, 2, 3])
    region_areas = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.AREAS_TXT.value.replace("%s", atlas_suffix)), usecols=[0])
    region_orientations = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.ORIENTATIONS_TXT.value.replace("%s", atlas_suffix)),
        usecols=[0, 1, 2])
    rm_idx = numpy.genfromtxt(
        os.path.join(region_details_direc, AsegFiles.RM_TO_APARC_ASEG_TXT.value.replace("%s", atlas_suffix)),
        usecols=[0, 1], dtype='i')
    rm_index_dict = dict(zip(rm_idx[:, 0], rm_idx[:, 1]))
    print(rm_index_dict)

    genericIO = GenericIO()
    genericIO.write_connectivity_zip(out_dir, weights_matrix, tracts_matrix, is_cortical_rm, region_names,
                                     region_centers, region_areas, region_orientations, atlas_suffix)

    aparc_aseg_file = os.path.join(mri_direc, T1Files.APARC_ASEG_NII_GZ.value.replace("%s", atlas_suffix))
    aparc_aseg_volume = IOUtils.read_volume(aparc_aseg_file)

    volume_service = VolumeService()
    aparc_aseg_cor_volume = volume_service.change_labels_of_aparc_aseg(atlas_suffix, aparc_aseg_volume, rm_index_dict,
                                                                       weights_matrix.shape[0])
    IOUtils.write_volume(os.path.join(out_dir, OutputConvFiles.APARC_ASEG_COR_NII_GZ.value.replace("%s", atlas_suffix)),
                         aparc_aseg_cor_volume)

    if bring_t1:
        shutil.copy2(os.path.join(mri_direc, "T1.nii.gz"), out_dir)

    if len(atlas_suffix) == 0:
        atlas_name = "default"
    else:
        atlas_name = atlas_suffix[1:]
    message = "%s_done" % atlas_name
    filename = os.path.join(out_dir, message+".txt")
    print("Writing file %s..." % filename)
    numpy.savetxt(filename, numpy.array([message.replace("_", " ")+"!"]), fmt="%s")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert pipeline output to TVB format")
    parser.add_argument("-p", help="Call from Pegasus WMS", required=False, action="store_true")

    parser.add_argument("atlas_suffix")
    parser.add_argument("mri_dir")
    parser.add_argument("rm_details_dir")
    parser.add_argument("weights_file")
    parser.add_argument("tracts_file")
    parser.add_argument("output_dir")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    if args.p:
        if args.atlas_suffix == "default":
            create_tvb_dataset(
                "",
                args.mri_dir,
                args.rm_details_dir,
                args.weights_file,
                args.tracts_file,
                args.output_dir
            )
        else:
            create_tvb_dataset(
                args.atlas_suffix,
                args.mri_dir,
                args.rm_details_dir,
                args.weights_file,
                args.tracts_file,
                args.output_dir
            )

    else:
        create_tvb_dataset(
            args.atlas_suffix,
            args.mri_dir,
            args.rm_details_dir,
            args.weights_file,
            args.tracts_file,
            args.output_dir,
            True
        )
