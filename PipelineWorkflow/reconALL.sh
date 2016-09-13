#!/bin/bash

#T1 input pre-processing
if [ "$T1_INPUT_FRMT" = "dicom" ]
then
    mrconvert $DATA/T1 $DATA/t1_raw.nii.gz
fi
#ENDIF

#Freesurfer T1 processing
recon-all -s ${SUBJECT} -i $DATA/t1_raw.nii.gz -all -parallel -openmp $OPENMP_THRDS

#Additional processing if T2 and/or FLAIR is available
if [ "$T2_FLAG" = "yes" ]
then
    if [ "$T2_INPUT_FRMT" = "dicom" ]
    then
        mrconvert $DATA/T2 $DATA/t2_raw.nii.gz
    fi
    recon-all s ${SUBJECT} -T2 $DATA/t2_raw.nii.gz -T2pial -autorecon3 -parallel -openmp $OPENMP_THRDS
fi

if [ "$FLAIR_FLAG" = "yes" ]
then
    if [ "$FLAIR_INPUT_FRMT" = "dicom" ]
    then
        mrconvert $DATA/FLAIR $DATA/flair_raw.nii.gz
    fi
    recon-all s ${SUBJECT} -FLAIR $DATA/flair_raw.nii.gz -FLAIRpial -autorecon3 -parallel -openmp $OPENMP_THRDS
fi

#This could be made already here:
#Generate nifti file with good orientation
#mri_convert $MRI/aparc+aseg.mgz $MRI/aparc+aseg.nii.gz --out_orientation RAS -rt nearest

#TODO: Visual checks for brain, pial, white, aparc+asseg
#