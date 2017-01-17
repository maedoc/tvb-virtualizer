# -*- coding: utf-8 -*-

import glob
import os
import gdist
import numpy
import scipy
from bnm.recon.io.factory import IOUtils
from bnm.recon.logger import get_logger
from bnm.recon.algo.service.annotation import AnnotationService
from bnm.recon.io.volume import VolumeIO
from bnm.recon.model.surface import Surface
from bnm.recon.model.annotation import Annotation
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from sklearn.metrics.pairwise import paired_distances
from scipy.spatial.distance import cdist

class SurfaceService(object):
    logger = get_logger(__name__)

    def __init__(self):
        self.annotation_service = AnnotationService()

    def tri_area(self, tri):
        i, j, k = numpy.transpose(tri, (1, 0, 2))
        ij = j - i
        ik = k - i
        return numpy.sqrt(numpy.sum(numpy.cross(ij, ik) ** 2, axis=1)) / 2.0

    def convert_fs_to_brain_visa(self, in_surf_path):
        surface = IOUtils.read_surface(in_surf_path, False)
        IOUtils.write_surface(in_surf_path + '.tri', surface)

    def convert_bem_to_tri(self, surfaces_directory_path):
        surfs_glob = '%s/*_surface-low' % (surfaces_directory_path)
        for surf_name in glob.glob(surfs_glob):
            self.convert_fs_to_brain_visa(surf_name)

    def merge_lh_rh(self, lh_surface, rh_surface, left_region_mapping, right_region_mapping):
        """
        Merge left and right hemisphere surfaces, and their region mappings.
        :return: the merge result surface and region mapping.
        """

        out_surface = Surface([], [], [], None)
        out_surface.vertices = numpy.r_[lh_surface.vertices, rh_surface.vertices]
        out_surface.triangles = numpy.r_[lh_surface.triangles, rh_surface.triangles + lh_surface.vertices.max()]
        out_region_mapping = numpy.r_[left_region_mapping, right_region_mapping + lh_surface.triangles.max()]
        return out_surface, out_region_mapping

    def compute_gdist_mat(self, surf_name='pial', max_distance=40.0):
        max_distance = float(max_distance)  # in case passed from sys.argv
        for h in 'rl':
            subjects_dir = os.environ['SUBJECTS_DIR']
            subject = os.environ['SUBJECT']
            surf_path = '%s/%s/surf/%sh.%s' % (subjects_dir, subject, h, surf_name)
            surface = IOUtils.read_surface(surf_path, False)
            mat_path = '%s/%s/surf/%sh.%s.gdist.mat' % (subjects_dir, subject, h, surf_name)
            mat = gdist.local_gdist_matrix(surface.vertices, surface.triangles.astype('<i4'), max_distance=max_distance)
            scipy.io.savemat(mat_path, {'gdist': mat})

    # TODO: maybe create a new "connectome" service and transfer this function there
    # TODO: add more normalizations modes
    def compute_geodesic_dist_affinity(self, dist, norm=None):
        """
        This function calculates geodesic distances among nodes of a mesh,
        starting from the array of the distances between directly connected nodes.
        Optionally, normalization with the maximum geodesic distances is performed.
        Infinite distances (corresponding to disconnected components of the mesh, are not allowed)
        :param dist: a dense array of distances between directly connected nodes of a mesh/network
        :param norm: a flag to be currently used for optional normalization with the maximum geodesic distance

        :return:
        """
        #TODO: make sure that this returns a symmetric matrix!
        geodist = shortest_path(dist, method='auto', directed=False,
                                return_predecessors=False, unweighted=False, overwrite=False).astype('single')
        # Find the maximum non infinite geodesic distance:
        max_gdist = numpy.max(geodist, axis=None)
        assert numpy.isfinite(max_gdist)
        if norm is not None:
            geodist /= max_gdist
        # Convert them to normalized distances and return them
        return geodist

    # TODO: instead of verts and faces we should use surface. Denis: not sure about this!..
    def extract_subsurf(self, verts, faces, verts_mask):
        """
        Extracts a sub-surface that contains only the masked vertices and the corresponding faces.
        An important step is to replace old vertices indexes of faces to the new ones.
        :param verts_mask: vertices to keep mask.
        :return: vertices and faces of the sub-surface.
        """

        verts_out = verts[verts_mask, :]
        face_mask = numpy.c_[verts_mask[faces[:, 0]], verts_mask[faces[:, 1]], verts_mask[faces[:, 2]]].all(axis=1)
        faces_out = faces[face_mask]
        verts_out_inds, = numpy.where(verts_mask)

        for face_idx in xrange(faces_out.shape[0]):
            for vertex_idx in xrange(3):
                faces_out[face_idx, vertex_idx], = numpy.where(faces_out[face_idx, vertex_idx] == verts_out_inds)

        return verts_out, faces_out

    # TODO: use surface instead of verts and faces?? Denis: not sure about this!..
    def compute_surface_area(self, verts, faces, mask=None):
        """
            This function computes the surface area, after optionally applying a mask to choose a sub-surface
            :param verts: vertices' coordinates array (number of vertices x 3)
            :param faces: faces' array, integers>=0 (number of faces x 3)
            :param mask: optional boolean mask (number of vertices x )
            :return: (sub)surface area, float
            """
        if mask is not None:
            # Apply the optional mask in order to extract the sub-surface (vertices and relevant triangles)
            (v, f) = self.extract_subsurf(verts, faces, mask)
        return numpy.sum(self.tri_area(verts[faces]))

    # TODO: use surface instead of verts and faces?? Denis: not sure about this!..
    def vertex_connectivity(self, verts, faces, mode="sparse", metric=None):
        """
        It computes a sparse matrix of the connectivity among the vertices of a surface.
        :param verts: vertices' coordinates array (number of vertices x 3)
        :param faces: faces' array, integers>=0 (number of faces x 3)
        :param mode: "sparse" by default or "2D"
        :param metric: None by default, could be "euclidean"
        :return: the computed matrix.
        """
        # Get all pairs of vertex indexes (i.e., edges) that appear in each face (triangle)
        edges = numpy.r_[faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]]
        # Remove repetitions
        edges = numpy.vstack(set(map(tuple, faces)))
        # Mark all existing pairs to 1
        n_v = verts.shape[0]
        n_e = edges.shape[0]
        if metric is None:
            con = csr_matrix((numpy.ones((n_e,)), (edges[:, 0], edges[:, 1])), shape=(n_v, n_v))
            if mode != "sparse":
                # Create non-sparse matrix
                con = con.todense()
        else:
            d = paired_distances(verts[edges[:, 0]], verts[edges[:, 1]], metric)
            if mode == "sparse":
                # Create sparse matrix
                con = csr_matrix((d, (edges[:, 0], edges[:, 1])), shape=(n_v, n_v))
        return con

    # TODO: use surface instead of verts and faces?? Denis: not sure about this!..
    def connected_surface_components(self, verts, faces, connectivity=None, mask=None):
        """
        This function returns all the different disconnected components of a surface, their number and their areas,
        after applying an optional boolean mask to exclude some subsurface from the area calculation.
        There should be at least one component returned, if the whole surface is connected.
        :param verts: vertices' coordinates array (number of vertices x 3)
        :param faces: faces' array, integers>=0 (number of faces x 3)
        :param connectivity: optionally an array or sparse matrix of structural connectivity constraints,
                            where True or 1 or entry>0 stands for the existing direct connections
                            among neighboring vertices (i.e., vertices of a common triangular face)
        :param mask: optional boolean mask (number of vertices x )
        :return:
        """
        #Create the connectivity matrix, if not in the input:
        if connectivity is None:
           connectivity=self.vertex_connectivity(verts, faces)
        # Find all connected components of this surface
        (n_components, components) = \
            connected_components(connectivity, directed=False, connection='weak', return_labels=True)
        # Check out if there is a mask for the vertices to be included in the area calculation
        if mask is None:
            mask = numpy.ones(components.shape, dtype=bool)
        comp_area = []
        # For each component...
        for ic in range(n_components):
            i_comp_verts = components == ic
            # ...compute the surface area, after applying any specified mask
            comp_area.append(self.compute_surface_area(verts, faces, mask=numpy.logical_and(i_comp_verts, mask[i_comp_verts])))
        return n_components, components, comp_area


    def aseg_surf_conc_annot(self, surf_path, out_surf_path, annot_path, label_indices,
                             lut_path=os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt')):
        """
        Concatenate surfaces of specific labels to create a single annotated surface.
        """

        label_names, color_table = self.annotation_service.lut_to_annot_names_ctab(lut_path=lut_path,
                                                                                   labels=label_indices)
        label_indices = numpy.array(label_indices.split()).astype('i')

        out_surface = Surface([], [], [], None)
        out_annotation = Annotation([], None, [])
        label_number = -1
        verts_number = 0

        for label_index in label_indices:
            this_surf_path = surf_path + "-%06d" % int(label_index)

            if os.path.exists(this_surf_path):
                ind_l, = numpy.where(label_indices == label_index)
                out_annotation.add_region_names_and_colors(label_names[ind_l], color_table[ind_l, :])
                label_number += 1
                surface = IOUtils.read_surface(this_surf_path, False)
                out_surface.set_main_metadata(surface.get_main_metadata())
                faces = surface.triangles + verts_number  # Update vertices indexes
                verts_number += surface.vertices.shape[0]
                out_surface.add_vertices_and_triangles(surface.vertices, faces)
                out_annotation.add_region_mapping(
                    label_number * numpy.ones((surface.vertices.shape[0],), dtype='int64'))

        out_annotation.regions_color_table = numpy.squeeze(numpy.array(out_annotation.regions_color_table).astype('i'))
        out_surface.stack_vertices_and_triangles()
        out_annotation.stack_region_mapping()

        IOUtils.write_surface(out_surf_path, out_surface)
        IOUtils.write_annotation(annot_path, out_annotation)



    def __prepare_grid(self, vertex_neighbourhood):
        # Prepare grid if needed for possible use:
        if vertex_neighbourhood > 0:
            grid = numpy.meshgrid(range(-vertex_neighbourhood, vertex_neighbourhood + 1, 1),
                                  range(-vertex_neighbourhood, vertex_neighbourhood + 1, 1),
                                  range(-vertex_neighbourhood, vertex_neighbourhood + 1, 1), indexing='ij')
            grid = numpy.c_[
                numpy.array(grid[0]).flatten(), numpy.array(grid[1]).flatten(), numpy.array(grid[2]).flatten()]
            n_grid = grid.shape[0]

            return grid, n_grid


    def sample_vol_on_surf(self, surf_path, vol_path, annot_path, out_surf_path, cras_path, ctx=None,
                           vertex_neighbourhood=1, add_lbl=[],
                           lut_path=os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt')):
        """
        Sample a volume of a specific label on a surface, by keeping only those surface vertices, the nearest voxel of
        which is of the given label (+ of possibly additional target labels, such as white matter).
        Allow optionally for vertices within a given voxel distance vn from the target voxels.
        """

        # Read the inputs
        surface = IOUtils.read_surface(surf_path, False)

        annotation = IOUtils.read_annotation(annot_path)
        labels = self.annotation_service.annot_names_to_labels(annotation.region_names, ctx, lut_path)

        volume_parser = VolumeIO()
        volume = volume_parser.read(vol_path)
        ras2vox_affine_matrix = numpy.linalg.inv(volume.affine_matrix)

        cras = numpy.loadtxt(cras_path)

        grid, n_grid = self.__prepare_grid(vertex_neighbourhood)

        # Initialize the output mask:
        verts_out_mask = numpy.repeat([False], surface.vertices.shape[0])

        for label_index in xrange(len(labels)):
            if isinstance(ctx, basestring):
                self.logger.info("ctx-%s-%s", ctx, annotation.region_names[label_index])
            else:
                self.logger.info("%s", annotation.region_names[label_index])

            # Add any additional labels
            all_labels = [labels[label_index]] + add_lbl

            # Get the indexes of the vertices corresponding to this label:
            verts_indices_of_label, = numpy.where(annotation.region_mapping[:] == label_index)
            verts_indices_of_label_size = verts_indices_of_label.size
            if verts_indices_of_label_size == 0:
                continue

            # get the vertices for current label and add cras to take them to scanner ras
            verts_of_label = surface.vertices[verts_indices_of_label, :]
            verts_of_label += numpy.repeat(numpy.expand_dims(cras, 1).T, verts_indices_of_label_size, axis=0)

            # Compute the nearest voxel coordinates using the affine transform
            ijk = numpy.round(
                ras2vox_affine_matrix.dot(numpy.c_[verts_of_label, numpy.ones(verts_indices_of_label_size)].T)[:3].T) \
                .astype('i')

            # Get the labels of these voxels:
            surf_vxls = volume.data[ijk[:, 0], ijk[:, 1], ijk[:, 2]]

            # Vertex mask to keep: those that correspond to voxels of one of the target labels
            verts_keep, = numpy.where(numpy.in1d(surf_vxls, all_labels))  # surf_vxls==lbl if only one target label
            verts_out_mask[verts_indices_of_label[verts_keep]] = True

            if vertex_neighbourhood > 0:
                # These are now the remaining indexes to be checked for neighboring voxels
                verts_indices_of_label = numpy.delete(verts_indices_of_label, verts_keep)
                ijk = numpy.delete(ijk, verts_keep, axis=0)

                for vertex_index in xrange(verts_indices_of_label.size):
                    # Generate the specific grid centered at the voxel ijk
                    ijk_grid = grid + numpy.tile(ijk[vertex_index, :], (n_grid, 1))

                    # Remove voxels outside the volume
                    indexes_within_limits = numpy.all([(ijk_grid[:, 0] >= 0), (ijk_grid[:, 0] < volume.dimensions[0]),
                                                       (ijk_grid[:, 1] >= 0), (ijk_grid[:, 1] < volume.dimensions[1]),
                                                       (ijk_grid[:, 2] >= 0), (ijk_grid[:, 2] < volume.dimensions[2])],
                                                      axis=0)
                    ijk_grid = ijk_grid[indexes_within_limits, :]
                    surf_vxls = volume.data[ijk_grid[:, 0], ijk_grid[:, 1], ijk_grid[:, 2]]

                    # If any of the neighbors is of the target labels include the current vertex
                    if numpy.any(numpy.in1d(surf_vxls, all_labels)):  # surf_vxls==lbl if only one target label
                        verts_out_mask[verts_indices_of_label[vertex_index]] = True

            # Vertex indexes and vertices to keep:
            verts_out_indices, = numpy.where(verts_out_mask)
            verts_out = surface.vertices[verts_out_indices]

            # TODO maybe: make sure that all voxels of this label correspond to at least one vertex.
            # Create a similar mask for faces by picking only triangles of which all 3 vertices are included
            face_out_mask = numpy.c_[
                verts_out_mask[surface.triangles[:, 0]], verts_out_mask[surface.triangles[:, 1]], verts_out_mask[
                    surface.triangles[:, 2]]].all(axis=1)
            faces_out = surface.triangles[face_out_mask]

            # The old vertices' indexes of faces have to be transformed to the new vrtx_out_inds:
            for iF in xrange(faces_out.shape[0]):
                for vertex_index in xrange(3):
                    faces_out[iF, vertex_index], = numpy.where(faces_out[iF, vertex_index] == verts_out_indices)

            surface.vertices = verts_out
            surface.triangles = faces_out

            # Write the output surfaces and annotations to files. Also write files with the indexes of vertices to keep.
            IOUtils.write_surface(out_surf_path, surface)

            annotation.set_region_mapping(annotation.get_region_mapping_by_indices([verts_out_indices]))
            IOUtils.write_annotation(out_surf_path + ".annot", annotation)

            numpy.save(out_surf_path + "-idx.npy", verts_out_indices)
            numpy.savetxt(out_surf_path + "-idx.txt", verts_out_indices, fmt='%d')


    # TODO: maybe create a new "connectome" service and transfer this function there
    def compute_consim_affinity(self, verts, vox, voxxzy, con, cras=None):
        """
        This function creates a connectome affinity matrix among vertices,
        starting from an affinity matrix among voxels,
        by assignment from the nearest neighboring voxel to the respective vertex.
        :param verts: vertices' coordinates array (number of vertices x 3)
        :param vox: labels of connectome nodes-voxels (integers>=1)
        :param voxxzy: coordinates of the connectome nodes-voxels in ras space
        :param con: connectivity affinity matrix
        :param cras: center ras point to be optionally added to the vertices coordinates
                    (being probably in freesurfer tk-ras or surface ras coordinates) to align with the volume voxels
        :return: the affinity matrix among vertices
        """
        # Add the cras to take them to scanner ras coordinates, if necessary:
        if cras is not None:
            verts += numpy.repeat(numpy.expand_dims(cras, 1).T, verts.shape[0], axis=0)
        # TODO?: to use aparc+aseg to correspond vertices only to voxels of the same label
        # There would have to be a vertex->voxel of aparc+aseg of the same label -> voxel of tdi_lbl_in_T1 mapping
        # Maybe redundant  because we might be ending to the same voxel of tdi_lbl anyway...
        # Something to test/discuss...
        # Find for each vertex the closest voxel node in terms of euclidean distance:
        v2n = numpy.argmin(cdist(verts, voxxzy, 'euclidean'), axis=1)
        # Assign to each vertex the integer identity of the nearest voxel node.
        v2n = vox[v2n]
        print "Surface component's vertices correspond to " + \
              str(numpy.size(numpy.unique(v2n))) + " distinct voxel nodes"
        affinity = con[v2n - 1, :][:, v2n - 1]
        return affinity
