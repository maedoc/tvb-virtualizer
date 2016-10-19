import numpy


class Annotation(object):
    region_mapping = None
    color_table = None
    region_names = None

    def __init__(self, labels, ctab, names):
        self.region_mapping = labels
        self.color_table = ctab
        self.region_names = names


    def face_colors(self, triangles):
        result_colors = [0 for _ in xrange(len(triangles))]
        for i, tri in enumerate(triangles):
            result_colors[i] = self.color_table[tri[1]]
            vert1_color = numpy.dot(self.color_table[tri[0]], 0.33)
            vert2_color = numpy.dot(self.color_table[tri[1]], 0.33)
            vert3_color = numpy.dot(self.color_table[tri[2]], 0.33)
            color_aux = numpy.add(vert1_color, vert2_color)
            result_colors[i] = numpy.add(color_aux, vert3_color)
        return result_colors