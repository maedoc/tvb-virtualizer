#!/bin/bash

pushd $DMR

#IF surface parcellation generation:
if [ "$CONNECTOME_MODE" = "surf" ]
then

    # Volumes for connectome generation should be provided as arguments.
    #vols=$*

    #Generate labels for the default parcellation
    #echo " compute labels”
    conf=/usr/local/mrtrix3/src/connectome/config/fs_default.txt
    labelconfig ./aparc+aseg-in-d.nii.gz $conf ./aparc_lbl.nii.gz -lut_freesurfer ${FREESURFER_HOME/FreeSurferColorLUT.txt

    #Generate labels for sub-parcellations (LOOP)
    for vol in $vols
    do
        python -c "import reconutils; reconutils.simple_label_config('./$vol-in-d.nii.gz','/$vol_lbl.nii.gz')"
    done

    #Generate track counts and mean track lengths for all parcellations
    assignment="-assignment_radial_search 2" #make a ball of 2 mm and look for the nearest node on the gmwgmi surface
    for vol in $vols
    do
        for metric in count meanlength
        do
        tck2connectome $STRMLNS_SIFT_NO.tck ./$vol_lbl.nii.gz $assignment ./$vol_counts$STRMLNS_SIFT_NO.csv
        tck2connectome $STRMLNS_SIFT_NO.tck ./$vol_lbl.nii.gz $assignment -scale_length -stat_edge mean ./$volc_mean_tract_lengths$STRMLNS_SIFT_NO.csv
        done
    done

else

    #Get volume labels:
    tckmap ./$STRMLNS_SIFT_NO.tck ./tdi_ends.mif -vox 5 -ends_only #vox: size of bin

    #Visual check
    mrview ./t1-in-d.nii.gz -overlay.load ./tdi_ends..mif
    mrconvert ./tdi_ends.mif ./tdi_ends.nii

    #Label:
    python -c "import reconutils; reconutils.label_vol_tdi('./tdi_ends.nii','./tdi_lbl.nii')"

    #Generate track counts and mean track lengths
    tck2connectome -assignement_end_voxels ./$STRMLNS_SIFT_NO.tck ./tdilbl.nii ./counts$STRMLNS_SIFT_NO.csv
    tck2connectome -assignement_end_voxels ./$STRMLNS_SIFT_NO.tck ./tdilbl.nii -scale_length -stat_edge mean ./mean_tract_lengths$STRMLNS_SIFT_NO.csv

fi

popd