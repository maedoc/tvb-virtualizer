# -*- coding: utf-8 -*-

import os
import numpy
import scipy
from scipy.spatial.distance import pdist, cdist, squareform
from sklearn.cluster import AgglomerativeClustering
#from scipy.cluster import hierarchy
#import bnm.recon.algo.tree as tree
from bnm.recon.io.factory import IOUtils
from bnm.recon.algo.service.annotation import AnnotationService, DEFAULT_LUT
from bnm.recon.algo.service.surface import SurfaceService
from bnm.recon.algo.service.volume import VolumeService
from bnm.recon.model.annotation import Annotation

MIN_PARC_AREA_RATIO = 0.5
MAX_PARC_AREA_RATIO = 1.5

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
            roi_area = numpy.sum(self.surface_service.tri_area(surface.vertices[surface.triangles[rfi]]))

            # choose k for desired roi area
            k = int(roi_area / trg_area) + 1
            assert k >= 1

            # cluster centered vertices
            v_roi = surface.vertices[mask]
            _, i_lab = scipy.cluster.vq.kmeans2(v_roi - v_roi.mean(axis=0), k)

            # update annot
            new_annotation.region_mapping[mask] = next_aval + i_lab
            next_aval += k
            new_annotation.region_names += ['%s-%d' % (name.decode('ascii'), j) for j in range(k)]

        # create random colored ctab
        new_annotation.regions_color_table = numpy.random.randint(255, size=(len(new_annotation.region_names), 5))
        r, g, b, _, _ = new_annotation.regions_color_table.T
        new_annotation.regions_color_table[:, 3] = 0
        new_annotation.regions_color_table[:, 4] = self.annotation_service.rgb_to_fs_magic_number([r, g, b])

        return new_annotation

    def subparc_files(self, surf_path, annot_path, out_annot_parc_name, trg_area):
        trg_area = float(trg_area)
        surface = IOUtils.read_surface(surf_path, False)
        annotation = IOUtils.read_annotation(annot_path)
        new_annotation = self.make_subparc(surface, annotation, trg_area=trg_area)
        IOUtils.write_annotation(out_annot_parc_name, new_annotation)

    #TODO: maybe create a new "connectome" service and transfer this function there
    def node_connectivity_metric(self, con_mat_path, metric="cosine", out_consim_path=None):
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



    def divisive_clustering(self, verts, faces, ind_verts_con, distance, connectivity=None):

        #Initialize clusters' masks:
        n_points = distance.shape[0]
        clusters=[]
        clusters.append(numpy.zeros((n_points,)).astype('bool'))
        clusters.append(numpy.zeros((n_points,)).astype('bool'))
        clusters_areas=[]
        clusters_areas.append(0.0)
        clusters_areas.append(0.0)

        #Find two most distant points
        [c1, c2] = numpy.where(numpy.max(distance))
        #Assign them as first points to each cluster:
        clusters[0][c1[0]] = True
        clusters[1][c2[0]] = True

        #Remaining points:
        rest = numpy.ones((n_points,)).astype('bool')
        rest[c1[0]] = False
        rest[c2[0]] = False

        tocluster = []
        assign=[]
        #While there are remaining points:
        while numpy.any(rest):

            #Initialize the available points for each cluster:
            tocluster.append(numpy.array(rest))
            tocluster.append(numpy.array(rest))
            #And the assignment:
            assign.append(-1)
            assign.append(-1)

            #Get the index of the smaller cluster to start with:
            clusters_order = numpy.argsort(clusters_areas)
            ic=clusters_order.pop(0)

            while assign[ic] and numpy.any(tocluster[ic]):
                pass
            pass




    # This function clusters the nodes of a mesh, using hierarchical clustering,
    # an affinity matrix, and connectivity constraints
    def run_clustering(self,affinity,parc_area,verts,faces,ind_verts_con,connectivity=None, n_clusters=2):
        """
        :param affinity: a distance array, number_of_verts x number_of_verts as clustering criterion
        :param parc_area: the target average parcel area
        :param verts: the array of vertices' coordinates, number_of_verts x 3
        :param faces: the array of faces, number_of_faces x 3, integers
        :param ind_verts_con: a boolean array, defining a mask on the vertices, where true stands for those vertices
                        that are close to voxels, where white matter tracts start or end
        :param geod_dist: geodesic distance array, number_of_verts x number_of_verts, used for assignment of too small
                            clusters to accepted ones
        :param connectivity: an array of structural connectivity constraints, where True or 1 stands for the existing
                            direct connections among neighboring vertices (i.e., vertices of a common triangular face)
        :return: clusters: an array of one integer index>=0, coding for participation to a cluster/parcel
        """
        #Total number of vertices to cluster:
        n_verts = verts.shape[0]
        #Initialize
        # -the number of resulting clusters:
        n_out_clusters = 0
        # -the number of too small clusters, which will be assigned to other clusters:
        n_too_small = 0
        # -the cluster indexes to be returned:
        clusters=-numpy.ones((n_verts,))
        # - the cluster labels:
        clusters_labels = []
        #clusters_areas = []
        # -a list of masks for vertices' clusters, which need to be further clustered:
        verts2cluster=[]
        verts2cluster.append(numpy.ones((n_verts,)).astype('bool'))
        # - a list of masks for vertices of too small clusters:
        too_small = []
        #too_small_clusters_areas = []
        #Threshold for too small clusters:
        min_parc_area=MIN_PARC_AREA_RATIO*parc_area
        #Threshold for acceptance of a cluster:
        max_parc_area = MAX_PARC_AREA_RATIO * parc_area
        #While there are still clusters to further cluster:
        #NOTE: all masks refer to the original vertices array and are of length n_verts!
        while len(verts2cluster)>0:
            # get the first cluster out of the queue
            curr_verts_mask = verts2cluster.pop(0)
            # as well as the corresponding affinity matrix
            curr_affinity=affinity[curr_verts_mask,:][:,curr_verts_mask]
            # the corresponding sub-surface:
            if connectivity is not None:
                # and its corresponding connectivity matrix, if any
                curr_connectivity = connectivity[curr_verts_mask,:][:,curr_verts_mask]
            # Determine the number of desired clusters at the current round as:
            # (approximate number of target clusters - current number of output clusters) /
            # (number of remaining clusters to be further clustered in the queue)
            # minimum should be 2
            curr_n_clusters = \
                  numpy.max([2,numpy.round(1.0 * (n_clusters - n_out_clusters) / numpy.max([len(verts2cluster),1]))]).astype('i')
            # define the current model to be clustered now...:
            model = AgglomerativeClustering(affinity="precomputed", connectivity=curr_connectivity,
                                                n_clusters=curr_n_clusters, linkage='average')
            # and fit to return only n_clusters (default behavior n_clusters=2):
            model.fit(curr_affinity)
            #Get the cluster labels [0,curr_n_clusters-1] for each vertex of curr_verts
            curr_clusters=model.labels_
            #and loop through the respective labels...
            for i_cluster in range(curr_n_clusters):
                # ...compute a boolean mask of the vertices of each label:
                subcluster_mask=numpy.array(curr_verts_mask)
                subcluster_mask[curr_verts_mask == True] = curr_clusters==i_cluster
                #...and calculate the area of that parcel that touches white matter tracts:
                subcluster_lbl_area = self.surface_service.compute_surface_area(verts, faces,
                                                                                numpy.logical_and(ind_verts_con,subcluster_mask))
                #If subcluster_lbl_area is between the min and max areas allowed:
                if subcluster_lbl_area>min_parc_area and subcluster_lbl_area<max_parc_area:
                    #...store it as a new accepted cluster/parcel:
                    (curr_verts, curr_faces) = self.surface_service.extract_subsurf(verts, faces, subcluster_mask)
                    if connectivity is not None:
                        # and its corresponding connectivity matrix, if any
                        curr_connectivity = connectivity[subcluster_mask, :][:, subcluster_mask]
                    else:
                        curr_connectivity = None
                    n_components = \
                        self.surface_service.connected_surface_components(curr_verts, curr_faces,
                                                                          connectivity=curr_connectivity,
                                                                          mask=ind_verts_con[subcluster_mask])[0]
                    assert n_components == 1
                    clusters[subcluster_mask]=n_out_clusters
                    clusters_labels.append(n_out_clusters)
                    #clusters_areas.append(subcluster_lbl_area)
                    n_out_clusters += 1
                #else if it is too small:
                elif subcluster_lbl_area<min_parc_area:
                    #...store it as a cluster to be assigned to another one in the end:
                    too_small.append(numpy.array(subcluster_mask))
                    #too_small_clusters_areas.append(subcluster_lbl_area)
                    n_too_small += 1
                #else if it is too big:
                else:
                    #...add it to the queue for further clustering:
                    verts2cluster.append(numpy.array(subcluster_mask))
        #If any too small clusters, prepare the distance matrix:
        if n_too_small > 0:
            if connectivity is not None:
                connectivity = connectivity.todense()
                connectivity[connectivity == 0] = 100.0
            #...and loop over them:
            for i_small_cluster in range(n_too_small):
                #...initialize a very long distance as minimum distance:
                mindist = 1000.0  # this is 1 meter long!
                #...and the assignement to a cluster:
                assign_to_cluster = -1
                #...loop over the existing clusters so far:
                for i_cluster in clusters_labels:
                    #...calculate the minimum mean affinity from the "too small cluster" to each one
                    #of the existing clusters:
                    temp_dist = numpy.mean(affinity[too_small[i_small_cluster], :][:, clusters == i_cluster])
                    if connectivity is not None:
                        # ...making sure that the connectivity constraint is met
                        temp_dist += numpy.min(connectivity[too_small[i_small_cluster], :][:, clusters == i_cluster])
                    #...if it is the new minimum distance, perform the corresponding assignments:
                    if temp_dist < mindist:
                        mindist = temp_dist
                        assign_to_cluster = i_cluster
                #Having looped over all clusters, assign now the "too small cluster" to the winning cluster:
                clusters[too_small[i_small_cluster]] = assign_to_cluster
        clusters_areas=[]
        for i_cluster in clusters_labels:
            curr_verts_mask=clusters==i_cluster
            (curr_verts, curr_faces)=self.surface_service.extract_subsurf(verts,faces,curr_verts_mask)
            if connectivity is not None:
                # and its corresponding connectivity matrix, if any
                curr_connectivity = connectivity[curr_verts_mask, :][:, curr_verts_mask]
            else:
                curr_connectivity = None
            (n_components, _, comp_area) = \
                self.surface_service.connected_surface_components(curr_verts, curr_faces,
                                                                  connectivity=curr_connectivity,
                                                                  mask=ind_verts_con[curr_verts_mask])
            assert n_components==1
            clusters_areas.append(comp_area[0])
        #The following code is not used anymore:
        #You can also do
        #children=model.children_
        #to get an (n_vertscon,2) array of all nodes with their children
        #or
        #cluster_tree=dict(enumerate(model.children_, model.n_leaves_))
        #which will give you a dictionary where each key is the
        #ID of a node and the value is the pair of IDs of its children.
        #or to get a list:
#       import itertools
#       ii = itertools.count(n_vertscon)
#       tree=[{'node_id': next(ii), 'left': x[0], 'right':x[1]} for x in model.children_]
        #Now make a tree out of it:
        #(cluster_tree,root)=tree.make_tree(cluster_tree)
        return (clusters, n_out_clusters, clusters_labels, clusters_areas)

    #TODO: a file of sub-parcellation statistics should be also saved as txt and as npy.
    def connectivity_geodesic_subparc(self, surf_path, annot_path, con_verts_idx, out_annot_path=None,
                                      labels=None, ctx=None, add_string='',
                                      parc_area=100, con_sim_aff=1.0, geod_dist_aff=1.0,
                                      structural_connectivity_constraint=True,
                                      cras_path=None, ref_vol_path=None, consim_path=None,
                                      in_lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT),
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
        #  so that we can further sub-parcellate a sub-parcellation, for which there is no lut file
        labels_annot = self.annotation_service.annot_names_to_labels(annotation.region_names,
                                                                     add_string=add_string, lut_path=in_lut_path)
        # Read the indexes of vertices neighboring tracts' ends voxels:
        con_verts_idx = numpy.load(con_verts_idx)
        # Set the target labels:
        labels, n_in_labels = self.annotation_service.read_input_labels(labels=labels, ctx=ctx)
        if con_sim_aff > 0:
            # Load voxel connectivity dissimilarity/distance matrix:
            con = numpy.load(consim_path).astype('single')
            # Convert it back to similarity cosine because we want to use arccos instead of 1-cos for distance:
            con = 1-con
            # Read the cras:
            cras = numpy.loadtxt(cras_path)
            # Get only the reference tdi_lbl volume's voxels that correspond to connectome nodes
            # and their ras xyz coordinates:
            vox, voxxzy = self.volume_service.con_vox_in_ras(ref_vol_path)
        # Initialize the output:
        region_names = []
        region_color_table = []
        region_mapping = -numpy.ones(annotation.region_mapping.shape).astype('i')
        n_out_labels = int(0)
        # For every annotation name:
        for i_label in range(len(annotation.region_names)):
            print str(i_label) + ". " + annotation.region_names[i_label]
            # Get the mask of the respective vertices
            ind_verts_mask = annotation.region_mapping == i_label
            # ...and their indexes
            ind_verts, = numpy.where(ind_verts_mask)
            n_verts = len(ind_verts)
            # Find the corresponding label:
            lbl = labels_annot[i_label]
            # If there are no associated vertices or if it is not one of the target labels:
            if n_verts == 0 or (lbl not in labels):
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[i_label, numpy.newaxis])
                # and change the output indices
                region_mapping[ind_verts] = n_out_labels
                n_out_labels += 1
                print "Added "+annotation.region_names[i_label]+" as it stands..."
                continue
            # Get the vertices and faces of this label:
            (verts_lbl, faces_lbl) = self.surface_service.extract_subsurf(surface.vertices, surface.triangles, ind_verts_mask)
            # Compute distances among directly connected vertices
            dist = self.surface_service.vertex_connectivity(verts_lbl, faces_lbl, mode="sparse",
                                                            metric='euclidean', symmetric=True ).astype('single')
            # Mask of label vertices that are neighbors of tract end voxels ("con"):
            ind_verts_con = numpy.in1d(ind_verts, con_verts_idx)
            # Calculate total area on_out_labels of "con" surface:
            lbl_area = self.surface_service.compute_surface_area(verts_lbl, faces_lbl, ind_verts_con)
            print annotation.region_names[i_label]+" total connectivity area = " + str(lbl_area) + " mm2"
            # If no further parcellation is needed
            if lbl_area < 1.5*parc_area:
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[i_label, numpy.newaxis])
                # and change the output indices
                region_mapping[ind_verts] = n_out_labels
                n_out_labels += 1
                print "Added " + annotation.region_names[i_label] + \
                    " as it stands because its connectivity area is less than 1.5 times the target value"
                continue
            # Get all different (dis)connected components
            n_components, components, comp_area = \
                self.surface_service.connected_surface_components(verts_lbl,faces_lbl, connectivity=dist,mask=ind_verts_con)
            n_components=len(comp_area)
            print str(n_components)+" connected components in total of "\
                  +str(comp_area)+" mm2 connectivity area, respectively"
            n_parcels=int(0)
            parcels=-numpy.ones(components.shape,dtype='i')
            too_small_parcels=[]
            for i_comp in range(n_components):
                i_comp_verts = components == i_comp
                n_comp_verts=numpy.sum(i_comp_verts)
                print "...Treating connected surface component "+str(i_comp)\
                      +" of connectivity area "+str(comp_area[i_comp])+" mm2"
                if comp_area[i_comp]<=MAX_PARC_AREA_RATIO*parc_area:
                    if comp_area[i_comp]>=0.1*[parc_area]:
                        parcels[i_comp_verts] = n_parcels
                        n_parcels+=1
                        print "...Directly assigned to parcel "+str(n_parcels)+","
                        print "...because its connectivity area is within the limits of ["+ \
                        str(MIN_PARC_AREA_RATIO)+ ", " + str(MAX_PARC_AREA_RATIO)+"] times the target value"
                    else:
                        print "...Too small surface component, i.e., less than 0.1 times the target average parcel area."
                        print "...It will inherit the identity of the closest parcel in terms of euclidean distance."
                        too_small_parcels.append(i_comp_verts)
                else:
                    print "...Clustering will run for surface component " + str(i_comp) \
                          + " of region " + annotation.region_names[i_label]
                    # Extract the sub-surface of this component
                    (verts_comp, faces_comp) = self.surface_service.extract_subsurf(verts_lbl, faces_lbl, i_comp_verts)
                    if structural_connectivity_constraint:
                        print "...Forming the structural connectivity constraint matrix..."
                        connectivity = dist[i_comp_verts, :][:, i_comp_verts].astype('single')
                        connectivity[connectivity>0.0] = 1.0
                    else:
                        connectivity = None
                    if con_sim_aff>0:
                        print "...Computing the connectivity dissimilarity affinity matrix..."
                        affinity=\
                          self.surface_service.compute_consim_affinity(verts_comp, vox, voxxzy, con, cras).astype('single')
                        # Convert cosine distance to cosine
                        affinity = 1 - affinity
                        # invert cosine similarity to arccos distance
                        affinity = numpy.arccos(affinity)
                        # Normalize with maximum in [0,1]
                        affinity /= numpy.max(affinity).astype('single')
                        #...and then weight it by con_sim_aff:
                        affinity*=con_sim_aff
                    else:
                        # Initialize affinity matrix with zeros
                        affinity = numpy.zeros((n_comp_verts, n_comp_verts)).astype('single')
                    print "...Computing the geodesic distance affinity matrix..."
                    if geod_dist_aff>0:
                        # Compute geodesic distance normalized in [0,1] and
                        # add it to the affinity metric with the correct weight
                        affinity += geod_dist_aff*self.surface_service.compute_geodesic_dist_affinity(
                            dist[i_comp_verts, :][:, i_comp_verts].todense(), norm='max').astype('single')
                    #Calculate an approximate number of desired clusters:
                    n_clusters=numpy.round(comp_area[i_comp]/parc_area).astype('i')
                    print "...Running clustering, aiming at approximately "+str(n_clusters)+" clusters of " \
                          + str(parc_area)+" mm2 connectivity area..."
                    (clusters, n_clusters, clusters_labels, clusters_areas)=self.run_clustering(affinity,parc_area,
                                                                     verts_comp, faces_comp,ind_verts_con[i_comp_verts],
                                                                     connectivity=connectivity, n_clusters=n_clusters)
                    print "..." + str(n_clusters) + \
                          ' parcels finally created for component ' + str(i_comp) \
                          + " of region " + annotation.region_names[i_label] \
                          + " with connectivity areas " + str(clusters_areas) + ", respectively"
                    parcels[i_comp_verts] = clusters+n_parcels
                    n_parcels+=int(n_clusters)
            parcel_labels=range(n_parcels)
            for i_comp_verts in too_small_parcels:
                print "...Dealing now with too small surface components..." \
                      + " of region " + annotation.region_names[i_label]
                comp_to_parcel_mindist=1000.0 #this is 1 meter long!
                assign_to_parcel=-1
                for ip in parcel_labels:
                    temp_dist=\
                        numpy.min(cdist(verts_lbl[i_comp_verts, :], verts_lbl[parcels==ip, :], 'euclidean'),axis=None)
                    if temp_dist<comp_to_parcel_mindist:
                        comp_to_parcel_mindist=temp_dist
                        assign_to_parcel=ip
                parcels[i_comp_verts]=assign_to_parcel
                print "...Component "+str(i_comp)+" assigned to parcel "+str(assign_to_parcel)\
                      +" with a minimum euclidean distance of "+ str(comp_to_parcel_mindist)+" mm"
            if n_parcels==1:
                region_names.append(annotation.region_names[i_label])
                region_color_table.append(annotation.regions_color_table[i_label, numpy.newaxis])
            else:
                # Create the new annotation for these sub-labels:
                (names_lbl,ctab_lbl)=self.annotation_service.gen_new_parcel_annots(parcel_labels,
                                annotation.region_names[i_label],annotation.regions_color_table[i_label, numpy.newaxis])
                # Add the new label names
                region_names.append(names_lbl)
                #...and the new ctabs
                region_color_table.append(ctab_lbl)
            # Finally change the output indices
            # of the "con" vertices...
            region_mapping[ind_verts] = n_out_labels + parcels.astype('i')
            n_out_labels += int(n_parcels)
            for i_parcel in range(n_parcels):
                i_parc_verts=parcels==i_parcel
                parc_area_con=self.surface_service.compute_surface_area(verts_lbl, faces_lbl,
                                                          mask=numpy.logical_and(i_parc_verts,ind_verts_con))
                print '...parcel '+names_lbl[i_parcel]+ ' of connectivity area ' + str(parc_area_con) + ' mm2'
                parc_area_tot = self.surface_service.compute_surface_area(verts_lbl,faces_lbl,mask=i_parc_verts)
                print "...and of total area " + str(parc_area_tot)  + ' mm2'
        print "Write output annotation file"
        # Stack everything together
        region_color_table = numpy.vstack(region_color_table)
        region_names = numpy.hstack(region_names)
        # ...write the annotation to a file
        if out_annot_path is None:
            out_annot_path = os.path.splitext(annot_path)[0] + str(parc_area) + ".annot"
        print out_annot_path
        IOUtils.write_annotation(out_annot_path, Annotation(region_mapping, region_color_table, region_names))
        #...and write or append the lut file
        self.annotation_service.annot_to_lut(out_annot_path,lut_path=out_lut_path,add_string=add_string)
