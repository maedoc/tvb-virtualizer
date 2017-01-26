#!/bin/bash

#Configuration common for all processing streams:

#The path to the pipeline code
#CODE=/Users/dionperd/VirtualVEP/software/bnm-recon-tools/bin
CODE=/Users/dionperd/CBR/software/git/bnm-recon-tools/bin
export CODE
echo CODE=$CODE

#The path to the snapshot tool
SNAPSHOT=bnm.recon.qc.snapshot
export SNAPSHOT
echo SNAPSHOT=$SNAPSHOT

#Add utils in PYTHONPATH
PYTHONPATH="$PYTHONPATH:$CODE"
export PYTHONPATH
echo PYTHONPATH=$PYTHONPATH

#Subject codename, to be the name of the respective folder as well
SUBJECT=JUNG
export SUBJECT
echo SUBJECT=$SUBJECT
#SUBJECT=JUNG ./script

#Maybe make a copy of freesurfer subjects’ directory for each subject
# copy target to avoid modifying it
#CURRENT_SUBJECTS_DIR=/Users/dionperd/VEP/$SUBJECT
CURRENT_SUBJECTS_DIR=/Users/dionperd/CBR/VEP/$SUBJECT
if [ ! -d $CURRENT_SUBJECTS_DIR ]
then
    mkdir CURRENT_SUBJECTS_DIR
fi

SUBJS=fsaverage5
for s in $SUBJS
do
if [ ! -d $CURRENT_SUBJECTS_DIR/$s ]
then
    cp -r $SUBJECTS_DIR/$s $CURRENT_SUBJECTS_DIR
fi
done
SUBJECTS_DIR=$CURRENT_SUBJECTS_DIR
export SUBJECTS_DIR
echo SUBJECTS_DIR=$SUBJECTS_DIR

#The path to the subject's folder
SUBJ_DIR=$SUBJECTS_DIR/$SUBJECT
export SUBJ_DIR
echo SUBJ_DIR=$SUBJ_DIR

#The path to screenshots folder
FIGS=$SUBJ_DIR/figures
export FIGS
if [ ! -d $FIGS ]
then
    mkdir $FIGS
fi
echo FIGS=$FIGS


#INPUTS:

#The path to the input data
DATA=/Volumes/datasets/MRS/JUNG
export DATA
echo DATA=$DATA

#The path to T1
T1=$DATA/T1 #or $DATA/T1/T1_raw.nii.gz for nifti format
export T1
echo T1=$T1

#The path to T2
T2=$DATA/T2 #or $DATA/T2/T2_raw.nii.gz for nifti format
export T2
echo T2=$T2

#The path to FLAIR
FLAIR=$DATA/FLAIR #or $DATA/FLAIR/flair_raw.nii.gz for nifti format
export FLAIR
echo FLAIR=$FLAIR

#The path to DWI
DWI=$DATA/DWI #or $DATA/DWI/dwi_raw.nii.gz for nifti format
export DWI
echo DWI=$DWI

#The path to CT
CT=$DATA/CT/CT.nii #.gz
export CT
echo CT=$CT


#CO-REGISTRATION

#Co-registration method: default "flirt", else: "bbregister"
COREG_USE="flirt"
export COREG_USE
echo COREG_USE=$COREG_USE


#FREESURFER:

#mri folder location:
MRI=$SUBJ_DIR/mri
export MRI
echo MRI=$MRI

#T1 in RAS:
T1_RAS=$MRI/T1.nii.gz
export T1_RAS
echo T1_RAS=$T1_RAS

#surf folder location:
SURF=$SUBJ_DIR/surf
export SURF
echo SURF=$SURF

#label folder location:
LABEL=$SUBJ_DIR/label
export LABEL
echo LABEL=$LABEL

#aseg surfs folder location:
ASEG_SURFS=$SUBJ_DIR/surf/aseg_surfs
export ASEG_SURFS
if [ ! -d $ASEG_SURFS ]
then
    mkdir $ASEG_SURFS
fi
echo ASEG_SURFS=$ASEG_SURFS

#Cortical and sub-cortical segmentation folder:
SEGMENT=$SUBJ_DIR/segment
export SEGMENT
if [ ! -d $SEGMENT ]
then
    mkdir $SEGMENT
fi
echo SEGMENT=$SEGMENT

#Flags to depict the availability of T2 or FLAIR
T2_FLAG=no #'yes'
FLAIR_FLAG=no #'yes'

#Format of input
T1_INPUT_FRMT=dicom #or nifti
export T1_INPUT_FRMT
echo T1_INPUT_FRMT=$T1_INPUT_FRMT

#T2_INPUT_FRMT=dicom #or nifti
#export T2_INPUT_FRMT
#echo T2_INPUT_FRMT=$T2_INPUT_FRMT

#FLAIR_INPUT_FRMT=dicom #or nifti
#export FLAIR_INPUT_FRMT
#echo FLAIR_INPUT_FRMT=$FLAIR_INPUT_FRMT

#Number of openMP threads for Freesurfer:
OPENMP_THRDS=2
export OPENMP_THRDS
echo OPENMP_THRDS=$OPENMP_THRDS

DEFAULT_APARC="aparc"
export DEFAULT_APARC
echo DEFAULT_APARC=$DEFAULT_APARC


#TRANSFORMS:

#T1 cras path:
CRAS_PATH=$MRI/transforms/cras.txt
export CRAS_PATH
echo CRAS_PATH=$CRAS_PATH

#T1 native (mgz) vox2ras path:
T1_NAT_VOX2RAS_PATH=$MRI/transforms/vox2ras_nat.txt
export T1_NAT_VOX2RAS_PATH
echo T1_NAT_VOX2RAS_PATH=$T1_NAT_VOX2RAS_PATH

#T1 native (mgz) vox2ras-tkr path:
T1_NAT_VOX2RASTKR_PATH=$MRI/transforms/vox2rastkr_nat.txt
export T1_NAT_VOX2RASTKR_PATH
echo T1_NAT_VOX2RASTKR_PATH=$T1_NAT_VOX2RASTKR_PATH

#T1 ras (nii) vox2ras path:
T1_VOX2RAS_PATH=$MRI/transforms/vox2ras.txt
export T1_VOX2RAS_PATH
echo T1_VOX2RAS_PATH=$T1_VOX2RAS_PATH

#T1 ras (nii) vox2ras-tkr path:
T1_VOX2RASTKR_PATH=$MRI/transforms/vox2rastkr.txt
export T1_VOX2RASTKR_PATH
echo T1_VOX2RASTKR_PATH=$T1_VOX2RASTKR_PATH

#SEGMENTATION:

#Sub-parcellation area in mm2
SUBAPARC_AREA=200
export SUBAPARC_AREA
echo SUBAPARC_AREA=$SUBAPARC_AREA

#Sub-parcellations
for area in $SUBAPARC_AREA
do
SUBPARCS="aparc$area"
done
export SUBPARCS
echo SUBPARCS=$SUBPARCS

#Sub-segmentations
VOLS="aparc+aseg"
for area in $SUBAPARC_AREA
do
    VOLS="aparc$area+aseg$area $VOLS"  #add this to aseg$area when sub-aseg is ready
done
export VOLS
echo VOLS=$VOLS

#Segmentation mask methods: 'tdi','gwi','tdi+gwi','tdi*gwi'
SEGMENT_METHOD='tdi+gwi'
export SEGMENT_METHOD
echo SEGMENT_METHOD=$SEGMENT_METHOD

if [ "$SEGMENT_METHOD" = "tdi" ] || [ "$SEGMENT_METHOD" = "tdi+gwi" ] || [ "$SEGMENT_METHOD" = "tdi*gwi" ];
then
    #The path to tdi mask folder
    TDI=$SEGMENT/tdi
    export TDI
    if [ ! -d $TDI ]
    then
        mkdir $TDI
    fi
    echo TDI=$TDI

    #tdi threshold for volumes in terms of number of tracks
    TDI_THR=0.5
    export TDI_THR
    echo TDI_THR=$TDI_THR

fi
if [ "$SEGMENT_METHOD" = "gwi" ] || [ "$SEGMENT_METHOD" = "tdi+gwi" ] || [ "$SEGMENT_METHOD" = "tdi*gwi" ];
then
    #The path to gwi mask folder
    GWI=$SEGMENT/gwi
    export GWI
    if [ ! -d $GWI ]
    then
        mkdir $GWI
    fi
    echo GWI=$GWI

    #masking of volumes using grey-white matter interfaces
    #in terms of probability
    GWI_THR=0.1
    export GWI_THR
    echo GWI_THR=$GWI_THR
fi

#Set yes for sampling of the border/surface voxels of the regions only.
APARC_SURF=no
export APARC_SURF
echo APARC_SURF=$APARC_SURF

#number of tdi voxel neighbors to be considered during masking
VOL_VN=1
export VOL_VN
echo VOL_VN=$VOL_VN

#number of voxel neighbors to be considered during masking of connectivity surface voxels
SURF_VN=1
export SURF_VN
echo SURF_VN=$SURF_VN

#Labels' list of sub-cortical structures to segment
#7,19,20,27,46,55,56,59 ??
ASEG_LIST="8 10 11 12 13 16 17 18 26 47 49 50 51 52 53 54 58"
export ASEG_LIST
echo ASEG_LIST=$ASEG_LIST
#Left hemi plus Brain Stem
ASEG_LIST_lh="8 10 11 12 13 16 17 18 26"
export ASEG_LIST_lh
echo ASEG_LIST_lh=$ASEG_LIST_lh
#Right hemi
ASEG_LIST_rh="47 49 50 51 52 53 54 58"
export ASEG_LIST_rh
echo ASEG_LIST_rh=$ASEG_LIST_rh

#Sub-parcellation modes:
STRUCTURAL_CONNECTIVITY_CONSTRAINT=True
export STRUCTURAL_CONNECTIVITY_CONSTRAINT
echo STRUCTURAL_CONNECTIVITY_CONSTRAINT=$STRUCTURAL_CONNECTIVITY_CONSTRAINT
CON_SIM_AFF=1.0
export CON_SIM_AFF
echo CON_SIM_AFF=$CON_SIM_AFF
GEOD_DIST_AFF=1.0
export GEOD_DIST_AFF
echo GEOD_DIST_AFF=$GEOD_DIST_AFF

#DOWNSAMPLING:

#Decimating factor:
DECIM_FACTOR=0.1
export DECIM_FACTOR
echo DECIM_FACTOR=$DECIM_FACTOR

#Target subject for surface downsampling:
TRGSUBJECT=fsaverage5
#Custom, using mris_decimate:
#TRGSUBJECT=$SUBJECT-RESAMP_$DECIM_FACTOR
export TRGSUBJECT
echo TRGSUBJECT=$TRGSUBJECT

#TRACTOGRAPHY:

#dmr folder location:
DMR=$SUBJ_DIR/dmr
if [ ! -d $DMR ]
then
mkdir $DMR
fi
export DMR
echo DMR=$DMR

#Number of  threads for Mrtrix3:
MRTRIX_THRDS=2
export MRTRIX_THRDS
echo MRTRIX_THRDS=$MRTRIX_THRDS

#Format of input
DWI_INPUT_FRMT=dicom #or nifti
export DWI_INPUT_FRMT
echo DWI_INPUT_FRMT=$DWI_INPUT_FRMT

#Reversed scanning?
DWI_REVERSED=no #yes
export DWI_REVERSED
echo DWI_REVERSED=$DWI_REVERSED

#Scanning direction
DWI_PE_DIR=ap
export DWI_PE_DIR
echo DWI_PE_DIR=$DWI_PE_DIR

#MULTI SHELL flag
DWI_MULTI_SHELL=no
export DWI_MULTI_SHELL
echo DWI_MULTI_SHELL=$DWI_MULTI_SHELL

#Number of streamlines for tractography
STRMLNS_NO=25M
export STRMLNS_NO
echo STRMLNS_NO=$STRMLNS_NO

#Number of streamlines for SIFT filter
STRMLNS_SIFT_NO=5M
export STRMLNS_SIFT_NO
echo STRMLNS_SIFT_NO=$STRMLNS_SIFT_NO

#Maximum length of streamlines for tractography
STRMLNS_MAX_LEN=250
export STRMLNS_MAX_LEN
echo STRMLNS_MAX_LEN=$STRMLNS_MAX_LEN

#Step for tractography
STRMLNS_STEP=0.5
export STRMLNS_STEP
echo STRMLNS_STEP=$STRMLNS_STEP

#Volumetric vs surface connectome generation flag
CONNECTOME_MODE=surf #vol
export CONNECTOME_MODE
echo CONNECTOME_MODE=$CONNECTOME_MODE

#Volume voxel edge length (in mm) in case of volumetric tractography
VOX=3
export VOX
echo VOX=$VOX

#fs_default.txt location
FS_DEFAULT=/Users/dionperd/VirtualVEP/software/mrtrix3/src/connectome/tables/fs_default.txt
#FS_DEFAULT=/Users/dionperd/CBR/software/git/mrtrix3/src/connectome/tables/fs_default.txt
export FS_DEFAULT
echo FS_DEFAULT=$FS_DEFAULT


#Lead fields:

#BEM folder location:
BEM=$SUBJ_DIR/bem
export BEM
echo BEM=$BEM

#Format of input
CT_INPUT_FRMT=nifti #or dicom
export CT_INPUT_FRMT
echo CT_INPUT_FRMT=$CT_INPUT_FRMT

CT_ELEC_INTENSITY_TH=2000
export CT_ELEC_INTENSITY_TH
echo CT_ELEC_INTENSITY_TH=$CT_ELEC_INTENSITY_TH

#SEEG
#TODO: quite similar for EEG and MEG...
#SEEG folder location:
SEEG=$SUBJ_DIR/seeg
export SEEG
if [ ! -d $SEEG ]
then
mkdir$SEEG
fi
echo SEEG=$SEEG

#SEEG sensor file location:
SEEG_FILE=$SEEG/SEEG_sensors.txt
export SEEG_FILE
echo SEEG_FILE=$SEEG_FILE

#SEEG sensors' positions location:
SEEG_XZY=$SEEG/seeg_xyz.txt
export SEEG_XZY
echo SEEG_XZY=$SEEG_XZY


