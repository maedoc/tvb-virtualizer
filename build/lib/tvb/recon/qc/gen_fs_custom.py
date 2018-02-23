import os
import sys

from tvb.recon.algo.service.mapping_service import MappingService
from tvb.recon.io.factory import IOUtils
from tvb.recon.io.generic import GenericIO

if __name__ == "__main__":
    direc = sys.argv[1]
    out_file = sys.argv[2]

    annot_cort_lh = IOUtils.read_annotation(os.path.join(direc, "lh.aparc.annot"))
    annot_cort_rh = IOUtils.read_annotation(os.path.join(direc, "rh.aparc.annot"))

    annot_subcort_lh = IOUtils.read_annotation(os.path.join(direc, "lh.aseg.annot"))
    annot_subcort_rh = IOUtils.read_annotation(os.path.join(direc, "rh.aseg.annot"))

    mapping = MappingService(annot_cort_lh, annot_cort_rh, annot_subcort_lh, annot_subcort_rh)

    dict_fs_custom = mapping.get_mapping_for_connectome_generation()

    genericIO = GenericIO()
    genericIO.write_dict_to_txt_file(dict_fs_custom, out_file)