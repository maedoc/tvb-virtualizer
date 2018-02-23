# -*- coding: utf-8 -*-

import glob
import os
import gdist
import numpy
import scipy
from tvb.recon.io.factory import IOUtils
from tvb.recon.logger import get_logger
from tvb.recon.algo.service.annotation import AnnotationService, DEFAULT_LUT
from tvb.recon.io.volume import VolumeIO
from tvb.recon.model.surface import Surface
from tvb.recon.model.annotation import Annotation
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components, shortest_path
from sklearn.metrics.pairwise import paired_distances
from scipy.spatial.distance import cdist
from copy import deepcopy
from .annotation import default_lut_path  # TODO into fs module


class SurfaceService(object):
    logger = get_logger(__name__)

    def __init__(self):
        self.annotation_service = AnnotationService()

    # #TODO: transfer the following two to some general services?:
    # def mask2index(self,mask):
    #     """
    #     Convert a mask to an array of indices
    #     :param mask:
    #     :return:
    #     """
    #     return numpy.where(mask)
    #
    # def index2mask(self,index):
    #     """
    #     Convert an array of indices to the corresponding mask
    #     :param index:
    #     :return:
    #     """
    #     index=numpy.unique(index)
    #     mask=numpy.zeros((len(index,))).astype('bool')
    #     mask[index]=True
    #     return mask

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

    def merge_surfaces(self, surfaces):
        """
        Merge several surfaces, and their region mappings.
        :return: the merge result surface and region mapping.
        """
        n_surfaces = len(surfaces)
        out_surface = Surface([], [])
        # TODO: how to deal with the metadata of merged surfaces, so that freesurfer.io can handle them, e.g., write them
        # i.e., we need to have a final unique version of the metadata, not a list of them, as I am doing here in the
        # commented code
        # out_surface_attributes=dict()
        # for attribute in ["vertices_coord_system", "generic_metadata", "vertices_metadata", "triangles_metadata"]:
        #     out_surface_attributes[attribute]=[]
        for i_srf in range(n_surfaces):
            out_surface.add_vertices_and_triangles(surfaces[i_srf].vertices,
                                                   surfaces[i_srf].triangles,
                                                   surfaces[i_srf].area_mask)
            if out_surface.get_main_metadata() is None:
                out_surface.set_main_metadata(surfaces[i_srf].get_main_metadata())
            if len(surfaces[i_srf].center_ras) == 0:
                pass
            elif len(out_surface.center_ras) == 0:
                out_surface.center_ras = surfaces[i_srf].center_ras
            elif numpy.any(out_surface.center_ras != surfaces[i_srf].center_ras):
                self.logger.warn("At least two surfaces have different -non empty- centers in RAS coordinates!")
            # #TODO: think about how to better merge these fields
            # for attribute in ["vertices_coord_system", "generic_metadata", "vertices_metadata", "triangles_metadata"]:
            #     out_surface_attributes[attribute].append(getattr(surfaces[i_srf],attribute))
            #     setattr(out_surface,attribute,out_surface_attributes[attribute])
        return out_surface

    def compute_gdist_mat(self, surf_name='pial', max_distance=40.0):
        max_distance = float(max_distance)  # in case passed from sys.argv
        for h in 'rl':
            subjects_dir = os.environ['SUBJECTS_DIR']
            subject = os.environ['SUBJECT']
            surf_path = '%s/%s/surf/%sh.%s' % (subjects_dir,
                                               subject, h, surf_name)
            surface = IOUtils.read_surface(surf_path, False)
            mat_path = '%s/%s/surf/%sh.%s.gdist.mat' % (
                subjects_dir, subject, h, surf_name)
            mat = gdist.local_gdist_matrix(
                surface.vertices, surface.triangles.astype('<i4'), max_distance=max_distance)
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
        # TODO: make sure that this returns a symmetric matrix!
        geodist = shortest_path(dist, method='auto', directed=False,
                                return_predecessors=False, unweighted=False, overwrite=False).astype('single')
        # Find the maximum non infinite geodesic distance:
        max_gdist = numpy.max(geodist, axis=None)
        assert numpy.isfinite(max_gdist)
        if norm is not None:
            geodist /= max_gdist
        # Convert them to normalized distances and return them
        return geodist

    def extract_subsurf(self, surface, verts_mask, output='surface'):
        """
        Extracts a sub-surface that contains only the masked vertices and the corresponding faces.
        An important step is to replace old vertices indexes of faces to the new ones.
        :param: surface: input surface object
        :param: verts_mask: mask of the sub-surface to be extracted
        :return: output surface object
        """

        verts_out = surface.vertices[verts_mask]
        triangles_mask = numpy.c_[verts_mask[surface.triangles[:, 0]],
                                  verts_mask[surface.triangles[:, 1]],
                                  verts_mask[surface.triangles[:, 2]]].all(axis=1)
        triangles_out = numpy.array(surface.triangles[triangles_mask, :])
        verts_out_inds, = numpy.where(verts_mask)
        for triang_idx in range(triangles_out.shape[0]):
            for vertex_idx in range(3):
                triangles_out[triang_idx, vertex_idx], = \
                    numpy.where(
                        triangles_out[triang_idx, vertex_idx] == verts_out_inds)
        if output == 'surface':
            out_surface = Surface(verts_out, triangles_out, area_mask=surface.area_mask[verts_out_inds],
                                  center_ras=surface.center_ras, vertices_coord_system=surface.vertices_coord_system,
                                  generic_metadata=surface.generic_metadata,
                                  vertices_metadata=surface.vertices_metadata,
                                  triangles_metadata=surface.triangles_metadata)
            return out_surface
        else:
            return (verts_out, triangles_out,
                    surface.area_mask[verts_out_inds])

    def compute_surface_area(self, surface, area_mask=None):
        """
            This function computes the surface area, after optionally applying a mask to choose a sub-surface
            :param: surface: input surface object
            :param area_mask: optional boolean mask (number of vertices x ) to overwrite the surface.area_mask
            :return: (sub)surface area, float
            """
        if area_mask is None:
            area_mask = surface.area_mask
        # Apply the mask in order to extract the sub-surface (vertices and
        # relevant triangles)
        (vertices, triangles) = self.extract_subsurf(
            surface, area_mask, output='verts_triangls')[:2]
        return numpy.sum(self.tri_area(vertices[triangles]))

    def vertex_connectivity(self, surface, mode="sparse",
                            metric=None, symmetric=False, verts_mask=None):
        """
        It computes a sparse matrix of the connectivity among the vertices of a surface.
        :param surface: input surface object
        :param mode: "sparse" by default or "2D"
        :param metric: None by default, could be "euclidean"
        :param symmetric: True for symmetric matrix output
        :param verts_mask: a mask to apply the method to a a sub-surface of the original surface
        :return: the computed matrix.
        """
        if verts_mask is not None:
            (vertices, triangles) = self.extract_subsurf(
                surface, verts_mask, output='verts_triangls')[:2]
        else:
            vertices = surface.vertices
            triangles = surface.triangles
        # Get all pairs of vertex indexes (i.e., edges) that appear in each
        # face (triangle)
        edges = numpy.r_[triangles[:, [0, 1]],
                         triangles[:, [1, 2]], triangles[:, [2, 0]]]
        # Remove repetitions
        edges = numpy.vstack(set(map(tuple, edges)))
        # Mark all existing pairs to 1
        n_v = vertices.shape[0]
        n_e = edges.shape[0]
        # For symmetric output...
        if symmetric:
            # ...create for the moment the "double" edges
            edges2 = numpy.r_[edges, edges[:, [1, 0]]]
        if metric is None:
            # For symmetric output...
            if symmetric:
                # ...remove repetitions of edges2
                edges = numpy.vstack(set(map(tuple, edges2)))
                n_e = edges.shape[0]
            con = csr_matrix(
                (numpy.ones((n_e,)), (edges[:, 0], edges[:, 1])), shape=(n_v, n_v))
            if mode != "sparse":
                # Create non-sparse matrix
                con = con.todense()
        else:
            d = paired_distances(vertices[edges[:, 0]], vertices[
                edges[:, 1]], metric)
            # For symmetric output...
            if symmetric:
                # double also d...
                d = numpy.r_[d, d]
                edges = edges2
            if mode == "sparse":
                # Create sparse matrix
                con = csr_matrix(
                    (d, (edges[:, 0], edges[:, 1])), shape=(n_v, n_v))
        return con

    # TODO: use surface instead of verts and faces?? Denis: not sure about
    # this!..
    def connected_surface_components(
            self, surface=None, connectivity=None, verts_mask=None):
        """
        This function returns all the different disconnected components of a surface, their number and their areas,
        after applying an optional boolean mask to exclude some subsurface from the whole computation.
        There should be at least one component returned, if the whole surface is connected.
        :param surface: input surface object
        :param connectivity: optionally an array or sparse matrix of structural connectivity constraints,
                            where True or 1 or entry>0 stands for the existing direct connections
                            among neighboring vertices (i.e., vertices of a common triangular face)
        :param verts_mask: optional boolean mask (number of vertices x ) for vertices to include to the input surface
        :return:
        """
        if (surface is None) and connectivity is None:
            print("Error: neither a surface, nor a connectivity matrix in the input!")
            return 0
        elif connectivity is None:
            n_verts = surface.vertices.shape[0]
            # Create the connectivity matrix, if not in the input:
            connectivity = self.vertex_connectivity(
                surface, verts_mask=verts_mask)
            if verts_mask is None:
                verts_mask = numpy.ones((n_verts,), dtype=bool)
        else:
            n_verts = connectivity.shape[0]
            if verts_mask is None:
                verts_mask = numpy.ones((n_verts,), dtype=bool)
            else:
                connectivity = connectivity[verts_mask, :][:, verts_mask]
        # Find all connected components of this surface
        (n_components, components_masked) = \
            connected_components(connectivity, directed=False,
                                 connection='weak', return_labels=True)
        comp_area = []
        if surface is not None:
            # For each component...
            for ic in range(n_components):
                i_comp_verts = components_masked == ic
                # ...compute the surface area, after applying any specified mask
                comp_area.append(self.compute_surface_area(surface,
                                                           mask=numpy.logical_and(i_comp_verts, surface.area_mask)))
        # Prepare final components' labels output:
        components = -numpy.ones((n_verts,)).astype('i')
        components[verts_mask] = components_masked
        return n_components, components, comp_area

    def aseg_surf_conc_annot(self, surf_path, out_surf_path, annot_path,
                             label_indices, lut_path=None):
        """
        Concatenate surfaces of one specific label of interest each, to create a single annotated surface.
        """

        lut_path = lut_path or default_lut_path()

        label_names, color_table = self.annotation_service.lut_to_annot_names_ctab(lut_path=lut_path,
                                                                                   labels=label_indices)
        label_indices = numpy.array(label_indices.split()).astype('i')

        #                  verts tri area_mask cras
        surfaces = []
        out_annotation = Annotation([], [], [])
        label_number = -1

        for label_index in label_indices:
            # TODO: This is hardcoded: /aseg-%06d here and also in pegasus dax generator
            this_surf_path = surf_path + "/aseg-%06d" % int(label_index)

            if os.path.exists(this_surf_path):
                ind_l, = numpy.where(label_indices == label_index)
                out_annotation.add_region_names_and_colors(
                    label_names[int(ind_l)],
                    color_table[ind_l, :])
                label_number += 1
                surfaces.append(IOUtils.read_surface(this_surf_path, False))
                out_annotation.add_region_mapping(
                    label_number * numpy.ones((surfaces[-1].n_vertices,), dtype='int64'))
        out_surface = self.merge_surfaces(surfaces)
        # out_annotation.regions_color_table = numpy.squeeze(numpy.array(out_annotation.regions_color_table).astype('i'))

        IOUtils.write_surface(out_surf_path, out_surface)
        IOUtils.write_annotation(annot_path, out_annotation)

    def __prepare_grid(self, vertex_neighbourhood):
        # Prepare grid if needed for possible use:
        if vertex_neighbourhood > 0:
            grid = numpy.meshgrid(list(range(-vertex_neighbourhood, vertex_neighbourhood + 1, 1)),
                                  list(range(-vertex_neighbourhood,
                                             vertex_neighbourhood + 1, 1)),
                                  list(range(-vertex_neighbourhood, vertex_neighbourhood + 1, 1)), indexing='ij')
            grid = numpy.c_[
                numpy.array(grid[0]).flatten(), numpy.array(grid[1]).flatten(), numpy.array(grid[2]).flatten()]
            n_grid = grid.shape[0]

            return grid, n_grid

    def sample_vol_on_surf(self, surf_path, vol_path, annot_path, out_surf_path,
                           cras_path, add_string='', vertex_neighbourhood=1,
                           add_lbl=[], lut_path=None):
        """
        Sample a volume of a specific label on a surface, by keeping only those surface vertices, the nearest voxel of
        which is of the given label (+ of possibly additional target labels, such as white matter).
        Allow optionally for vertices within a given voxel distance vn from the target voxels.
        """

        lut_path = lut_path or default_lut_path()

        # Read the inputs
        surface = IOUtils.read_surface(surf_path, False)

        annotation = IOUtils.read_annotation(annot_path)
        labels = self.annotation_service.annot_names_to_labels(annotation.region_names,
                                                               add_string=add_string, lut_path=lut_path)
        region_mapping_indexes = numpy.unique(annotation.region_mapping)

        volume_parser = VolumeIO()
        volume = volume_parser.read(vol_path)
        ras2vox_affine_matrix = numpy.linalg.inv(volume.affine_matrix)

        cras = numpy.loadtxt(cras_path)

        grid, n_grid = self.__prepare_grid(vertex_neighbourhood)

        # Initialize the output mask:
        verts_out_mask = numpy.repeat([False], surface.vertices.shape[0])
        for label_index in range(len(region_mapping_indexes)):

            self.logger.info("%s", add_string +
                             annotation.region_names[label_index])

            # Get the indexes of the vertices corresponding to this label:
            verts_indices_of_label, = numpy.where(
                annotation.region_mapping[:] == region_mapping_indexes[label_index])
            verts_indices_of_label_size = verts_indices_of_label.size
            if verts_indices_of_label_size == 0:
                continue

            # Add any additional labels
            all_labels = [labels[label_index]] + add_lbl

            # get the vertices for current label and add cras to take them to
            # scanner ras
            verts_of_label = surface.vertices[verts_indices_of_label, :]
            verts_of_label += numpy.repeat(numpy.expand_dims(
                cras, 1).T, verts_indices_of_label_size, axis=0)

            # Compute the nearest voxel coordinates using the affine transform
            ijk = numpy.round(
                ras2vox_affine_matrix.dot(numpy.c_[verts_of_label, numpy.ones(verts_indices_of_label_size)].T)[:3].T) \
                .astype('i')

            # Get the labels of these voxels:
            surf_vxls = volume.data[ijk[:, 0], ijk[:, 1], ijk[:, 2]]

            # Vertex mask to keep: those that correspond to voxels of one of
            # the target labels
            # surf_vxls==lbl if only one target label
            verts_keep, = numpy.where(numpy.in1d(surf_vxls, all_labels))
            verts_out_mask[verts_indices_of_label[verts_keep]] = True

            if vertex_neighbourhood > 0:
                # These are now the remaining indexes to be checked for
                # neighboring voxels
                verts_indices_of_label = numpy.delete(
                    verts_indices_of_label, verts_keep)
                ijk = numpy.delete(ijk, verts_keep, axis=0)

                for vertex_index in range(verts_indices_of_label.size):
                    # Generate the specific grid centered at the voxel ijk
                    ijk_grid = grid + \
                               numpy.tile(ijk[vertex_index, :], (n_grid, 1))

                    # Remove voxels outside the volume
                    indexes_within_limits = numpy.all([(ijk_grid[:, 0] >= 0), (ijk_grid[:, 0] < volume.dimensions[0]),
                                                       (ijk_grid[:, 1] >= 0), (ijk_grid[
                                                                               :, 1] < volume.dimensions[1]),
                                                       (ijk_grid[:, 2] >= 0), (ijk_grid[:, 2] < volume.dimensions[2])],
                                                      axis=0)
                    ijk_grid = ijk_grid[indexes_within_limits, :]
                    surf_vxls = volume.data[
                        ijk_grid[:, 0], ijk_grid[:, 1], ijk_grid[:, 2]]

                    # If any of the neighbors is of the target labels include
                    # the current vertex
                    # surf_vxls==lbl if only one target label
                    if numpy.any(numpy.in1d(surf_vxls, all_labels)):
                        verts_out_mask[
                            verts_indices_of_label[vertex_index]] = True

        # Vertex indexes and vertices to keep:
        verts_out_indices, = numpy.where(verts_out_mask)
        verts_out = surface.vertices[verts_out_indices]

        # TODO maybe: make sure that all voxels of this label correspond to at least one vertex.
        # Create a similar mask for faces by picking only triangles of which
        # all 3 vertices are included
        face_out_mask = numpy.c_[
            verts_out_mask[surface.triangles[:, 0]], verts_out_mask[surface.triangles[:, 1]], verts_out_mask[
                surface.triangles[:, 2]]].all(axis=1)
        faces_out = surface.triangles[face_out_mask]

        # The old vertices' indexes of faces have to be transformed to the new
        # vrtx_out_inds:
        for iF in range(faces_out.shape[0]):
            for vertex_index in range(3):
                faces_out[iF, vertex_index], = numpy.where(
                    faces_out[iF, vertex_index] == verts_out_indices)

        surface.vertices = verts_out
        surface.triangles = faces_out

        # Write the output surfaces and annotations to files. Also write files
        # with the indexes of vertices to keep.
        IOUtils.write_surface(out_surf_path, surface)

        annotation.set_region_mapping(
            annotation.get_region_mapping_by_indices([verts_out_indices]))
        IOUtils.write_annotation(out_surf_path + ".annot", annotation)

        numpy.save(out_surf_path + "-idx.npy", verts_out_indices)
        numpy.savetxt(out_surf_path + "-idx.txt", verts_out_indices, fmt='%d')

    # TODO: maybe create a new "connectome" service and transfer this function
    # there
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
            verts += numpy.repeat(numpy.expand_dims(cras,
                                                    1).T, verts.shape[0], axis=0)
        # TODO?: to use aparc+aseg to correspond vertices only to voxels of the same label
        # There would have to be a vertex->voxel of aparc+aseg of the same label -> voxel of tdi_lbl_in_T1 mapping
        # Maybe redundant  because we might be ending to the same voxel of tdi_lbl anyway...
        # Something to test/discuss...
        # Find for each vertex the closest voxel node in terms of euclidean
        # distance:
        v2n = numpy.argmin(cdist(verts, voxxzy, 'euclidean'), axis=1)
        # Assign to each vertex the integer identity of the nearest voxel node.
        v2n = vox[v2n]
        print("...surface component's vertices correspond to " +
              str(numpy.size(numpy.unique(v2n))) + " distinct voxel nodes")
        affinity = con[v2n - 1, :][:, v2n - 1]
        return affinity

    def compute_areas_for_regions(self, regions: list, surface: Surface, region_mapping: list) -> numpy.array:
        """Compute the areas of given regions"""

        region_surface_area = numpy.zeros(len(regions))
        avt = numpy.array(surface.get_vertex_triangles())
        # NOTE: Slightly overestimates as it counts overlapping border triangles,
        #       but, not really a problem provided triangle-size << region-size.
        for i, k in enumerate(regions):
            regs = list(map(set, avt[numpy.array(region_mapping) == k]))
            if len(regs) == 0:
                continue
            region_triangles = set.union(*regs)
            if region_triangles:
                region_surface_area[i] = surface.get_triangle_areas()[list(region_triangles)].sum()

        return region_surface_area

    def compute_orientations_for_regions(self, regions, surface, region_mapping) -> numpy.ndarray:
        """Compute the orientation of given regions from vertex_normals and region mapping"""

        average_orientation = numpy.zeros((len(regions), 3))
        vertex_normals = surface.vertex_normals()
        # Average orientation of the region
        for i, k in enumerate(regions):
            orient = vertex_normals[numpy.array(region_mapping) == k, :]
            if orient.shape[0] > 0:
                avg_orient = numpy.mean(orient, axis=0)
                average_orientation[i, :] = avg_orient / numpy.sqrt(numpy.sum(avg_orient ** 2))

        return average_orientation

    def compute_centers_for_regions(self, regions, surface, region_mapping) -> numpy.ndarray:
        region_centers = numpy.zeros((len(regions), 3))
        for i, k in enumerate(regions):
            vert = surface.vertices[numpy.array(region_mapping) == k, :]
            if vert.shape[0] > 0:
                region_centers[i, :] = numpy.mean(vert, axis=0)

        return region_centers
