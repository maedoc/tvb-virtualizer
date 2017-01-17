# -*- coding: utf-8 -*-

import os
import numpy
import scipy.ndimage
from bnm.recon.logger import get_logger
from bnm.recon.algo.service.annotation import AnnotationService
from bnm.recon.io.factory import IOUtils
from bnm.recon.model.volume import Volume
from bnm.recon.model.constants import NPY_EXTENSION

class VolumeService(object):
    logger = get_logger(__name__)

    def __init__(self):
        self.annotation_service = AnnotationService()

    def vol_to_ext_surf_vol(self, in_vol_path, labels=None, hemi=None, out_vol_path=None, labels_surf=None,
                            labels_inner='0'):
        """
        Separate the voxels of the outer surface of a structure, from the inner ones. Default behavior: surface voxels
        retain their label, inner voxels get the label 0, and the input file is overwritten by the output.
        """

        labels, number_of_labels = self.annotation_service.read_input_labels(labels=labels, hemi=hemi)
        # Set the labels for the surfaces
        if labels_surf is None:
            labels_surf = labels
        else:
            # Read the surface labels and make sure there is one for each label
            labels_surf = numpy.array(labels_surf.split()).astype('i')
            if len(labels_surf) == 1:
                labels_surf = numpy.repeat(labels_inner, number_of_labels).tolist()
            elif len(labels_surf) != number_of_labels:
                self.logger.warning("Output labels for surface voxels are neither of length 1 nor of length equal to "
                                    "the one of target labels")
                return
            else:
                labels_surf = labels_surf.tolist()
        # Read the inner, non-surface labels
        labels_inner = numpy.array(labels_inner.split()).astype('i')
        # ...and make sure there is one for each label
        if len(labels_inner) == 1:
            labels_inner = numpy.repeat(labels_inner, number_of_labels).tolist()
        elif len(labels_inner) != number_of_labels:
            self.logger.warning("Output labels for inner voxels are neither of length 1 nor of length equal to the one "
                                "of the target labels")
            return
        else:
            labels_inner = labels_inner.tolist()

        # Read the input volume...
        volume = IOUtils.read_volume(in_vol_path)

        # Neigbors' grid sharing a face
        border_grid = numpy.c_[numpy.identity(3), -numpy.identity(3)].T.astype('i')
        n_border = 6

        out_volume = Volume(numpy.array(volume.data), volume.affine_matrix, volume.header)

        # Initialize output indexes
        out_ijk = []

        for label_index in xrange(number_of_labels):
            current_label = labels[label_index]
            # Get the indexes of all voxels of this label:
            label_volxels_i, label_voxels_j, label_voxels_k = numpy.where(volume.data == current_label)
            # and for each voxel
            for voxel_index in xrange(label_volxels_i.size):
                # indexes of this voxel:
                current_voxel_i, current_voxel_j, current_voxel_k = \
                    label_volxels_i[voxel_index], label_voxels_j[voxel_index], label_voxels_k[voxel_index]
                # Create the neighbors' grid sharing a face
                ijk_grid = border_grid + \
                           numpy.tile(numpy.array([current_voxel_i, current_voxel_j, current_voxel_k]), (n_border, 1))
                # Remove voxels outside the image
                indices_inside_image = numpy.all([(ijk_grid[:, 0] >= 0), (ijk_grid[:, 0] < volume.dimensions[0]),
                                               (ijk_grid[:, 1] >= 0), (ijk_grid[:, 1] < volume.dimensions[1]),
                                               (ijk_grid[:, 2] >= 0), (ijk_grid[:, 2] < volume.dimensions[2])],
                                              axis=0)
                ijk_grid = ijk_grid[indices_inside_image, :]
                try:
                    # If all face neighbors are of the same label...
                    if numpy.all(volume.data[ijk_grid[:, 0], ijk_grid[:, 1], ijk_grid[:, 2]] == numpy.tile(
                            volume.data[current_voxel_i, current_voxel_j, current_voxel_k],
                            (n_border, 1))):
                        # ...set this voxel to the corresponding inner target label
                        out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_inner[label_index]
                    else:
                        # ...set this voxel to the corresponding surface target label
                        out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_surf[label_index]
                        out_ijk.append([current_voxel_i, current_voxel_j, current_voxel_k])
                except ValueError:  # empty grid
                    self.logger.error("Error at voxel ( %s, %s, %s ) of label %s: It appears to have no common-face "
                                      "neighbors inside the image!", str(current_voxel_i), str(current_voxel_j),
                                      str(current_voxel_k), str(current_label))
                    return

        if out_vol_path is None:
            out_vol_path = in_vol_path

        IOUtils.write_volume(out_vol_path, out_volume)

        # save the output indexes that survived masking
        out_ijk = numpy.vstack(out_ijk)
        filepath = os.path.splitext(out_vol_path)[0]
        numpy.save(filepath + "-idx.npy", out_ijk)
        numpy.savetxt(filepath + "-idx.txt", out_ijk, fmt='%d')

    def mask_to_vol(self, in_vol_path, mask_vol_path, out_vol_path=None, labels=None, hemi=None, vol2mask_path=None,
                    vn=1, th=0.999, labels_mask=None, labels_nomask='0'):
        """
        Identify the voxels that are neighbors within a voxel distance vn, to a mask volume, with a mask threshold of th
        Default behavior: we assume a binarized mask and set th=0.999, no neighbors search, only looking at the exact
        voxel position, i.e., vn=0. Accepted voxels retain their label, whereas rejected ones get a label of 0
        """

        # Set the target labels:
        labels, number_of_labels = self.annotation_service.read_input_labels(labels=labels, hemi=hemi)
        # Set the labels for the selected voxels
        if labels_mask is None:
            labels_mask = labels

        else:
            # Read the labels and make sure there is one for each label
            labels_mask = numpy.array(labels_mask.split()).astype('i')

            if len(labels_mask) == 1:
                labels_mask = numpy.repeat(labels_mask, number_of_labels).tolist()

            elif len(labels_mask) != number_of_labels:
                self.logger.warning("Output labels for selected voxels are neither of length 1 nor of length equal to "
                                    "the one of target labels")
                return

            else:
                labels_mask = labels_mask.tolist()

        # Read the excluded labels and make sure there is one for each label
        labels_nomask = numpy.array(labels_nomask.split()).astype('i')
        if len(labels_nomask) == 1:
            labels_nomask = numpy.repeat(labels_nomask, number_of_labels).tolist()

        elif len(labels_nomask) != number_of_labels:
            self.logger.warning("Output labels for excluded voxels are neither of length 1 nor of length equal to the "
                                "one of the target labels")
            return

        else:
            labels_nomask = labels_nomask.tolist()

        volume = IOUtils.read_volume(in_vol_path)

        mask_vol = IOUtils.read_volume(mask_vol_path)

        # Compute the transform from vol ijk to mask ijk:
        ijk2ijk = numpy.identity(4)

        # If vol and mask are not in the same space:
        if os.path.exists(str(vol2mask_path)):
            # read the xyz2xyz transform and apply it to the inverse mask affine transform to get an ijk2ijk transform.
            xyz2xyz = numpy.loadtxt(vol2mask_path)
            ijk2ijk = volume.affine_matrix.dot(numpy.dot(xyz2xyz, numpy.linalg.inv(mask_vol.affine_matrix)))

        # Construct a grid template of voxels +/- vn voxels around each ijk voxel, sharing at least a corner
        grid = numpy.meshgrid(range(-vn, vn + 1, 1), range(-vn, vn + 1, 1), range(-vn, vn + 1, 1), indexing='ij')
        grid = numpy.c_[numpy.array(grid[0]).flatten(), numpy.array(grid[1]).flatten(), numpy.array(grid[2]).flatten()]
        n_grid = grid.shape[0]

        out_volume = Volume(numpy.array(volume.data), volume.affine_matrix, volume.header)

        # Initialize output indexes
        out_ijk = []

        # For each target label:
        for label_index in xrange(number_of_labels):
            current_label = labels[label_index]
            # Get the indexes of all voxels of this label:
            label_voxels_i, label_voxels_j, label_voxels_k = numpy.where(volume.data == current_label)

            for voxel_index in xrange(label_voxels_i.size):
                current_voxel_i, current_voxel_j, current_voxel_k = \
                    label_voxels_i[voxel_index], label_voxels_j[voxel_index], label_voxels_k[voxel_index]
                # TODO if necessary: deal with voxels at the edge of the image, such as brain stem ones...
                #     if any([(i==0), (i==mask_shape[0]-1),(j==0), (j==mask_shape[0]-1),(k==0), (k==mask_shape[0]-1)]):
                #               mask_shape[i,j,k]=0
                #               continue

                # ...get the corresponding voxel in the mask volume:
                ijk = numpy.round(ijk2ijk.dot(numpy.array([current_voxel_i, current_voxel_j, current_voxel_k, 1]))[:3]).astype('i')

                # Make sure this point is within image limits
                for cc in xrange(3):
                    if ijk[cc] < 0:
                        ijk[cc] = 0

                    elif ijk[cc] >= mask_vol.dimensions[cc]:
                        ijk[cc] = mask_vol.dimensions[cc] - 1

                # If this is a voxel to keep, set it so...
                if mask_vol.data[ijk[0], ijk[1], ijk[2]] >= th:
                    out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_mask[label_index]
                    out_ijk.append([current_voxel_i, current_voxel_j, current_voxel_k])

                elif vn > 0:
                    # If not, and as long as vn>0 check whether any of its vn neighbors is a mask voxel.
                    # Generate the specific grid centered at the vertex ijk
                    ijk_grid = grid + numpy.tile(ijk, (n_grid, 1))

                    # Remove voxels outside the mask volume
                    indexes_within_limits = numpy.all([(ijk_grid[:, 0] >= 0), (ijk_grid[:, 0] < mask_vol.dimensions[0]),
                                                       (ijk_grid[:, 1] >= 0), (ijk_grid[:, 1] < mask_vol.dimensions[1]),
                                                       (ijk_grid[:, 2] >= 0),
                                                       (ijk_grid[:, 2] < mask_vol.dimensions[2])],
                                                      axis=0)
                    ijk_grid = ijk_grid[indexes_within_limits, :]

                    try:
                        # If none of these points is a mask point:
                        if (mask_vol.data[ijk_grid[:, 0], ijk_grid[:, 1], ijk_grid[:, 2]] < th).all():
                            out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_nomask[label_index]

                        else:  # if any of them is a mask point:
                            out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_mask[label_index]
                            out_ijk.append([current_voxel_i, current_voxel_j, current_voxel_k])

                    except ValueError:  # empty grid
                        self.logger.error("Error at voxel ( %s, %s, %s ): It appears to have no common-face neighbors "
                                          "inside the image!", str(current_voxel_i), str(current_voxel_j),
                                          str(current_voxel_k))
                        return

                else:
                    out_volume.data[current_voxel_i, current_voxel_j, current_voxel_k] = labels_nomask[label_index]

        if out_vol_path == None:
            out_vol_path = in_vol_path

        IOUtils.write_volume(out_vol_path, out_volume)

        # Save the output indexes that survived masking
        out_ijk = numpy.vstack(out_ijk)
        filepath = os.path.splitext(out_vol_path)[0]
        numpy.save(filepath + "-idx.npy", out_ijk)
        numpy.savetxt(filepath + "-idx.txt", out_ijk, fmt='%d')

    def label_with_dilation(self, to_label_nii_fname, dilated_nii_fname, out_nii_fname):
        """
        Labels a volume using its labeled dilation. The dilated volume is labeled using scipy.ndimage.label function.
        :param to_label_nii_fname: usually a CT-mask.nii.gz
        :param dilated_nii_fname: dilated version of the to_label_nii_fname volume
        """

        # TODO could make dilation with ndimage also.
        mask = IOUtils.read_volume(to_label_nii_fname)
        dil_mask = IOUtils.read_volume(dilated_nii_fname)

        lab, n = scipy.ndimage.label(dil_mask.data)
        mask.data *= lab
        self.logger.info('%d objects found when labeling the dilated volume.', n)

        IOUtils.write_volume(out_nii_fname, mask)

    def _label_config(self, aparc):
        unique_data = numpy.unique(aparc.data)
        unique_data_map = numpy.r_[:unique_data.max() + 1]
        unique_data_map[unique_data] = numpy.r_[:unique_data.size]
        aparc.data = unique_data_map[aparc.data]
        return aparc

    def simple_label_config(self, in_aparc_path, out_volume_path):
        """
        Relabel volume to have contiguous values like Mrtrix' labelconfig.
        :param in_aparc_path: volume voxel value is the index of the region it belongs to.
        :return: writes the labeled volume to out_volume_path.
        """

        aparc = IOUtils.read_volume(in_aparc_path)
        aparc = self._label_config(aparc)
        IOUtils.write_volume(out_volume_path, aparc)

    def _label_volume(self, tdi_volume, lo=0.5):
        mask = tdi_volume.data > lo
        tdi_volume.data[~mask] = 0
        tdi_volume.data[mask] = numpy.r_[1:mask.sum() + 1]
        return tdi_volume

    def label_vol_from_tdi(self, tdi_volume_path, out_volume_path, lo=0.5):
        """
        Creates a mask of the voxels with tract ends > lo and any other voxels become 0.
        Labels each voxel different from 0 with integer labels starting from 1.
        :param tdi_volume_path: volume voxel value is the sum of tract ends. Voxel without tract ends has value 0.
        :param lo: tract ends threshold used for masking.
        :return: writes labeled volume to :ut_volume_path.
        """

        nii_volume = IOUtils.read_volume(tdi_volume_path)
        tdi_volume = self._label_volume(nii_volume, lo)
        IOUtils.write_volume(out_volume_path, tdi_volume)

    def remove_zero_connectivity_nodes(self, node_volume_path, connectivity_matrix_path, tract_length_path=None):
        """
        It removes network nodes with zero connectivity from the volume and connectivity matrices.
        The zero connectivity nodes will be labeled with 0 in the volume and the remaining labels will be updated.
        The connectivity matrices will be symmetric.
        :param node_volume_path: tdi_lbl.nii volume path
        :param connectivity_matrix_path: .csv file, output of Mrtrix3 tck2connectome
        :param tract_length_path: optional .csv tract lengths matrix
        :return: overwrites the input volume and matrices with the processed ones. Also saves matrices as .npy.
        """

        node_volume = IOUtils.read_volume(node_volume_path)

        connectivity = numpy.array(numpy.genfromtxt(connectivity_matrix_path, dtype='int64'))
        connectivity = connectivity + connectivity.T
        connectivity_row_sum = numpy.sum(connectivity, axis=0)

        nodes_to_keep_indices = connectivity_row_sum > 0
        connectivity = connectivity[nodes_to_keep_indices, :][:, nodes_to_keep_indices]

        numpy.save(os.path.splitext(connectivity_matrix_path)[0] + NPY_EXTENSION, connectivity)
        numpy.savetxt(connectivity_matrix_path, connectivity, fmt='%1d')

        if os.path.exists(str(tract_length_path)):
            connectivity = numpy.array(numpy.genfromtxt(tract_length_path, dtype='int64'))
            connectivity = connectivity[nodes_to_keep_indices, :][:, nodes_to_keep_indices]

            numpy.save(os.path.splitext(tract_length_path)[0] + NPY_EXTENSION, connectivity)
            numpy.savetxt(tract_length_path, connectivity, fmt='%1d')

        else:
            self.logger.warning("Path %s is not valid.", tract_length_path)

        nodes_to_remove_indices, = numpy.where(~nodes_to_keep_indices)
        nodes_to_remove_indices += 1

        for node_index in nodes_to_remove_indices:
            node_volume.data[node_volume.data == node_index] = 0

        node_volume.data[node_volume.data > 0] = numpy.r_[1:(connectivity.shape[0] + 1)]

        IOUtils.write_volume(node_volume_path, node_volume)


    def con_vox_in_ras(self,ref_vol_path):
        """
        This function reads a tdi_lbl volume and returns the voxels that correspond to connectome nodes,
        and their coordinates in ras space, simply by applying the affine transform of the volume
        :param ref_vol_path: the path to the tdi_lbl volume
        :return: vox and voxxyz,
                i.e., the labels (integers>=1) and the coordinates of the connnectome nodes-voxels, respectively
        """
        # Read the reference tdi_lbl volume:
        vollbl = IOUtils.read_volume(ref_vol_path)
        vox = vollbl.data.astype('i')
        # Get only the voxels that correspond to connectome nodes:
        voxijk, = numpy.where(vox.flatten() > 0)
        voxijk = numpy.unravel_index(voxijk, vollbl.dimensions)
        vox = vox[voxijk[0], voxijk[1], voxijk[2]]
        # ...and their coordinates in ras xyz space
        voxxzy = vollbl.affine_matrix.dot(numpy.c_[voxijk[0], voxijk[1], voxijk[2], numpy.ones(vox.shape[0])].T)[:3].T
        return vox, voxxzy
