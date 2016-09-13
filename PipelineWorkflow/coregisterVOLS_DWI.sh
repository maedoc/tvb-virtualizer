#!/bin/bash

#FLIRT co-registration of volumes with DWI

# Parcellations to co-register should be provided as arguments.
#vols=$*

pushd $DMR

for vol in $vols
do

    #Not really necessary if we have already created .nii.gz files at each previous step:
    mri_convert $MRI/$vol.mgz $MRI/$vol.nii.gz --out_orientation RAS -rt nearest

    fslreorient2std $MRI/$vol.nii.gz $MRI/$vol-reo.nii.gz
    mv $MRI/$vol-reo.nii.gz $MRI/$vol.nii.gz

    flirt -applyxfm -in $MRI/$vol.nii.gz -ref ./b0.nii.gz -out ./$vol-in-d.nii.gz -init ./t2d.mat -interp nearestneighbour

    #Visual check (interactive):
    #-mode 2 is the view, you need & to allow more windows to open
    mrview ./b0.nii.gz -overlay.load ./$vol-in-d.nii.gz -overlay.opacity 0.3 -mode 2 &

    #Visual check (screenshot):
    freeview -v ./t1-in-d.nii.gz ./b0.nii.gz:colormap=heat ./$vol-in-d.nii.gz:colormap=jet
done

popd
