# -*- coding: utf-8 -*-

import os
import numpy
import scipy
from scipy.spatial.distance import pdist, cdist, squareform
from sklearn.cluster import AgglomerativeClustering
#from scipy.cluster import hierarchy
from scipy.sparse.csgraph import connected_components
import bnm.recon.algo.tree as tree
from scipy.sparse.csgraph import shortest_path
from bnm.recon.io.factory import IOUtils
from bnm.recon.algo.service.annotation import AnnotationService
from bnm.recon.algo.service.surface import SurfaceService
from bnm.recon.algo.service.volume import VolumeService
from bnm.recon.model.annotation import Annotation

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

        # It receives a binary connectivity matrix, and outputs a node connectivity
        # distance or dissimilarity  matrix
        # con_mat_path: path to connectivity file
        # metric: default "cosine"

    def node_connectivity_metric(self, con_mat_path, metric="cosine", out_consim_path=None):
        con = numpy.load(con_mat_path)
        # Calculate distance metric
        con = squareform(pdist(con, metric=metric))
        if out_consim_path is not None:
            numpy.save(out_consim_path, con)
        return con

    # Applying optionally a mask to the vertices and picking up only the relevant triangles,
    # before computing the surface area
    def compute_surface_area(self,v,f,mask=None):
        if mask is not None:
            #Apply the optional mask in order to extract the sub-surface (vertices and relevant triangles)
            (v, f) = self.surface_service.extract_subsurf(v, f, mask)
        return numpy.sum(self.surface_service.tri_area(v[f]))

    # This function takes as an input a reference tdi_lbl volume (ref_vol_path),
    # where increasing integers>0 signify each voxel-connectome node,
    #and it returns a vector of these voxels (vox),
    #  and their coordinates in the ras space of the original T1 (voxxyz),
    # simply by applying the affine transform of tdi_lbl.
    def con_vox_in_ras(self,ref_vol_path):
        # Read the reference tdi_lbl volume:
        vollbl = IOUtils.read_volume(ref_vol_path)
        vox = vollbl.data.astype('i')
        # Get only the voxels that correspond to connectome nodes:
        voxijk, = numpy.where(vox.flatten() > 0)
        voxijk = numpy.unravel_index(voxijk, vollbl.dimensions)
        vox = vox[voxijk[0], voxijk[1], voxijk[2]]
        # ...and their coordinates in freesurfer surface tk-ras xyz space
        voxxzy = vollbl.affine_matrix.dot(numpy.c_[voxijk[0], voxijk[1], voxijk[2], numpy.ones(vox.shape[0])].T)[:3].T
        return vox, voxxzy

    # This function
    # takes a surface and its connectivity matrix
    # (where for each triangle side, there is the value 1 for the corresponding connection)
    # separates the dis-connected components, if any, of a surface, and returns
    # in order to return the number (n_components),
    # the indices (components; an integer value for each component assigned to each vertex),
    # and the areas (comp_area; using an optional mask)
    # of all separate dis-connected components of the surface (1 component minimum)
    def connected_surface_components(self,v,f,connectivity, mask=None):
        #Find all connected components of this surface
        (n_components, components) = connected_components(connectivity, directed=False, connection='weak', return_labels=True)
        #Check out if there is a mask for the vertices to be included in the area calculation
        if mask is None:
            mask = numpy.ones(components.shape,dtype=bool)
        comp_area = []
        #For each component...
        for iC in range(n_components):
            i_comp_verts=components==iC
            #...compute the surface area, after applying any specified mask
            comp_area.append(self.compute_surface_area(v,f,mask=numpy.logical_and(i_comp_verts,mask[i_comp_verts])))
        return n_components, components, comp_area

    # This function takes as inputs
    # the vertices of a surface,
    # the voxels indices of the reference tdi_lbl volume
    # (optionally with cras in order to be transferred to freesurfer surface tk-ras space)
    # and their coordinates in the T1 ras space,
    # as well as the connectivity similarity matrix among the node-voxels of that volume,
    # in order to compute a connectivity distance matrix among the vertices (affinity; the output),
    # by assignement for each vertex from the nearest voxel,
    # and by inversion of the similarity using arccos (assuming cosine similarity as similarity metric)
    def compute_consim_affinity(self,verts,vox,voxxzy,con,cras=None):
        # Add the cras to take them to scanner ras coordinates, if necessary:
        if cras is not None:
            verts += numpy.repeat(numpy.expand_dims(cras, 1).T, verts.shape[0], axis=0)
        # TODO?: to use aparc+aseg to correspond vertices only to voxels of the same label
        # There would have to be a vertex->voxel of aparc+aseg of the same label -> voxel of tdi_lbl_in_T1 mapping
        # Maybe redundant  because we might be ending to the same voxel of tdi_lbl anyway...
        # Something to test/discuss...
        # Find for each vertex the closest voxel node in terms of euclidean distance:
        v2n = numpy.argmin(cdist(verts, voxxzy, 'euclidean'), axis=1)
        #Assign to each vertex the integer identity of the nearest voxel node.
        v2n = vox[v2n]
        print "Surface component's vertices correspond to " + str(numpy.size(numpy.unique(v2n))) + " distinct voxel nodes"
        # Convert connectivity similarity to a distance matrix
        # affinity = 1 - con[v2n - 1, :][:, v2n - 1]
        # (inverting cosine similarity to arccos distance)
        affinity = numpy.arccos(con[v2n - 1, :][:, v2n - 1])
        #Normalize with maximum
        affinity /=numpy.max(affinity).astype('single')
        return affinity

    # This function computes normalized (by maximum non-infinite) geodesic distances,
    # starting from a distance matrix between all adjacent nodes of a mesh
    def compute_geodesic_dist_affinity(self,dist):
        geodist = shortest_path(dist, method='auto', directed=False,
                                return_predecessors=False, unweighted=False, overwrite=False).astype('single')
        # Find the maximum non infite geodesic distance:
        max_gdist = numpy.max(geodist, axis=None)
        assert numpy.isfinite(max_gdist)
        # Convert them to normalized distances and return them
        return geodist/max_gdist

    # This function clusters the nodes of a mesh, using hiearchical clustering,
    # an affinity matrix, and connectivity constraints
    def run_clustering(self,affinity,parc_area,connectivity=None):
        model = AgglomerativeClustering(affinity="precomputed", connectivity=connectivity, linkage='average')
        model.fit(affinity)
        #You can also do
        #children=model.children_
        #to get an (nVcon,2) array of all nodes with their children
        #or
        cluster_tree=dict(enumerate(model.children_, model.n_leaves_))
        #which will give you a dictionary where each key is the
        #ID of a node and the value is the pair of IDs of its children.
        #or to get a list:
#       import itertools
#       ii = itertools.count(nVcon)
#       tree=[{'node_id': next(ii), 'left': x[0], 'right':x[1]} for x in model.children_]
        #Now make a tree out of it:
        (cluster_tree,root)=tree.make_tree(cluster_tree)
        return clusters

    # This function
    # takes as inputs the labels of a new parcellation, a base name for the parcels and a base color,
    # and generates the name labels, and colors of the new parcellation's annotation
    # It splits the RGB color space along the dimension that has a longer margin, in order to create new, adjacent colors
    # Names are created by just adding increasing numbers to the base name.
    def gen_new_parcel_annots(self,parcel_labels,base_name,base_ctab):
        n_parcels=len(parcel_labels)
        #Names:
        names_lbl = [base_name+ "-" + str(item).zfill(2) for item in parcel_labels]
        # Initialize ctab for these labels
        ctab_lbl = numpy.repeat(base_ctab, n_parcels, axis=0)
        # For the RGB coordinate with the bigger distance to 255 or 0
        # distribute that distance  to nParcs values:
        # Find the maximum and minimum RGB coordinates
        iC = numpy.argsort(base_ctab[0, :3])
        # Calculate the distances of the maximum RGB coordinate to 0, and of the minimum one to 255,
        x = 255 - base_ctab[0, iC[0]] >= base_ctab[0, iC[2]]
        dist = numpy.where(x, 255 - base_ctab[0, iC[0]], -base_ctab[0, iC[2]])
        # Pick, out of the two candidates, the coordinate with the longer available range
        iC = numpy.where(x, iC[0], iC[2])
        # Create the step size to run along that range, and make it to be exact
        step = dist / (n_parcels - 1)
        dist = step * n_parcels
        # Assign colors
        ctab_lbl[:, iC] = numpy.array(range(base_ctab[0, iC], base_ctab[0, iC] + dist, step), dtype='int')
        # Fix 0 and 255 as min and max RGB values
        ctab_lbl[:, :3][ctab_lbl[:, :3] < 0] = 0
        ctab_lbl[:, :3][ctab_lbl[:, :3] > 255] = 255
        # Calculate the resulting freesurfer magic number for each new RGB triplet
        ctab_lbl[:, 4] = numpy.array([self.annotation_service.rgb_to_fs_magic_number(base_ctab[iCl, :3]) for iCl in range(n_parcels)])
        return (names_lbl,ctab_lbl)

    def connectivity_geodesic_subparc(self, surf_path, annot_path, con_verts_idx, out_annot_path=None,
                                      labels=None, hemi=None, ctx=None,
                                      parc_area=100, con_sim_aff=1.0, geod_dist_aff=1.0, structural_connectivity_constraint=True,
                                      cras_path=None, ref_vol_path=None, consim_path=None,
                                      lut_path=os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt')):

        # Read the surface...
        surface = IOUtils.read_surface(surf_path, False)
        # ...and its annotation
        annotation = IOUtils.read_annotation(annot_path)
        # ...and get the corresponding labels:
        labels_annot = self.annotation_service.annot_names_to_labels(annotation.region_names, ctx, lut_path=lut_path)
        # Read the indexes of vertices neighboring tracts' ends voxels:
        con_verts_idx = numpy.load(con_verts_idx)
        # Set the target labels:
        labels, nLbl = self.annotation_service.read_input_labels(labels=labels, hemi=hemi)
        if con_sim_aff > 0:
            # Load voxel connectivity dissimilarity/distance matrix:
            con = numpy.load(consim_path).astype('single')
            # Convert it back to similarity cosine because we want to use arccos instead of 1-cos for distance:
            con = 1-con
            # Read the cras:
            cras = numpy.loadtxt(cras_path)
            # Get only the reference tdi_lbl volume's voxels that correspond to connectome nodes
            # and their ras xyz coordinates:
            vox, voxxzy = self.con_vox_in_ras(ref_vol_path)
        # Initialize the output:
        region_names = []
        region_color_table = []
        region_mapping = numpy.array(annotation.region_mapping)
        nL = 0
        # For every annotation name:
        for iL in range(len(annotation.region_names)):
            print str(iL) + ". " + annotation.region_names[iL]
            # Get the mask of the respective vertices
            iv_mask = annotation.region_mapping == iL
            # ...and their indexes
            iv, = numpy.where(iv_mask)
            nV = len(iv)
            # Find the corresponding label:
            lbl = labels_annot[iL]
            # If there are no associated vertices or if it is not one of the target labels:
            if nV == 0 or (lbl not in labels):
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[iL])
                region_color_table.append(annotation.regions_color_table[iL])
                # and change the output indices
                region_mapping[iv] = nL
                nL += 1
                print "Added "+annotation.region_names[iL]+" as it stands..."
                continue
            # Get the vertices and faces of this label:
            (verts_lbl, faces_lbl) = self.surface_service.extract_subsurf(surface.vertices, surface.triangles, iv_mask)
            # Compute distances among directly connected vertices
            dist = self.surface_service.vertex_connectivity(verts_lbl, faces_lbl, mode="sparse", metric='euclidean').astype('single')
            # Mask of label vertices that are neighbors of tract end voxels ("con"):
            iv_con = numpy.in1d(iv, con_verts_idx)
            # Calculate total area only of "con" surface:
            lbl_area = self.compute_surface_area(verts_lbl, faces_lbl, iv_con)
            print annotation.region_names[iL]+" total area receiving white matter tracts = " + str(lbl_area) + " mm2"
            # If no further parcellation is needed
            if lbl_area < 1.5*parc_area:
                # Just add this label to the new annotation as it stands:
                region_names.append(annotation.region_names[iL])
                region_color_table.append(annotation.regions_color_table[iL])
                # and change the output indices
                region_mapping[iv] = nL
                nL += 1
                print "Added " + annotation.region_names[iL] + " as it stands because its connectivity area is less than 1.5 times the target average parcel area"
                continue
            # Get all different (dis)connected components
            n_components, components, comp_area = self.connected_surface_components(verts_lbl,faces_lbl, dist,mask=iv_con)
            n_components=len(comp_area)
            print str(n_components)+" connected components in total of "+comp_area+"mm2 area, respectively"
            n_parcels=0
            parcels=-numpy.ones(components.shape,dtype='i')
            too_small_parcels=dict()
            for iC in range(n_components):
                i_comp_verts = components == iC
                n_comp_verts=numpy.sum(i_comp_verts)
                print "Treating connected surface component "+str(iC)+" of area "+str(comp_area[iC])+"mm2"
                if comp_area[iC]<=1.5*parc_area:
                    if comp_area[iC]>=0.1*[parc_area]:
                        parcels[i_comp_verts] = n_parcels
                        n_parcels+=1
                        print "Directly assigned to parcel "+str(n_parcels)+","
                        print "because its area is within the limits of [0.1, 1.5] times the target average parcel area"
                    else:
                        print "Too small surface component, i.e., less than 0.1 times the target average parcel area."
                        print "It will inherit the identity of the closest parcel in terms of euclidean distance."
                        too_small_parcels[iC]=i_comp_verts
                else:
                    print "Clustering will run for this surface component"
                    if structural_connectivity_constraint:
                        print "Forming the structural connectivity constraint matrix..."
                        connectivity = dist[i_comp_verts, :][:, i_comp_verts].astype('single')
                        connectivity[connectivity>0.0] = 1.0
                    else:
                        connectivity = None
                    # Initialize affinity matrix with zeros
                    affinity = numpy.zeros((n_comp_verts, n_comp_verts)).astype('single')
                    if con_sim_aff>0:
                        print "Computing the connectivity similarity affinity matrix..."
                        #...for this component, first normalized in [0,1] and then weighted by con_sim_aff:
                        affinity+=con_sim_aff*self.compute_consim_affinity(verts_lbl[i_comp_verts,:],vox,voxxzy,con,cras).astype('single')
                    if geod_dist_aff>0:
                        print "Computing the geodesic distance affinity matrix..."
                        # ...normalized in [0,1], and add it to the affinity metric with the correct weight
                        affinity += geod_dist_aff*self.compute_geodesic_dist_affinity(dist[i_comp_verts, :][:, i_comp_verts].todense()).astype('single')
                    print "Running clustering..."
                    clusters=self.run_clustering(affinity,parc_area,connectivity=connectivity)
                    clusters_labels=numpy.unique(clusters)
                    n_clusters=len(clusters_labels)
                    parcels[i_comp_verts] = clusters_labels+n_parcels
                    n_parcels+=n_clusters
                    print str(n_clusters) + ' parcels created for this component'
            parcel_labels=range(n_parcels)
            print "Dealing now with too small surface components..."
            for (iC,i_comp_verts) in too_small_parcels.items():
                comp_to_parcel_mindist=1000.0 #this is 1 meter long!
                assign_to_parcel=-1
                for iP in parcel_labels:
                    #TODO??!!: Alternatively, we could minimize the mean pacel distance with numpy. mean(.) here...
                    temp_dist=numpy.min(cdist(verts_lbl[i_comp_verts, :], verts_lbl[parcels==iP, :], 'euclidean'),axis=None)
                    if temp_dist<comp_to_parcel_mindist:
                        comp_to_parcel_mindist=temp_dist
                        assign_to_parcel=iP
                parcels[i_comp_verts]=assign_to_parcel
                print "Component "+str(iC)+" assigned to parcel "+str(assign_to_parcel)+" with a minimum euclidean distance of "+ str(comp_to_parcel_mindist)+"mm"
            # Create the new annotation for these sub-labels:
            (names_lbl,ctab_lbl)=self.gen_new_parcel_annots(parcel_labels,annotation.region_names[iL],annotation.regions_color_table[iL, numpy.newaxis])
            # Add the new label names
            region_names.append(names_lbl)
            #...and the new ctabs
            region_color_table.append(ctab_lbl)
            # Finally change the output indices
            # of the "con" vertices...
            region_mapping[iv] = nL + parcels
            for iP in range(n_parcels):
                iParcVerts=parcels==iP
                print 'parcel '+names_lbl[iP]+ 'of connectivity area ' + self.compute_surface_area(verts_lbl,faces_lbl,mask=numpy.logical_and(iParcVerts,iv_con)) + 'mm2'
                print "and of total area "+ self.compute_surface_area(verts_lbl,faces_lbl,mask=iParcVerts) + 'mm2'
            nL += n_parcels
        print "Write output annotation file"
        # Stack everything together
        region_color_table = numpy.vstack(region_color_table)
        region_names = numpy.hstack(region_names)
        # ...and write the annotation to a file
        if out_annot_path is None:
            out_annot_path = os.path.splitext(annot_path)[0] + str(parc_area) + ".annot"
        print out_annot_path
        IOUtils.write_annotation(out_annot_path, Annotation(region_mapping, region_color_table, region_names))
