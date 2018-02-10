# -*- coding: utf-8 -*-

import argparse
import os

from tvb.recon.logger import get_logger
from tvb.recon.model.constants import *
from tvb.recon.model.constants import SNAPSHOT_NAME
from tvb.recon.qc.image.processor import ImageProcessor
from tvb.recon.qc.image.transformer import ImageTransformer

arg_1vol = "1vol"
arg_2vols = "2vols"
arg_3vols = "3vols"
arg_surf_annot = "surf_annot"
arg_vol_surf = "vol_surf"
arg_vol_white_pial = "vol_white_pial"
arg_connectivity_measure = "aparc_aseg_conn"


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate a BNM snapshot")
    subparsers = parser.add_subparsers(title='Sub Commands', dest='subcommand')

    parser.add_argument("--snapshot_name",
                        help="String to optionally substitute the default constant SNAPSHOT_NAME in the output filenames.",
                        action="store", default=SNAPSHOT_NAME, required=False)

    parser.add_argument("--ras_transform", help="This flag applies the RAS orientation on volumes.",
                        action="store_true")
    parser.add_argument("--center_surface",
                        help="Centers surfaces using the ras centering point. "
                             "This will correctly align the surface contour over a RAS oriented volume. "
                             "If the flag is not used, the correct surface contour will be displayed but "
                             "it will not be perfectly aligned over the volume. Always use the original "
                             "surfaces (not already centered ones) with an overlapping sub-command.",
                        action="store_true")

    parser.add_argument("--use_cc_point",
                        help="By specifying this argument, the Corpus Callosum point will be used when taking the snapshots.",
                        action="store_true")

    subcommand_1_vol = subparsers.add_parser(
        arg_1vol, help='Display a single volume')
    subcommand_2_vols = subparsers.add_parser(
        arg_2vols, help='Display 2 volumes overlapped')
    subcommand_3_vols = subparsers.add_parser(
        arg_3vols, help='Display 3 volumes overlapped')
    subcommand_surf_annot = subparsers.add_parser(
        arg_surf_annot, help='Display a surface with annotations')
    subcommand_vol_surf = subparsers.add_parser(arg_vol_surf,
                                                help='Display a surface overlapped on a volume. '
                                                     'The flag --center_surface can be used with this sub-command.')
    subcommand_vol_2surf = subparsers.add_parser(arg_vol_white_pial,
                                                 help='Display white and pial freesurfer surfaces over a volume. '
                                                      'The flag --center_surface can be used with this sub-command.')
    subcommand_conn_measure = subparsers.add_parser(arg_connectivity_measure,
                                                    help='Display aseg volume with a connectivity measure (eg: epileptogenicity values)')

    subcommand_1_vol.add_argument("volume")

    subcommand_2_vols.add_argument("background")
    subcommand_2_vols.add_argument("overlay")

    subcommand_3_vols.add_argument("background")
    subcommand_3_vols.add_argument("overlay1")
    subcommand_3_vols.add_argument("overlay2")

    subcommand_vol_surf.add_argument("background")
    subcommand_vol_surf.add_argument("surfaces_list", nargs='+')

    subcommand_surf_annot.add_argument("surface")
    subcommand_surf_annot.add_argument("annotation")

    subcommand_vol_2surf.add_argument("background")
    subcommand_vol_2surf.add_argument("-resampled_surface_name", default='')
    subcommand_vol_2surf.add_argument(
        "-gifti", help="Use gifti white and pial surfaces", action="store_true")

    subcommand_conn_measure.add_argument("aparc_aseg_volume")
    subcommand_conn_measure.add_argument("region_values")
    subcommand_conn_measure.add_argument("-fs_to_conn_mapping", default=FS_TO_CONN_INDICES_MAPPING_PATH,
                                         help='Specify a mapping file. File data/mapping_FS_88.txt is used by default. '
                                              'This contains the mapping from Freesurfer labels to connectivity indices.')
    subcommand_conn_measure.add_argument(
        "-background", default='', help='Specify a background volume')

    return parser.parse_args()


def check_files_for_cc_exist():
    mri_directory = os.environ[MRI_DIRECTORY]
    if mri_directory is "":
        message = "There is no value assigned to %s environment variable. It should specify the path to %s." % (
            MRI_DIRECTORY, T1_RAS_VOLUME)
        logger.error(message)
        raise Exception(message)

    t1_name = os.environ[T1_RAS_VOLUME]
    if t1_name is "":
        message = "There is no value assigned to %s environment variable. It should specify the name of T1 RAS oriented " \
                  "volume" % T1_RAS_VOLUME
        logger.error(message)
        raise Exception(message)

    t1_path = os.path.join(mri_directory, t1_name)
    if not os.path.exists(t1_path):
        message = "File %s does not exist. Please change %s value to %s path." % (
            t1_path, MRI_DIRECTORY, T1_RAS_VOLUME)
        logger.error(message)
        raise Exception(message)

    if not os.path.exists(os.path.expandvars(CC_POINT_FILE)):
        message = "File %s does not exist." % CC_POINT_FILE
        logger.error(message)
        raise Exception(message)


if __name__ == "__main__":
    logger = get_logger(__name__)

    args = parse_arguments()
    abs_path = os.path.abspath(os.path.dirname(__file__))

    snapshots_directory = os.environ[SNAPSHOTS_DIRECTORY_ENVIRON_VAR]
    if snapshots_directory is "":
        snapshots_directory = SNAPSHOTS_DIRECTORY
        logger.warning(
            "There is no value assigned to %s environment variable. The snapshots will be in %s directory by default.",
            SNAPSHOTS_DIRECTORY_ENVIRON_VAR, SNAPSHOTS_DIRECTORY)

    snapshot_count = int(os.environ.get(SNAPSHOT_NUMBER_ENVIRON_VAR, 0))

    imageTransformer = ImageTransformer(abs_path)
    imageTransformer.use_ras_transform = args.ras_transform
    imageTransformer.use_center_surface = args.center_surface

    if args.use_cc_point:
        check_files_for_cc_exist()

    imageProcessor = ImageProcessor(
        snapshots_directory=snapshots_directory, snapshot_count=snapshot_count)

    if args.subcommand == arg_1vol:
        volume_path = imageTransformer.transform_single_volume(
            os.path.expandvars(args.volume))
        imageProcessor.show_single_volume(os.path.expandvars(volume_path), args.use_cc_point,
                                          snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_2vols:
        background, overlay = imageTransformer.transform_2_volumes(os.path.expandvars(args.background),
                                                                   os.path.expandvars(args.overlay))
        imageProcessor.overlap_2_volumes(os.path.expandvars(background), os.path.expandvars(overlay), args.use_cc_point,
                                         snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_3vols:
        background, overlay1, overlay2 = imageTransformer.transform_3_volumes(os.path.expandvars(args.background),
                                                                              os.path.expandvars(
                                                                                  args.overlay1),
                                                                              os.path.expandvars(args.overlay2))
        imageProcessor.overlap_3_volumes(os.path.expandvars(background), os.path.expandvars(overlay1),
                                         os.path.expandvars(
                                             overlay2), args.use_cc_point,
                                         snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_surf_annot:
        imageProcessor.overlap_surface_annotation(os.path.expandvars(args.surface), os.path.expandvars(args.annotation),
                                                  snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_vol_surf:
        background, surfaces_paths_list = imageTransformer.transform_volume_surfaces(
            os.path.expandvars(args.background), args.surfaces_list)
        imageProcessor.overlap_volume_surfaces(os.path.expandvars(background), surfaces_paths_list, args.center_surface,
                                               args.use_cc_point, snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_vol_white_pial:
        surfaces_path = os.environ[SURFACES_DIRECTORY_ENVIRON_VAR]
        background, surfaces_paths_list = imageTransformer.transform_volume_white_pial(
            os.path.expandvars(args.background), os.path.expandvars(
                args.resampled_surface_name),
            os.path.expandvars(surfaces_path), args.gifti)
        imageProcessor.overlap_volume_surfaces(os.path.expandvars(background), surfaces_paths_list,
                                               args.center_surface, args.use_cc_point, snapshot_name=args.snapshot_name)

    elif args.subcommand == arg_connectivity_measure:
        aparc_aseg_volume_path = imageTransformer.transform_single_volume(
            os.path.expandvars(args.aparc_aseg_volume))
        background_volume_path = args.background
        if background_volume_path != '':
            background_volume_path = imageTransformer.transform_single_volume(
                os.path.expandvars(args.background))
        imageProcessor.show_aparc_aseg_with_new_values(os.path.expandvars(aparc_aseg_volume_path),
                                                       os.path.expandvars(
                                                           args.region_values),
                                                       os.path.expandvars(
                                                           background_volume_path),
                                                       args.use_cc_point,
                                                       os.path.expandvars(
                                                           args.fs_to_conn_mapping),
                                                       snapshot_name=args.snapshot_name)

    try:
        for created_file in imageTransformer.created_files:
            os.remove(created_file)
        os.rmdir(imageTransformer.converted_files_directory_path)
    except OSError:
        logger.error("Cannot delete files created at transform step")
