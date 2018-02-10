# -*- coding: utf-8 -*-

import os
import numpy
import scipy
from scipy.spatial.distance import pdist, cdist, squareform
from sklearn.cluster import AgglomerativeClustering
from ...io.factory import IOUtils
from ...algo.service.annotation import AnnotationService, DEFAULT_LUT
from ...algo.service.surface import SurfaceService
from ...algo.service.volume import VolumeService
from ...model.annotation import Annotation


# TODO should be parameters to relevant methods
MIN_PARC_AREA_RATIO = 0.5
MAX_PARC_AREA_RATIO = 1.5


# TODO these should be broken out into smaller classes and functions
class SubparcellationService(object):

    def __init__(self):
        self.annotation_service = AnnotationService()
        self.surface_service = SurfaceService()
        self.volume_service = VolumeService()

    def make_subparc(self, surface, annotation, trg_area=100.0):
        # TODO subcort subparc with geodesic on bounding gmwmi
        # TODO normalize fiber counts by relevant gmwmi area

        vertex_face_mapping = [set([]) for _ in surface.vertices]
        for i, face in enumerate(surface.triangles):
            for j in face:
                vertex_face_mapping[j].add(i)
        vertex_face_mapping = numpy.array(vertex_face_mapping)

        # Make new annotation
        new_annotation = Annotation([], [], [])
        new_annotation.region_mapping = annotation.region_mapping.copy()

        next_aval = 1
        for region_names_index in numpy.unique(annotation.region_mapping):
            name = annotation.region_names[region_names_index]
            mask = annotation.region_mapping == region_names_index

            # "unknown", just skip
            if region_names_index == -1:
                new_annotation.region_mapping[mask] = 0
                new_annotation.region_names.append(name)
                continue

            # indices of faces in ROI
            rfi = set([])
            for face_set in vertex_face_mapping[mask]:
                rfi.update(face_set)
            rfi = numpy.array(list(rfi))

            # empty roi
            if rfi.size == 0:
                continue

            # compute area of faces in roi
            roi_area = numpy.sum(self.surface_service.tri_area(
                surface.vertices[surface.triangles[rfi]]))

            # choose k for desired roi area
            k = int(roi_area / trg_area) + 1
            assert k >= 1

            # cluster centered vertices
            v_roi = surface.vertices[mask]
            _, i_lab = scipy.cluster.vq.kmeans2(v_roi - v_roi.mean(axis=0), k)

            # update annot
            new_annotation.region_mapping[mask] = next_aval + i_lab
            next_aval += k
            new_annotation.region_names += ['%s-%d' %
                                            (name.decode('ascii'), j) for j in range(k)]

        # create random colored ctab
        new_annotation.regions_color_table = numpy.random.randint(
            255, size=(len(new_annotation.region_names), 5))
        r, g, b, _, _ = new_annotation.regions_color_table.T
        new_annotation.regions_color_table[:, 3] = 0
        new_annotation.regions_color_table[
            :, 4] = self.annotation_service.rgb_to_fs_magic_number([r, g, b])

        return new_annotation

    def subparc_files(self, surf_path, annot_path,
                      out_annot_parc_name, trg_area):
        trg_area = float(trg_area)
        surface = IOUtils.read_surface(surf_path, False)
        annotation = IOUtils.read_annotation(annot_path)
        new_annotation = self.make_subparc(
            surface, annotation, trg_area=trg_area)
        IOUtils.write_annotation(out_annot_parc_name, new_annotation)

    # TODO: maybe create a new "connectome" service and transfer this function
    # there
    def node_connectivity_metric(
            self, con_mat_path, metric="cosine", out_consim_path=None):
        """
        This function computes a connectivity distance matrix starting from a connectivity matrix,
        i.e., a square matrix where the i,j entry denotes the dissimilarity of the connectivity profiles of the
        i and j nodes of the network
        :param con_mat_path: path to connectivity matrix file
        :param metric: distance/dissimilarity metric, default "cosine distance"
        :param out_consim_path: output path for the connectivity matrix to be optionally saved
        :return: the connectivity distance matrix
        """
        con = numpy.load(con_mat_path)
        # Calculate distance metric
        con = squareform(pdist(con, metric=metric))
        if out_consim_path is not None:
            numpy.save(out_consim_path, con)
        return con

    def divisive_clustering(self, distance, connectivity=None, surface=None):
        """
        This function splits a set a points to two clusters using a distance matrix,
        and optionally a structural connectivity constraint.
        It takes care to produce as evenly sized clusters by assigning in turn points to one after the other,
        as long as there are points that are closer to the respective cluster than the other.
        Cluster size is computed either as surface area, or number of points.
        :param distance: a distance (affinity) matrix of n_points x n_points, to be used for clustering
        :param connectivity: an optional structural connectivity constraint matrix of 1s (True) and 0s (False),
                            for the directly (dis)connected (neighboring) points, respectively
        :param surface: an optional surface object
        :return: clusters: a vector assigning all points to 0 (cluster 1) or 1 (cluster 2)
        """
        # Initialize clusters' indexes to -1, signifying points still remaining
        # to be clustered:
        n_points = distance.shape[0]
        clusters = -numpy.ones((n_points,)).astype('i')
        # Cluster areas'list
        clusters_size = [0.0, 0.0]
        # Deterministic initialization: find two points that maximize their mutual distance,
        # and are, optionally, well connected:
        #...Find the maximum distance...
        max_dist = numpy.max(distance)
        #...and all pairs of points that of that distance:
        (c1, c2) = numpy.where(distance == max_dist)
        if connectivity is None:
            #...assign the first pair of points as first points to each cluster:
            clusters[c1[0]] = 0
            clusters[c2[0]] = 1
        else:
            connectivity = connectivity.todense()
            #...compute the total connectivity of each pair of points to all other points:
            tot_con = []
            for ic in range(len(c1)):
                tot_con.append(
                    numpy.sum(connectivity[c1[ic], :] + connectivity[c2[ic], :]))
            #...find the first pair that maximizes total connectivity as well...
            con_max_id = numpy.argmax(tot_con)
            #...and assign it as first points to each cluster:
            clusters[c1[con_max_id]] = 0
            clusters[c2[con_max_id]] = 1
        # While there are remaining points:
        n_remaining = n_points - 2
        while n_remaining > 0:
            # Get the index of the smaller cluster to start with:
            ics = numpy.argsort(clusters_size)
            # Calculate the average distance of all points to the bigger cluster minus the one to the smaller cluster...
            #...and sort them in decreasing order
            points_left = clusters == -1
            mean_dist = numpy.mean( distance[points_left, :][:, clusters == ics[1]], axis=1) - \
                numpy.mean(distance[points_left, :][
                           :, clusters == ics[0]], axis=1)
            sort_dist = numpy.sort(mean_dist)[::-1].tolist()
            # The desirable sign for the clustering criterion
            sign = 1
            # Keep looping while True
            loop = True
            # Element to pop from the sort_dist list, either 0 for first, or -1
            # for last element
            pop = 0
            # Index of the current cluster
            ic = ics[0]
            # Flag for having dealt with current cluster
            cluster_done = False
            n_assigned = [0, 0]
            # While loop=True and there are still elements in the sort_dist
            # list:
            while loop and len(sort_dist) > 0:
                # Get either the first (for the smallest cluster) or the last
                # (for the bigger cluster) element:
                curr_dist = sort_dist.pop(pop)
                # If the distance is positive (for the smallest cluster) or
                # negative (for the bigger cluster)...
                if curr_dist * sign >= 0.0:
                    #...get the points that are equal to that distance...
                    curr_points, = numpy.where(mean_dist == curr_dist)
                    # ...and assign them to the current cluster...
                    clusters[curr_points] = ic
                    # ...signaling that at least one point has been assigned...
                    cluster_done = True
                    n_assigned[ic] += len(curr_points)
                    #...if the surface is in the input and structural constraints are present...
                    if (surface is not None) and (connectivity is not None):
                        # Find how many connnected components are now in this
                        # cluster:
                        (n_components, components, comp_areas) = \
                            self.surface_service.connected_surface_components(surface=surface,
                                                                              connectivity=connectivity,
                                                                              verts_mask=clusters == ic)

                        # If there are more than one components,
                        if n_components > 1:
                            # we need to remove all but the main and larger component:
                            #...find the component labels,
                            comp_labels = numpy.unique(components)
                            #...except for the masked ones (-1), i.e., those that do not belong to this cluster
                            comp_labels = comp_labels[
                                comp_labels > -1].tolist()
                            #...find the main and larger component:
                            comp_max = numpy.argmax(comp_areas)
                            #...and remove it from the list of components to remove
                            comp_labels.remove(comp_max)
                            #...find the points of the components to remove
                            remove_points = numpy.where(
                                numpy.in1d(components, comp_labels))
                            #...remove them from this cluster...
                            clusters[remove_points] = -1
                            #...reduce accordingly the assignment counter
                            n_assigned[ic] -= len(remove_points)
                            #...if we removed exactly the points we have just added and no changes
                            # has been made to the cluster
                            if numpy.all(numpy.sort(curr_points) ==
                                         numpy.sort(remove_points)):
                                #...signal so...
                                cluster_done = False
                else:
                    # if the distance is negative (for the smallest cluster) or positive (for the biggest cluster)...
                    #... there are no available points to assign to this cluster...
                    cluster_done = True
                # If we are done with this cluster...
                if cluster_done == True:
                    #...compute its new area if there were any new points assigned or removed...
                    if n_assigned[ic] != 0:
                        if surface is not None:
                            clusters_size[ic] = self.surface_service.compute_surface_area(surface,
                                                                                          numpy.logical_and(surface.area_mask, clusters == ic))
                        else:
                            clusters_size[ic] = numpy.sum(clusters == ic)
                    #...if this was the first (smallest) cluster, move to the next one...
                    if ic == ics[0]:
                        #...change the sign...
                        sign = -1
                        #...start popping from the end of the list...
                        pop = -1
                        #...change the index of the cluster...
                        ic = ics[1]
                        #...and reset the cluster_done flag...
                        cluster_done = False
                    else:
                        #...else, we are done with looping
                        loop = False
                #...else, we just continue by popping the next element of the list, for the same cluster...
            # In the rare case that there was no assignment to any of the two clusters,
            # although there are still available points (this might happen only if there are connectivity constraints)
            # TODO: through an exception if this happens without the respective connectivity constraints,
            # i.e., wihtout having points that are closer to one cluster, but
            # not connected to it.
            if numpy.all(n_assigned == 0):
                if connectivity is None:
                    print("ERROR: 0 assignement although there are no "
                          "connectivity constraints")
                    return clusters
                #...for each cluster
                for ic in ics:
                    # Calculate the sum of connectivity of each of the cluster
                    # points to each one of the remaining points,
                    remaining_points, = numpy.where(clusters == -1)
                    sum_connectivity = numpy.sum(connectivity[clusters == ic, :][
                                                 :, remaining_points], axis=0)
                    #...and assign the maximally connected point to the cluster, if it is connected (>0)
                    max_connectivity = numpy.argmax(sum_connectivity)
                    if sum_connectivity[max_connectivity] > 0:
                        clusters[remaining_points[max_connectivity]] = ic
                        n_assigned[ic] = 1
            # If there is still no assignment, meaning that these points are
            # fully disconnected, through an error:
            if numpy.all(n_assigned == 0):
                print("ERROR: fully disconnected points")
                return clusters
            # Update the stopping criterion
            n_remaining = numpy.sum(clusters == -1)
        return clusters

    def agglomerative_clustering(
            self, distance, n_clusters=2, connectivity=None):
        """
        This function uses agglomerative hierarchical clustering to cluster points according to the distance matrix,
        and optionally a structural connectivity constraint.
        :param distance: a distance (affinity) matrix of n_points x n_points, to be used for clustering
        :param n_clusters: desired number of clusters
        :param connectivity: an optional structural connectivity constraint matrix of 1s (True) and 0s (False),
                            for the directly (dis)connected (neighboring) points, respectively
        :return: a vector assigning all points to 0 (cluster 1) or 1 (cluster 2)
        """
        # Define the model to be clustered...:
        model = AgglomerativeClustering(affinity="precomputed", connectivity=connectivity,
                                        n_clusters=n_clusters, linkage='average')
        # and fit to return only n_clusters:
        model.fit(distance)
        # Get the cluster labels [0,n_clusters-1] for each point
        clusters = model.labels_
        return clusters

    # This function clusters the nodes of a mesh, using hierarchical clustering,
    # an affinity matrix, and connectivity constraints
    def run_clustering(self, affinity, parc_area, surface,
                       clustering_mode='divisive', connectivity=None):
        """
        :param affinity: a distance array, number_of_verts x number_of_verts as clustering criterion
        :param parc_area: the target average parcel area
        :param surface: a surface object
        :param geod_dist: geodesic distance array, number_of_verts x number_of_verts, used for assignment of too small
                            clusters to accepted ones
        :param clustering_mode: 'agglomerative'or 'divisive' hierarchical clustering
        :param connectivity: an array of structural connectivity constraints, where True or 1 stands for the existing
                            direct connections among neighboring vertices (i.e., vertices of a common triangular face)
        :return: clusters: an array of one integer index>=0, coding for participation to a cluster/parcel
        """
        # Total number of vertices to cluster:
        n_verts = surface.n_vertices
        # Initialize
        # -the number of resulting clusters:
        n_out_clusters = 0
        # -the number of too small clusters, which will be assigned to other clusters:
        n_too_small = 0
        # -the cluster indexes to be returned:
        clusters = -numpy.ones((n_verts,))
        # - the cluster labels:
        clusters_labels = []
        #clusters_areas = []
        # -a list of masks for vertices' clusters, which need to be further clustered:
        verts2cluster = []
        verts2cluster.append(numpy.ones((n_verts,)).astype('bool'))
        # - a list of masks for vertices of too small clusters:
        too_small = []
        #too_small_clusters_areas = []
        # Threshold for too small clusters:
        min_parc_area = MIN_PARC_AREA_RATIO * parc_area
        # Threshold for acceptance of a cluster:
        max_parc_area = MAX_PARC_AREA_RATIO * parc_area
        # While there are still clusters to further cluster:
        # NOTE: all masks refer to the original vertices array and are of
        # length n_verts!
        iter = 0
        while len(verts2cluster) > 0:
            iter += 1
            curr_accept = 0
            curr_too_small = 0
            curr_too_big = 0
            # get the first cluster out of the queue
            curr_verts_mask = verts2cluster.pop(0)
            # as well as the corresponding affinity matrix
            curr_affinity = affinity[curr_verts_mask, :][:, curr_verts_mask]
            # the corresponding sub-surface:
            if connectivity is not None:
                # and its corresponding connectivity matrix, if any
                curr_connectivity = connectivity[
                    curr_verts_mask, :][:, curr_verts_mask]
            # Determine the number of desired clusters at the current round as:
            # (approximate number of target clusters - current number of output clusters) /
            # (number of remaining clusters to be further clustered in the queue)
            # minimum should be 2
            curr_area = self.surface_service.compute_surface_area(surface,
                                                                  area_mask=numpy.logical_and(surface.area_mask, curr_verts_mask))
            if clustering_mode == 'agglomerative':
                curr_n_clusters = numpy.round(
                    curr_area / parc_area).astype('i')
                print(("     Iteration " + str(iter) + "...aiming at "
                       "clustering a white tract area of "
                       + str(curr_area) + " mm2 in " +
                       str(curr_n_clusters) + "  "
                       "clusters..."))
                curr_clusters = self.agglomerative_clustering(curr_affinity, n_clusters=curr_n_clusters,
                                                              connectivity=curr_connectivity)
            elif clustering_mode == 'divisive':
                print(("     Iteration " + str(iter) + "...aiming at "
                       "clustering a white tract area of "
                       + str(curr_area) + " mm2 in 2 clusters..."))
                curr_clusters = self.divisive_clustering(curr_affinity, connectivity=curr_connectivity,
                                                         surface=self.surface_service.extract_subsurf(surface, curr_verts_mask))
            # and loop through the respective labels...
            for i_cluster in range(curr_n_clusters):
                # ...compute a boolean mask of the vertices of each label:
                subcluster_mask = numpy.array(curr_verts_mask)
                subcluster_mask[curr_verts_mask ==
                                True] = curr_clusters == i_cluster
                #...and calculate the area of that parcel that touches white matter tracts:
                subcluster_lbl_area = self.surface_service.compute_surface_area(surface,
                                                                                numpy.logical_and(surface.area_mask, subcluster_mask))
                # If subcluster_lbl_area is between the min and max areas
                # allowed:
                if subcluster_lbl_area > min_parc_area and subcluster_lbl_area < max_parc_area:
                    #...make sure that the parcel is fully connected:
                    n_components = \
                        self.surface_service.connected_surface_components(connectivity=connectivity,
                                                                          verts_mask=subcluster_mask)[0]
                    assert n_components == 1
                    clusters[subcluster_mask] = n_out_clusters
                    clusters_labels.append(n_out_clusters)
                    # clusters_areas.append(subcluster_lbl_area)
                    n_out_clusters += 1
                    curr_accept += 1
                # else if it is too small:
                elif subcluster_lbl_area < min_parc_area:
                    #...store it as a cluster to be assigned to another one in the end:
                    too_small.append(numpy.array(subcluster_mask))
                    # too_small_clusters_areas.append(subcluster_lbl_area)
                    n_too_small += 1
                    curr_too_small += 1
                # else if it is too big:
                else:
                    #...add it to the queue for further clustering:
                    verts2cluster.append(numpy.array(subcluster_mask))
                    curr_too_big += 1
            print((" ...returned " + str(curr_accept) + " accepted, "
                   + str(curr_too_small) + " too small, and " + str(
                curr_too_big) + " too big clusters"))
        # If any too small clusters, prepare the distance matrix:
        if n_too_small > 0:
            print((" ...Assigning now " + str(n_too_small) + " too small "
                   "clusters to the closest clusters in affinity space..."))
            if connectivity is not None:
                print("...subject to structural connectivity constraints...")
                connectivity_temp = connectivity.todense()
                connectivity_temp[connectivity == 0] = 100.0
            #...and loop over them:
            for i_small_cluster in range(n_too_small):
                #...initialize an infintely long distance as minimum distance:
                mindist = +numpy.inf
                #...and the assignement to a cluster:
                assign_to_cluster = -1
                #...loop over the existing clusters so far:
                for i_cluster in clusters_labels:
                    #...calculate the minimum mean affinity from the "too small cluster" to each one
                    # of the existing clusters:
                    temp_dist = numpy.mean(affinity[too_small[i_small_cluster], :][
                                           :, clusters == i_cluster])
                    if connectivity is not None:
                        # ...making sure that the connectivity constraint is met
                        temp_dist += \
                            numpy.min(numpy.sum(connectivity[too_small[i_small_cluster], :][
                                      :, clusters == i_cluster]))
                    #...if it is the new minimum distance, perform the corresponding assignments:
                    if temp_dist < mindist:
                        mindist = temp_dist
                        assign_to_cluster = i_cluster
                # Having looped over all clusters, assign now the "too small
                # cluster" to the winning cluster:
                clusters[too_small[i_small_cluster]] = assign_to_cluster
            del connectivity_temp
        clusters_areas = []
        print(" ...Finally, checking that all clusters are fully connected "
              "and calculating final white tract areas...")
        for i_cluster in clusters_labels:
            (n_components, _, comp_area) = \
                self.surface_service.connected_surface_components(surface=surface, connectivity=connectivity,
                                                                  verts_mask=clusters == i_cluster)
            assert n_components == 1
            clusters_areas.append(comp_area[0])
        # The following code is not used anymore:
        # You can also do
        # children=model.children_
        # to get an (n_vertscon,2) array of all nodes with their children
        # or
        #cluster_tree=dict(enumerate(model.children_, model.n_leaves_))
        # which will give you a dictionary where each key is the
        # ID of a node and the value is the pair of IDs of its children.
        # or to get a list:
#       import itertools
#       ii = itertools.count(n_vertscon)
#       tree=[{'node_id': next(ii), 'left': x[0], 'right':x[1]} for x in model.children_]
        # Now make a tree out of it:
        #(cluster_tree,root)=tree.make_tree(cluster_tree)
        return (clusters, n_out_clusters, clusters_labels, clusters_areas)

    # TODO: a file of sub-parcellation statistics should be also saved as txt
    # and as npy.
    def connectivity_geodesic_subparc(self, surf_path, annot_path, con_verts_idx, out_annot_path=None,
                                      labels=None, ctx=None, add_string='',
                                      parc_area=100, con_sim_aff=1.0, geod_dist_aff=1.0,
                                      structural_connectivity_constraint=True,
                                      clustering_mode='divisive',
                                      cras_path=None, ref_vol_path=None, consim_path=None,
                                      in_lut_path=os.path.join(
                                          os.environ['FREESURFER_HOME'], DEFAULT_LUT),
                                      out_lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT)):
        """
        This is the main function performing the sub-parcellation.
        :param surf_path: The path to the surface to be parcellated, in ras or freesurfer ras (tk-ras) coordinates
        :param annot_path: The path to the freesurfer annotation file of this surface
        :param con_verts_idx: a boolean vector, determining which vertices of the surface are neighboring
                                white matter tracts ends
        :param out_annot_path: The path for the output annotation file to be saved
        :param labels: An optional list of the target region labels to be sub-parcellated.
            It should be given for sub-cortical surfaces, or in cases a sub-selection of cortical surfaces is desired.
        :param ctx: Alternatively, ctx should be given as 'lh' or 'rh' in order to select the whole left or right cortex
        :param add_string: String to add at the start of region names, i.e., 'ctx-lh-' or 'ctx-rh-' for cortical ones
        :param parc_area: an approximate target sub-parcel surface area, referring only to area touching white matter
        :param con_sim_aff: a 0=< weight <=1.0 for the connectivity dissimilarity affinity, as clustering criterion
        :param geod_dist_aff: a 0=< weight <=1.0 for the geodesic distance affinity, as clustering criterion
            (The final affinity matrix will be formed as a weighted sum (linear combination) of the two)
        :param structural_connectivity_constraint: True or False, for inclusion of a structural connectivity constraint,
            optionally constraining the resulting sub-parcels to be fully connected (having no disconnected components)
        :param clustering_mode: 'agglomerative'or 'divisive' hierarchical clustering
        :param cras_path: The path to the file where the freesurfer cras point is saved.
                         Necessary if the surface is in freesurfer's (tk-ras) ras coordinates.
        :param ref_vol_path: The path to the tdi_lbl volume, labeling the connectome nodes-voxels, as integers>=1.
                            Necessary only if the connectivity dissimilarity affinity is used.
        :param consim_path: The path to the connectivity dissimilarity affinity matrix of the connectome nodes-voxels.
                            Necessary only if the connectivity dissimilarity affinity is used.
        :param in_lut_path: The path to an input freesurfer-like Color LUT file ot use for reading target label names
        :param out_lut_path: The path to a freesurfer-like Color LUT file, to be written/appended for the new annotation
        :return: Nothing. New annotation is saved to a file.
        """

        # Read the surface...
        surface = IOUtils.read_surface(surf_path, False)
        # ...and its annotation
        annotation = IOUtils.read_annotation(annot_path)
        # ...and get the corresponding labels:
        # TODO: in the future there should be alternative ways to define the target labels,
        # probably directly via the annotation, not via any lut file,
        # so that we can further sub-parcellate a sub-parcellation, for which
        # there is no lut file
        labels_annot = self.annotation_service.annot_names_to_labels(annotation.region_names,
                                                                     add_string=add_string, lut_path=in_lut_path)
        # Read the indexes of vertices neighboring tracts' ends voxels:
        con_verts_idx = numpy.load(con_verts_idx)
        # Set the target labels:
        labels = self.annotation_service.read_input_labels(
            labels=labels, ctx=ctx)
        if con_sim_aff > 0:
            # Load voxel connectivity dissimilarity/distance matrix:
            con = numpy.load(consim_path).astype('single')
            # Convert it back to similarity cosine because we want to use
            # arccos instead of 1-cos for distance:
            con = 1 - con
            # Read the cras:
            cras = numpy.loadtxt(cras_path)
            # Get only the reference tdi_lbl volume's voxels that correspond to connectome nodes
            # and their ras xyz coordinates:
            vox, voxxzy = self.volume_service.con_vox_in_ras(ref_vol_path)
        # Initialize the output:
        region_names = []
        region_color_table = []
        region_mapping = - \
            numpy.ones(annotation.region_mapping.shape).astype('i')
        n_out_labels = int(0)
        # For every annotation name:
        for i_label in range(len(annotation.region_names)):
            print((str(i_label) + ". " + annotation.region_names[i_label]))
            # Get the mask of the respective vertices
            ind_verts_mask = annotation.region_mapping == i_label
            # ...and their indexes
            ind_verts, = numpy.where(ind_verts_mask)
            n_verts = len(ind_verts)
            # Find the corresponding label:
            lbl = labels_annot[i_label]
            # If there are no associated vertices or if it is not one of the
            # target labels:
            if n_verts == 0 or (lbl not in labels):
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[
                                          i_label, numpy.newaxis])
                # and change the output indices
                region_mapping[ind_verts] = n_out_labels
                n_out_labels += 1
                print(("Added " + annotation.region_names[i_label] + " as it "
                       "stands..."))
                continue
            # Get the vertices and faces of this label:
            label_surface = self.surface_service.extract_subsurf(
                surface, ind_verts_mask)
            # Compute distances among directly connected vertices
            dist = self.surface_service.vertex_connectivity(label_surface, mode="sparse",
                                                            metric='euclidean', symmetric=True).astype('single')
            # Mask of label vertices that are neighbors of tract end voxels
            # ("con"):
            label_surface.area_mask = numpy.in1d(ind_verts, con_verts_idx)
            # Calculate total area on_out_labels of "con" surface:
            lbl_area = self.surface_service.compute_surface_area(label_surface)
            print((annotation.region_names[i_label] + " total connectivity area "
                   "= " + str(lbl_area) + " mm2"))
            # If no further parcellation is needed
            if lbl_area < 1.5 * parc_area:
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[
                                          i_label, numpy.newaxis])
                # and change the output indices
                region_mapping[ind_verts] = n_out_labels
                n_out_labels += 1
                print(("Added " + annotation.region_names[i_label] +
                       " as it stands because its connectivity area is less than 1.5 times the target value"))
                continue
            # Get all different (dis)connected components
            n_components, components, comp_area = \
                self.surface_service.connected_surface_components(
                    surface=label_surface, connectivity=dist)
            n_components = len(comp_area)
            print((str(n_components) + " connected components in total of "
                   + str(comp_area) + " mm2 connectivity area, respectively"))
            n_parcels = int(0)
            parcels = -numpy.ones(components.shape, dtype='i')
            too_small_parcels = []
            for i_comp in range(n_components):
                i_comp_verts = components == i_comp
                n_comp_verts = numpy.sum(i_comp_verts)
                print(("...Treating connected surface component " + str(i_comp)
                       + " of connectivity area " + str(comp_area[i_comp]) + " mm2"))
                if comp_area[i_comp] <= MAX_PARC_AREA_RATIO * parc_area:
                    if comp_area[i_comp] >= 0.1 * [parc_area]:
                        parcels[i_comp_verts] = n_parcels
                        n_parcels += 1
                        print(("...Directly assigned to parcel " + str(
                            n_parcels) + ","))
                        print(("...because its connectivity area is within the limits of [" +
                               str(MIN_PARC_AREA_RATIO) + ", " + str(
                                   MAX_PARC_AREA_RATIO) + "] times the target value"))
                    else:
                        print("...Too small surface component, i.e., "
                              "less than 0.1 times the target average parcel area.")
                        print(
                            "...It will inherit the identity of the closest parcel in terms of euclidean distance.")
                        too_small_parcels.append(i_comp_verts)
                else:
                    print(("...Clustering will run for surface component " + str(i_comp)
                           + " of region " + annotation.region_names[i_label]))
                    # Extract the sub-surface of this component
                    component_surface = self.surface_service.extract_subsurf(
                        label_surface, i_comp_verts)
                    if structural_connectivity_constraint:
                        print("...Forming the structural connectivity "
                              "constraint matrix...")
                        connectivity = dist[i_comp_verts, :][
                            :, i_comp_verts].astype('single')
                        connectivity[connectivity > 0.0] = 1.0
                    else:
                        connectivity = None
                    if con_sim_aff > 0:
                        print("...Computing the connectivity dissimilarity "
                              "affinity matrix...")
                        affinity =\
                            self.surface_service.compute_consim_affinity(
                                component_surface.vertices, vox, voxxzy, con, cras).astype('single')
                        # Convert cosine distance to cosine
                        affinity = 1 - affinity
                        # invert cosine similarity to arccos distance
                        affinity = numpy.arccos(affinity)
                        # Normalize with maximum in [0,1]
                        affinity /= numpy.max(affinity).astype('single')
                        #...and then weight it by con_sim_aff:
                        affinity *= con_sim_aff
                    else:
                        # Initialize affinity matrix with zeros
                        affinity = numpy.zeros(
                            (n_comp_verts, n_comp_verts)).astype('single')
                    print("...Computing the geodesic distance affinity "
                          "matrix...")
                    if geod_dist_aff > 0:
                        # Compute geodesic distance normalized in [0,1] and
                        # add it to the affinity metric with the correct weight
                        affinity += geod_dist_aff * self.surface_service.compute_geodesic_dist_affinity(
                            dist[i_comp_verts, :][:, i_comp_verts].todense(), norm='max').astype('single')
                    n_clusters = numpy.round(
                        comp_area[i_comp] / parc_area).astype('i')
                    print(("...Running clustering, aiming at approximately " + str(n_clusters) + " clusters of "
                           + str(parc_area) + " mm2 connectivity area..."))
                    (clusters, n_clusters, clusters_labels, clusters_areas) = self.run_clustering(affinity, parc_area,
                                                                                                  component_surface, clustering_mode=clustering_mode,
                                                                                                  connectivity=connectivity)
                    print(("..." + str(n_clusters) +
                           ' parcels finally created for component ' +
                           str(i_comp)
                           + " of region " + annotation.region_names[i_label]
                           + " with connectivity areas " + str(clusters_areas)
                           + ", respectively"))
                    parcels[i_comp_verts] = clusters + n_parcels
                    n_parcels += int(n_clusters)
            parcel_labels = list(range(n_parcels))
            for i_comp_verts in too_small_parcels:
                print(("...Dealing now with too small surface components..."
                       + " of region " + annotation.region_names[i_label]))
                comp_to_parcel_mindist = 1000.0  # this is 1 meter long!
                assign_to_parcel = -1
                for ip in parcel_labels:
                    temp_dist =\
                        numpy.min(cdist(label_surface.vertices[i_comp_verts, :], label_surface.vertices[parcels == ip, :],
                                        'euclidean'), axis=None)
                    if temp_dist < comp_to_parcel_mindist:
                        comp_to_parcel_mindist = temp_dist
                        assign_to_parcel = ip
                parcels[i_comp_verts] = assign_to_parcel
                print(("...Component " + str(i_comp) + " assigned to parcel " + str(assign_to_parcel)
                       + " with a minimum euclidean distance of " + str(
                    comp_to_parcel_mindist) + " mm"))
            if n_parcels == 1:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[
                                          i_label, numpy.newaxis])
            else:
                # Create the new annotation for these sub-labels:
                (names_lbl, ctab_lbl) = self.annotation_service.gen_new_parcel_annots(parcel_labels,
                                                                                      annotation.region_names[i_label], annotation.regions_color_table[i_label, numpy.newaxis])
                # Add the new label names
                region_names.append(names_lbl)
                #...and the new ctabs
                region_color_table.append(ctab_lbl)
            # Finally change the output indices
            # of the "con" vertices...
            region_mapping[ind_verts] = n_out_labels + parcels.astype('i')
            n_out_labels += int(n_parcels)
            for i_parcel in range(n_parcels):
                i_parc_verts = parcels == i_parcel
                parc_area_con = self.surface_service.compute_surface_area(label_surface,
                                                                          area_mask=numpy.logical_and(i_parc_verts, label_surface.area_mask))
                print(('...parcel ' + names_lbl[i_parcel] + ' of connectivity '
                       'area ' + str(parc_area_con) + ' mm2'))
                parc_area_tot = self.surface_service.compute_surface_area(
                    label_surface, area_mask=i_parc_verts)
                print(("...and of total area " + str(parc_area_tot) + ' mm2'))
        print("Write output annotation file")
        # Stack everything together
        region_color_table = numpy.vstack(region_color_table)
        region_names = numpy.hstack(region_names)
        # ...write the annotation to a file
        if out_annot_path is None:
            out_annot_path = os.path.splitext(
                annot_path)[0] + str(parc_area) + ".annot"
        print(out_annot_path)
        IOUtils.write_annotation(out_annot_path, Annotation(
            region_mapping, region_color_table, region_names))
        #...and write or append the lut file
        self.annotation_service.annot_to_lut(
            out_annot_path, lut_path=out_lut_path, prefix=add_string)
