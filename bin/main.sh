#!/bin/bash


#Pre-configure
source activate python2.7.3
cd /Users/dionperd/VirtualVEP/software/bnm-recon-tools/bin
source ./config.sh


#Step 1: Recon All and post-Recon All
#->It needs T1 dicoms or niftii file
sh $CODE/reconALL.sh
source $CODE/postreconALL.sh
#<-It returns all surfaces and volumes...

# Generate surfaces for subcortical structures
$CODE/aseg2srf -s ${SUBJECT}


#Now, for Steps 2 we split to three parallel streams:

#Step 2.1: Starting with generation of aseg surfs, continuing with downsampling, and finally, head and source model computations

#->It needs aparc+aseg.mgz and norm.mgz
sh $CODE/gen_aseg_surf.sh
#<-It returns l/rh.aseg surfaces and l/rh.aseg.annot
#->It needs aparc, surfs (pial, white, inflated), annotations and T1.{mgz,nii.gz}, as well as aseg surfs and annotations
#!!Source in order to be able to export/modify the environment variable $TRGSUBJECT
source $CODE/resamp-surf.sh
#<-It returns all surfs and annotations downsampled

#Step 2.1.1: resampling default parcellation annotations
#->It needs annotations and the environment variable $TRGSUBJECT modified by the previous step
#TODO!: downsampling of aseg surf annotations!
sh $CODE/resamp-annot.sh
#<-It returns all annotations dowsampled

#Step 2.1.2: Head and source model computations
#->It needs all downsampled surfaces
sh head_model.sh
#<-It returns head.mat head-inv.mat and head_model.{geom,cond}
#->It needs head_model.{geom,cond} and downsampled white (or pial unti recently) surfaces
#TODO!: the python function that will generate the sub-cortical sources, either as volume dipoles per voxel (??arbitrary orienation or orientation based on the normal of the nearest aseg surface vertex??), or as surface dipols on the aseg surfaces with the normal orientation
sh source_model.sh
#<-It returns cortical-$h.{tri,ssm}, cortical-$h.{dip,dsm}, subcortical-$h.{dip,dsm}


#Step 2.2: DWI processing and T1-DWI co-registration up to the connectome generation for the default parcellation

#->It needs DWI dicoms or niftii file
sh $CODE/dwi_preproc.sh
#<-It returns b0.nii.gz, mask.mif, and dwi.mif

#->It needs T1 and b0.nii.gz:
sh $CODE/coregisterT1_DWI.sh
#<-It returns t2d, d2t transforms and b0-in-t1.nii.gz and T1-in-d.nii.gz

#Step 2.2.1: co-registration of default parcellation and DWI
#->It needs aparc+aseg, b0.nii.gz and t2d:
sh $CODE/coregisterVOLS_DWI.sh
#<-It returns aparc+aseg-in-d.nii.gz

#Step 2.2.2: Tractography
#->It needs dwi.mif, and t1-in-d.nii.gz, mask.mif and b0.nii.gz
sh $CODE/act_fod.sh
#<-It returns wm_fod.mif, 5tt.mif and gmwmi.mif
#->It needs wm_fod.mif, 5tt.mif and gmwmi.mif
sh $CODE/tractography.sh
#<-It returns $STRMLNS_NO.tck and $STRMLNS_SIFT_NO, as well as tdi_ends.nii.gz (for VOX = 1.0 mm)

#Step 2.2.1: The two steps getting together now to generate the connectome for the default parcellations
#->It needs $STRMLNS_SIFT_NO and aparc+aseg-in-d.nii.gz, as well as $FREESURFER_HOME/FreeSurferColorLUT.txt
sh $CODE/connectome_gen_parcel.sh
#<-It returns $vol-counts$STRMLNS_SIFT_NO.csv, $vol-mean_tract_lengths$STRMLNS_SIFT_NO.csv, as well as aparc+aseg-in-d_lbl.nii.gz
#Step 2.2.2: The two steps getting together now to generate the connectome for in a volume-wise manner in order to be used for segmentation
#->It needs $STRMLNS_SIFT_NO
sh $CODE/connectome_gen_vol.sh
#<-It returns vol-counts$STRMLNS_SIFT_NO-v$VOX.{csv,npy} and vol-mean_tract_lengths$STRMLNS_SIFT_NO-v$VOX.{csv,npy}, as well as tdi_ends-v$VOX.nii.gz and tdi_lbl-v$VOX.nii.gz

#Step 2.3: CT scan
#->It needs CT scan (dicoms or niftii) and T1, brain, aparc+aseg
sh $CODE/seeg-ct.sh
#<-It returns seeg_xyz.txt


#Step 3.1: Sub-parcellations and sub-segmentations
sh $CODE/segment.sh

#Step 3.2: Sensor model and lead-field generation for default parcellation
#->It needs seeg_xyz.txt, head_model.{geom,cond}, source models ({cortical subcortical}-$h.dsm)
sh $CODE/sensor_model.sh
#<-It returns sensor models (seeg.h2ipm) and sensor->source models (seeg-{cortical subcortical}-$h.ds2ipm)
#->It needs head-inv.mat, source models (cortical.dsm, subcortical.dsm), sensor->source models (seeg-cortical-$h.ds2ipm, seeg-subcortical-$h.ds2ipm) and sensor models (seeg.h2ipm)
sh $CODE/lead_field_model.sh
#TODO!: concatenation of seeg-cortical-$h_gain.mat and seeg-subcortical-$h_gain.mat into a single seeg_gain.mat
#<-It returns seeg_gain.mat
#->It needs seeg_gain.mat, aparc+aseg, seeg_xyz.txt
#TODO!: the actual python function that will average the seeg_gain given a parcellation
sh $CODE/lead_field_gen.sh
#<-It returns seeg_lead_field.mat


#Steps 4: Repeat for all parcellations

#Step 4.1 Connectome generations for the additional parcellations
#similar to step 2.2.1

#Step 4.2: Lead field generation of all parcellations
#similar to step to 3.2

#Step 4.3: Downsampling of all parcellations' annotations
#similar to step to 2.1.1

