# -*- coding: utf-8 -*-

import os
import numpy
from collections import OrderedDict
from bnm.recon.io.factory import IOUtils
from datetime import datetime

DEFAULT_LUT = 'FreeSurferColorLUT_INS_test.txt'

class AnnotationService(object):

    def default_lut(self):
        return DEFAULT_LUT

    def read_lut(self, lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT),
                 key_mode='label'):
        f = open(lut_path, "r")
        l = list(f)
        f.close()
        ii = -1
        if key_mode == 'label':
            names = OrderedDict()
            colors = OrderedDict()
            labels = []
            for line in l:
                temp = line.split()
                try:
                    label = int(temp[0])
                    ii += 1
                    labels.append(label)
                    names[labels[ii]] = temp[1]
                    colors[labels[ii]] = [int(temp[2]), int(temp[3]), int(temp[4]), int(temp[5])]
                except:
                    pass
        elif key_mode == 'name':
            labels = OrderedDict()
            colors = OrderedDict()
            names = []
            for line in l:
                temp = line.split()
                try:
                    label = int(temp[0])
                    ii += 1
                    names.append(temp[1])
                    labels[names[ii]] = label
                    colors[names[ii]] = [int(temp[2]), int(temp[3]), int(temp[4]), int(temp[5])]
                except:
                    pass
        return labels, names, colors

    def rgb_to_fs_magic_number(self, rgb):
        return rgb[0] + 256 * rgb[1] + 256 * 256 * rgb[2]

    def annot_to_lut(self, annot_path,
                     lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT), add_string=''):
        """
        This function creates from an annotation a new lut_file, or adds new entries to an existing lut file.
        In the latter case, new entries have labels greater than the maximum alredy existing label inside the lut file.
        :param annot_path: path to annotation
        :param lut_path: path to an existing or new lut file
        :param add_string: an optional string to be added at the beginning of each name (i.e., "ctx-lh-")
        :return:
        """
        annotation = IOUtils.read_annotation(annot_path)
        #If this is an already existing lut file:
        if os.path.isfile(lut_path):
            #...find the maximum label in it and add 1
            add_lbl= 1+numpy.max(self.read_lut(lut_path=lut_path, key_mode='label')[0])
        else:
            #...else, set it to 0
            add_lbl=0
        with open(lut_path, 'a') as fd:
            if add_lbl==0:
                #TODO: we should include an environment variable for freesurfer version, and print it here
                fd.write('%s\n' % ("#$Id: " + lut_path + " " +str(datetime.now())))
                fd.write('\n')
                fd.write('%s\t%s\t%s%s%s%s\n' % ("#No.", "Label Name: ", "R   ", "G   ", "B   ", "A   "))
            else:
                fd.write('\n')
            # Leave one line blank
            fd.write('\n')
            fd.write('%s\n' % ("#Patient: " + os.environ['SUBJECT']))
            fd.write('%s\n' % ("#User: " + os.path.split(os.path.expanduser('~'))[-1]))
            fd.write('%s\n' % ("#Annotation path: "+annot_path))
            fd.write('%s\n' % ("#Time: " +str(datetime.now())))
            fd.write('\n')
            #TODO: align columns
            #NOTE!!! that the fourth and fifth columns of color_table are not used in the lut file!!!
            for name, (r, g, b, dummy1, dummy2), lbl in \
                    zip(annotation.region_names, annotation.regions_color_table,range(len(annotation.region_names))):
                fd.write('%d\t%s\t%d %d %d %d\n' % (lbl+add_lbl, add_string+name, r, g, b, 0))

    def lut_to_annot_names_ctab(self, lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT),
                                labels=None):
        _, names_dict, colors = self.read_lut(lut_path=lut_path)
        if labels is None:
            labels = names_dict.keys()
        elif isinstance(labels, basestring):
            labels = numpy.array(labels.split()).astype('i').tolist()
        else:
            labels = numpy.array(labels).astype('i').tolist()
        names = []
        ctab = []
        for lbl in labels:
            names.append(names_dict[lbl])
            rgb = numpy.array(colors[lbl])[:3].astype('int64')
            magic_number = self.rgb_to_fs_magic_number(rgb) * numpy.ones((1,), dtype='int64')
            ctab.append(numpy.concatenate([rgb, numpy.zeros((1,), dtype='int64'), magic_number]))
        ctab = numpy.asarray(ctab).astype('int64')
        return names, ctab

    def annot_names_to_labels(self, names, add_string='',
                              lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT)):
        labels_dict, _, _ = self.read_lut(lut_path=lut_path, key_mode='name')
        labels = []
        # if ctx == 'lh' or ctx == 'rh':
        #     ctx = 'ctx-' + ctx + '-'
        # else:
        #     ctx = ''
        for name in names:
            labels.append(labels_dict[add_string + name])
        return labels

    def annot_to_conn_conf(self, annot_path, conn_conf_path):
        annotation = IOUtils.read_annotation(annot_path)
        with open(conn_conf_path, 'w') as fd:
            for id, name in enumerate(annotation.region_names):
                fd.write('%d\t%s\n' % (id, name))

    def read_input_labels(self, labels=None, ctx=None):
        if labels is not None:
            if isinstance(labels, basestring):
                # Set the target labels
                labels = numpy.array(labels.split()).astype('i').tolist()
        else:
            labels = []
        if isinstance(ctx, basestring):
            ctx = ctx.split()
            for h in ctx:
                if h == 'lh':
                    labels = labels + range(1000, 1036)
                elif h == 'rh':
                    labels = labels + range(2000, 2036)

                    # This function
                    # takes as inputs the labels of a new parcellation, a base name for the parcels and a base color,
                    # and generates the name labels, and colors of the new parcellation's annotation
                    # It splits the RGB color space along the dimension that has a longer margin, in order to create new, adjacent colors
                    # Names are created by just adding increasing numbers to the base name.
        return labels, len(labels)

    def gen_new_parcel_annots(self, parcel_labels, base_name, base_ctab):
        """
        This function creates new names and colors for a new parcellation, based on the original name and color,
        of the super-parcel, these parcels originate from
        :param parcel_labels: an array (number of parcels, ) with the integer>=0 labels of the parcels
        :param base_name: a base name to form the parcels' names
        :param base_ctab: a base RGB triplet to form the parcels' colors
        :return: (names_lbl,ctab_lbl), i.e., the new names and colors of the parcels, respectively
        """
        n_parcels = len(parcel_labels)
        # Names:
        names_lbl = [base_name + "-" + str(item).zfill(2) for item in parcel_labels]
        # Initialize ctab for these labels
        ctab_lbl = numpy.repeat(base_ctab, n_parcels, axis=0)
        # For the RGB coordinate with the bigger distance to 255 or 0
        # distribute that distance  to nParcs values:
        # Find the maximum and minimum RGB coordinates
        ic = numpy.argsort(base_ctab[0, :3])
        # Calculate the distances of the maximum RGB coordinate to 0, and of the minimum one to 255,
        x = 255 - base_ctab[0, ic[0]] >= base_ctab[0, ic[2]]
        dist = numpy.where(x, 255 - base_ctab[0, ic[0]], -base_ctab[0, ic[2]])
        # Pick, out of the two candidates, the coordinate with the longer available range
        ic = numpy.where(x, ic[0], ic[2])
        # Create the step size to run along that range, and make it to be exact
        step = dist / (n_parcels - 1)
        dist = step * n_parcels
        # Assign colors
        ctab_lbl[:, ic] = numpy.array(range(base_ctab[0, ic], base_ctab[0, ic] + dist, step), dtype='int')
        # Fix 0 and 255 as min and max RGB values
        ctab_lbl[:, :3][ctab_lbl[:, :3] < 0] = 0
        ctab_lbl[:, :3][ctab_lbl[:, :3] > 255] = 255
        # Calculate the resulting freesurfer magic number for each new RGB triplet
        ctab_lbl[:, 4] = numpy.array([self.rgb_to_fs_magic_number(ctab_lbl[icl, :3])
                                      for icl in range(n_parcels)])
        return (names_lbl, ctab_lbl)


