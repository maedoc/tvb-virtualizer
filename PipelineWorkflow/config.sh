#!/bin/bash

#Configuration common for all processing streams:

#Subject codename, to be the name of the respective folder as well
SUBJECT=JUNG
export SUBJECT
echo $SUBJECT
#SUBJECT=JUNG ./script

#Maybe make a copy of freesurfer subjects’ directory for each subject
# copy target to avoid modifying it
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
echo $SUBJECTS_DIR

#The path to the subject's folder
SUBJ_DIR=$SUBJECTS_DIR/$SUBJECT
export SUBJ_DIR
echo $SUBJ_DIR

#The path to the input data
DATA=/Volumes/datasets/MRS/JUNG
export DATA
echo $DATA

#The path to T1
T1=$DATA/T1 #or $DATA/T1/T1_raw.nii.gz for nifti format
export T1
echo $T1

#The path to T2
T2=$DATA/T2 #or $DATA/T2/T2_raw.nii.gz for nifti format
export T2
echo $T2

#The path to FLAIR
FLAIR=$DATA/FLAIR #or $DATA/FLAIR/flair_raw.nii.gz for nifti format
export FLAIR
echo $FLAIR

#The path to DWI
DWI=$DATA/DWI #or $DATA/DWI/dwi_raw.nii.gz for nifti format
export DWI
echo $DWI

#The path to CT
CT=$DATA/CT/CT.nii.gz
export CT
echo $CT

#The path to the pipeline code
CODE=/Users/dionperd/CBR/software/git/bnm-recon-tools/PipelineWorkflow
export CODE
echo $CODE

#Add utils in PYTHONPATH
PYTHONPATH="$PYTHONPATH:$CODE"
export PYTHONPATH
echo $PYTHONPATH

#DMR folder location:
DMR=$SUBJ_DIR/dmr
if [ ! -d $DMR ]
then
    mkdir $DMR
fi
export DMR
echo $DMR

#MRI folder location:
MRI=$SUBJ_DIR/mri
export MRI
echo $MRI

#BEM folder location:
BEM=$SUBJ_DIR/bem
export BEM
echo $BEM


#Freesurfer:

#Flags to depict the availability of T2 or FLAIR
T2_FLAG=no #'yes'
FLAIR_FLAG=no #'yes'

#Format of input
T1_INPUT_FRMT=dicom #or nifti
export T1_INPUT_FRMT
echo $T1_INPUT_FRMT

#T2_INPUT_FRMT=dicom #or nifti
#export T2_INPUT_FRMT
#echo $T2_INPUT_FRMT

#FLAIR_INPUT_FRMT=dicom #or nifti
#export FLAIR_INPUT_FRMT
#echo $FLAIR_INPUT_FRMT

#Number of openMP threads for Freesurfer:
OPENMP_THRDS=2
export OPENMP_THRDS
echo $OPENMP_THRDS

#Sub-parcellation area in mm2
SUBAPARC_AREA=100
export SUBAPARC_AREA
echo $SUBAPARC_AREA

#Target subject for surface downsampling:
TRGSUBJECT=fsaverage5
export SUBAPARC_AREA
echo $TRGSUBJECT


#Tractography:

#Number of  threads for Mrtrix3:
MRTRIX_THRDS=2
export MRTRIX_THRDS
echo $MRTRIX_THRDS

#Format of input
DWI_INPUT_FRMT=dicom #or nifti
export DWI_INPUT_FRMT
echo $DWI_INPUT_FRMT

#Reversed scanning?
DWI_REVERSED=no #yes
export DWI_REVERSED
echo $DWI_REVERSED

#Scanning direction
DWI_PE_DIR=ap
export DWI_PE_DIR
echo $DWI_PE_DIR

#MULTI SHELL flag
DWI_MULTI_SHELL=no
export DWI_MULTI_SHELL
echo $DWI_MULTI_SHELL

#Number of streamlines for tractography
STRMLNS_NO=25M
export STRMLNS_NO
echo $STRMLNS_NO

#Number of streamlines for SIFT filter
STRMLNS_SIFT_NO=5M
export STRMLNS_SIFT_NO
echo $STRMLNS_SIFT_NO

#Maximum length of streamlines for tractography
STRMLNS_MAX_LEN=250
export STRMLNS_MAX_LEN
echo $STRMLNS_MAX_LEN

#Step for tractography
STRMLNS_STEP=0.5
export STRMLNS_STEP
echo $STRMLNS_STEP

#Volumetric vs surface connectome generation flag
CONNECTOME_MODE=surf #vol
export CONNECTOME_MODE
echo $CONNECTOME_MODE

#Volume voxel edge length in case of volumetric tractography
TRCT_VXL_EDGE=5
export TRCT_VXL_EDGE
echo $TRCT_VXL_EDGE


#Lead fields:
#Format of input
CT_INPUT_FRMT=nifti #or nifti
export CT_INPUT_FRMT
echo $CT_INPUT_FRMT


