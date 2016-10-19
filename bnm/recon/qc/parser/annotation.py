from nibabel.freesurfer.io import read_annot

from bnm.recon.snapshot.model.annotation import Annotation


class AnnotationParser(object):

    def parse(self, annot_path):
        [region_mapping, color_table, region_names] = read_annot(annot_path)

        color_mapping_list = [[0 for _ in xrange(4)] for _ in xrange(len(region_mapping))]
        for i in range(0, len(region_mapping)):
            for j in range(0, 4):
                color_mapping_list[i][j] = round((color_table[region_mapping[i]][j] / 255.0), 2)

        return Annotation(region_mapping, color_mapping_list, region_names)
