#!/bin/bash

#FLIRT co-registration of gmwmi with aseg

vol=aparc+aseg

pushd $SEGMENT


#Volume workflow:


if [ "$SEGMENT_METHOD" = "tdi" ] || [ "$SEGMENT_METHOD" = "tdi+gwi" ] || [ "$SEGMENT_METHOD" = "tdi*gwi" ];
then
    pushd $TDI

    if [ -e $DMR/tdi_ends-v1.nii.gz ]
    then
        tdiends=$DMR/tdi_ends-v1.nii.gz
    else
        #Get volume labels:
        tckmap $DMR/$STRMLNS_SIFT_NO.tck $DMR/tdi_ends-v1.mif -vox 1.0 -ends_only -template $DMR/b0.nii.gz -force
        mrconvert $DMR/tdi_ends-v1.mif $DMR/tdi_ends-v1.nii.gz -force
        tdiends=$DMR/tdi_ends-v1.nii.gz
    fi

    #Get the transform of tdi_ends in T1 space
    #QUESTION! Can we afford the loss of accuracy due to volume resampling from diffusion space and resolution to those of T1?

    if [ "$COREG_USE" = "flirt" ]
    then
        flirt -applyxfm -in $tdiends -ref $MRI/T1.nii.gz -init $DMR/d2t.mat -out ./tdi_ends-v1-in-t1.nii.gz
    else
        mri_vol2vol --mov $tdiends --targ $MRI/T1.mgz --o ./tdi_ends-v1-in-t1.mgz --reg ./d2t.reg
        mri_convert ./tdi_ends-v1-in-t1.mgz ./tdi_ends-v1-in-t1.nii.gz -out_orientation ras
        rm ./tdi_ends-v1-in-t1.mgz
    fi

    #QC snapshot
    python -m $SNAPSHOT --snapshot_name tdi-in-T1 2vols $MRI/T1.nii.gz ./tdi_ends-v1-in-t1.nii.gz

    #...and binarize it to create a tdi mask with a threshold equal to the number of tracks
    mri_binarize --i ./tdi_ends-v1-in-t1.nii.gz --min $TDI_THR --o ./tdi_mask.nii.gz

    #QC snapshot
    python -m $SNAPSHOT --snapshot_name tdimask-in-T1 2vols $MRI/T1.nii.gz ./tdi_mask.nii.gz

    popd
fi

if [ "$SEGMENT_METHOD" = "gwi" ] || [ "$SEGMENT_METHOD" = "tdi+gwi" ] || [ "$SEGMENT_METHOD" = "tdi*gwi" ];
then
    pushd $GWI

    #Create a mask of vol's white matter
    mri_binarize --i $MRI/$vol.nii.gz --all-wm --o ./wm.nii.gz
    #is this really needed?:
    mri_convert ./wm.nii.gz ./wm.nii.gz --out_orientation RAS -rt nearest
    ##!!Probably not necesary anymore
    #fslreorient2std ./wm.nii.gz ./wm-reo.nii
    #mv ./wm-reo.nii.gz ./wm.nii.gz

    #gmwmi:
    #Anatomically constraint spherical deconvolution
    #5ttgen fsl $MRI/T1.nii.gz ./5tt-in-t1.mif -force #if a brain mask is already applied: -premasked
    5tt2gmwmi ./5tt-in-t1.mif ./gmwmi-in-t1.mif -nthreads $MRTRIX_THRDS -force
    mrconvert ./gmwmi-in-t1.mif ./gmwmi-in-t1.nii.gz -force

    #Scale gmwmi-in-T1 in 0-256 for visualization reasons
    mris_calc ./gmwmi-in-t1.nii.gz mul 256
    mri_convert ./out.mgz ./gmwmi-in-t1-256.nii.gz --out_orientation RAS -rt nearest
    rm ./out.mgz

    #Visual checks
    #(interactive):
    #freeview -v $MRI/T1.nii ../$vol.nii.gz ./gmwmi-in-t1-256.nii:opacity=0.5
    #(screenshot):
    #freeview -v $MRI/T1.nii.gz ../$vol.nii.gz ./gmwmi-in-t1-256.nii.gz:opacity=0.5 -ss $FIGS/gmwmi-in-t1-$vol.png

    #Resample and register gmwmi with aparc+aseg
    #tkregister2 --mov ./gmwmi-in-t1.nii.gz --targ $MRI/T1.nii.gz --reg ./resamp_gw-in-t1.dat --noedit --regheader
    #Resample gmwmi in aseg space [256 256 256]
    #mri_vol2vol --mov ./gmwmi-in-t1.nii.gz --targ $MRI/T1.nii.gz --o ./gmwmi-in-t1-resamp.nii.gz --reg ./resamp_gw-in-t1.dat
    mri_vol2vol --mov ./gmwmi-in-t1.nii.gz --targ $MRI/T1.nii.gz --o ./gmwmi-in-t1-resamp.nii.gz --regheader
    #Renormalize gmwmi in the [0.0, 1.0] interval
    mris_calc ./gmwmi-in-t1-resamp.nii.gz norm
    mri_convert ./out.mgz ./gmwmi-in-t1-resamp-norm.nii.gz --out_orientation RAS -rt nearest
    #rm ./out.mgz
    #...and binarize it to create a gmwmi mask

    #QC snapshot
    python -m $SNAPSHOT --snapshot_name gmwmi-in-T1 2vols $MRI/T1.nii.gz ./gmwmi-in-t1-resamp-norm.nii.gz

    mri_binarize --i ./gmwmi-in-t1-resamp-norm.nii.gz --min $GWI_THR --o ./gmwmi-in-t1-bin.mgz
    mri_convert ./gmwmi-in-t1-bin.mgz ./gmwmi-in-t1-bin.nii.gz --out_orientation RAS -rt nearest
    ##!!Probably not necesary anymore
    #fslreorient2std ./gmwmi-in-t1-bin.nii.gz ./gmwmi-in-t1-bin-reo.nii.gz
    #mv ./gmwmi-in-t1-bin-reo.nii.gz ./gmwmi-in-t1-bin.nii.gz

    #QC snapshot
    python -m $SNAPSHOT --snapshot_name gmwmi-bin-in-T1 2vols $MRI/T1.nii.gz ./gmwmi-in-t1-bin.nii.gz

    #Visual checks
    #(interactive):
    #freeview -v $MRI/T1.nii.gz ../$vol.nii.gz ./gmwmi-in-t1-bin.nii.gz:opacity=0.5
    #(screenshot):
    #freeview -v $MRI/T1.nii.gz ../$vol.nii.gz ./gmwmi-in-t1-bin.nii.gz:opacity=0.5 -ss $FIGS/gmwmi-bin-in-$vol.png
    #source snapshot.sh 3vols $MRI/T1.nii.gz ../$vol.nii.gz ./gmwmi-in-t1-bin.nii.gz

    #Create a mask by combining gmwmi-bin and wm masks with logical OR
    mris_calc ./gmwmi-in-t1-bin.nii.gz or ./wm.nii.gz
    mri_convert ./out.mgz ./gwi_mask.nii.gz --out_orientation RAS -rt nearest
    rm ./out.mgz
    ##!!Probably not necesary anymore
    #fslreorient2std ./gwi_mask.nii.gz ./gwi_mask-reo.nii.gz
#   mv ./gwi_mask-reo.nii.gz ./gwi_mask.nii.gz

    #QC snapshot
    python -m $SNAPSHOT --snapshot_name gwimask-in-T1 2vols $MRI/T1.nii.gz ./gwi_mask.nii.gz

    popd
fi

#Create the final mask

if [ "$SEGMENT_METHOD" = "tdi" ]
then
    cp $TDI/tdi_mask.nii.gz ./mask-$SEGMENT_METHOD.nii.gz
elif [ "$SEGMENT_METHOD" = "tdi" ]
then
    cp $GWI/gwi_mask.nii.gz ./mask-$SEGMENT_METHOD.nii.gz
elif [ "$SEGMENT_METHOD" = "tdi+gwi" ] || [ "$SEGMENT_METHOD" = "tdi*gwi" ]
then
    if [ "$SEGMENT_METHOD" = "tdi+gwi" ]
    then
        mris_calc $TDI/tdi_mask.nii.gz or $GWI/gwi_mask.nii.gz
    else
        mris_calc $TDI/tdi_mask.nii.gz and $GWI/gwi_mask.nii.gz
    fi
    mri_convert ./out.mgz ./mask-$SEGMENT_METHOD.nii.gz --out_orientation RAS -rt nearest
    rm ./out.mgz
    ##!!Probably not necesary anymore
    #fslreorient2std ./mask-$SEGMENT_METHOD.nii.gz ./mask-$SEGMENT_METHOD-reo.nii.gz
    #mv ./mask-$SEGMENT_METHOD-reo.nii.gz ./mask-$SEGMENT_METHOD.nii.gz
fi
#QC snapshot
python -m $SNAPSHOT --snapshot_name mask-$SEGMENT_METHOD-in-T1 2vols $MRI/T1.nii.gz ./mask-$SEGMENT_METHOD.nii.gz


#If segmentation is performed via parcellation of the surface, maybe it is not necessary to work on the surface voxels of aparc+aseg volume. In this case we directly mask the aparc+aseg.
if [ "$APARC_SURF" = "yes" ]
then
    #Apply the mask to the border voxels

    #Get the voxels that lie at the external surface (or border) of the target volume structures:

    #Using my python code:
    #python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.vol_to_ext_surf_vol('$MRI/$vol.nii.gz',labels='$ASEG_LIST',ctx='lh rh',out_vol_path='./$vol-surf.nii.gz',labels_surf=None,labels_inner='0')"
    #flirt -applyxfm -in ./$vol-surf.nii -ref $DMR/b0.nii.gz -out ./$vol-surf-in-d.nii.gz -init $DMR/t2d.mat -interp nearestneighbour

    #Using freesurfer:
    #Create a zero mask template:
    mris_calc $MRI/T1.mgz mul 0
    #For every surface:
    for srf in white aseg
    do
        for h in lh rh
        do
            #Sample the surface to the T1 volume
            mri_surf2vol --mkmask --hemi $h --surf $srf --identity $SUBJECT --template $MRI/T1.mgz --o ./$h.$srf-surf-mask.mgz --vtxvol ./$h.$srf-surf-map.mgz

            #And use logical OR to add the result to the mask
            mris_calc ./out.mgz or ./$h.$srf-surf-mask.mgz

        done
    done
    #Now mask the parcellation volume with this surface-voxel mask to get the border voxels of each label
    mv ./out.mgz ./$vol-surf-mask.mgz
    mris_calc $MRI/$vol.mgz masked ./$vol-surf-mask.mgz
    mv ./out.mgz ./$vol-surf.mgz

    #Convert to RAS
    for v in ./$vol-surf-mask ./$vol-surf
    do
        mri_convert ./$v.mgz ./$v.nii.gz --out_orientation RAS -rt nearest
        ##!!Probably not necesary anymore
        #fslreorient2std ./$v.nii.gz ./$v-reo.nii.gz
        #mv ./$v-reo.nii.gz ./$v.nii.gz
    done

    #Set the name of the parcellation mask to mask
    #QC snapshot
    python -m $SNAPSHOT --snapshot_name $vol-surf 2vols $MRI/T1.nii.gz ./$vol-surf.nii.gz

else
    #Apply the mask to the whole aparc+aseg, not only to the border voxels
    mask_this_vol=$MRI/$vol
fi


#Apply the mask to the parcellation volume now to get the parcellation volume of the regions that white matter touches. i.e., that survive the mask constructed above:
#Using my python code:
#python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.mask_to_vol('$mask_this_vol.nii.gz','./mask-$SEGMENT_METHOD.nii.gz','./$vol-mask.nii.gz',labels='$ASEG_LIST',ctx='lh rh',vol2mask_path=None,vn=$VOL_VN,th=1,labels_mask=None,labels_nomask='0')"

#Using freesurfer:
mris_calc $mask_this_vol.nii.gz masked ./mask-$SEGMENT_METHOD.nii.gz
mri_convert ./out.mgz ./$vol-mask.nii.gz --out_orientation RAS -rt nearest
rm ./out.mgz
##!!Probably not necesary anymore
#fslreorient2std ./$vol-mask.nii.gz ./$vol-mask-reo.nii
#mv ./$vol-mask-reo.nii.gz ./$vol-mask.nii.gz

#QC snapshot
python -m $SNAPSHOT --snapshot_name $vol-mask 2vols $MRI/T1.nii.gz ./$vol-mask.nii.gz

#Get final masked surfaces by sampling the surface with the mask-surviving voxels of the parcellation volume:
#Cortical:
#Give an empty list for add_lbl, if you want cerebral white matter to be masked out
for h in lh rh
do
    python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.sample_vol_on_surf('$SURF/$h.white','./$vol-mask.nii.gz','$LABEL/$h.aparc.annot','./$h.white-mask','$CRAS_PATH',add_string='ctx-'+'$h'+'-',vertex_neighbourhood=int('$SURF_VN'), add_lbl=[2,41], lut_path='$FREESURFER_HOME/FreeSurferColorLUT.txt')"
done
#Sub-cortical:
for h in lh rh
do
    python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.sample_vol_on_surf('$SURF/$h.aseg','./$vol-mask.nii.gz','$LABEL/$h.aseg.annot','./$h.aseg-mask','$CRAS_PATH',vertex_neighbourhood=int('$SURF_VN'),lut_path='$FREESURFER_HOME/FreeSurferColorLUT.txt')"
done

#Quality control snapshots:
python -m $SNAPSHOT --center_surface --snapshot_name segment_masked-surfs-in-T1 vol_surf $MRI/T1.nii.gz ./{lh,rh}.{white,aseg}-mask
for h in lh rh
do
    for srf in white aseg
    do
        python -m $SNAPSHOT --center_surface --snapshot_name segment_masked-$srf-$h-in-T1 vol_surf $MRI/T1.nii.gz $SURF/$h.$srf ./$h.$srf-mask
        python -m $SNAPSHOT --center_surface --snapshot_name segment-mask-$srf-annot-$h surf_annot ./$h.$srf-mask ./$h.$srf-mask.annot
    done

done

#If connectivity similarity is one of the criteria for parcellation
if [[ $SUBAPARC_MODE == *"con"* ]]
then

    #Sample the connectome volume to T1 space
    if [ "$COREG_USE" = "flirt" ]
    then
        flirt -applyxfm -in $DMR/tdi_lbl-v$VOX.nii.gz -ref $MRI/T1.nii.gz -init $DMR/d2t.mat -out ./tdi_lbl-v$VOX-in-t1.nii.gz -interp nearestneighbour
    else
        mri_vol2vol --mov $DMR/tdi_ends-v$VOX.nii.gz --targ $MRI/T1.mgz --o ./tdi_ends-v$VOX-in-t1.mgz --reg $DMR/d2t.reg --nearest
        mri_convert ./tdi_ends-v$VOX-in-t1.mgz ./tdi_ends-v$VOX-in-t1.nii.gz --out_orientation ras
    fi

    #Quality control snapshot depending on whether VOX resolution is 1, and on the existence of tdi_ends-v1 or not
    if [ -e ./tdi_ends-v1-in-t1.nii.gz ]
    then
        if [ $VOX != 1 ]
            python -m $SNAPSHOT --snapshot_name tdilbl-tdi-in-T1 3vols $MRI/T1.nii.gz ./tdi_lbl-v$VOX-in-T1nii.gz ./tdi_ends-v1-in-T1.nii.gz
        else
            python -m $SNAPSHOT --snapshot_name tdilbl-tdi-in-T1 3vols $MRI/T1.nii.gz ./tdi_ends-v1-in-T1.nii.gz ./tdi_lbl-v$VOX-in-T1nii.gz
    else
        python -m $SNAPSHOT --snapshot_name tdilbl-tdi-in-T1 2vols $MRI/T1.nii.gz $./tdi_lbl-v$VOX-in-T1nii.gz
    fi
    ref_vol_path=./tdi_lbl-v$VOX-in-t1.nii.gz

    out_consim_path=./consim-vol-counts$STRMLNS_SIFT_NO-v$VOX.npy
    #Compute the voxel connectivity similarity
    #This takes a lot of time...
    python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.node_connectivity_metric('$DMR/vol-counts$STRMLNS_SIFT_NO-v$VOX.npy',metric='cosine', out_consim_path='$out_consim_path')"

else
    ref_vol_path=''
    out_consim_path=''
fi


for h in lh rh
do
    python -c "import bnm.recon.algo.reconutils; import os; bnm.recon.algo.reconutils.connectivity_geodesic_subparc('$SURF/$h.white', '$LABEL/$h.aparc.annot', './$h.white-mask-idx.npy', out_annot_path='$LABEL/$h.aparc$SUBAPARC_AREA-$SUBAPARC_MODE.annot', parc_area=int('$SUBAPARC_AREA'), labels=None, ctx='$h', add_string='ctx-'+'$h'+'-', mode='$SUBAPARC_MODE', cras_path='$CRAS_PATH', ref_vol_path='$ref_vol_path', consim_path='$out_consim_path', lut_path='$FREESURFER_HOME/FreeSurferColorLUT_INS.txt')"

    #Quality control snapshot
    python -m $SNAPSHOT --snapshot_name subaparc-aparc$SUBAPARC_AREA-$SUBAPARC_MODE-$h surf_annot $SURF/$h.inflated $LABEL/$h.aparc$SUBAPARC_AREA-$SUBAPARC_MODE.annot
done

for h in lh rh
do
    aseglist=ASEG_LIST_$h
    python -c "import bnm.recon.algo.reconutils; import os; bnm.recon.algo.reconutils.connectivity_geodesic_subparc('$SURF/$h.aseg', '$LABEL/$h.aseg.annot', './$aseg-mask-idx.npy', out_annot_path='$LABEL/$h.aseg$SUBAPARC_AREA-$SUBAPARC_MODE.annot', parc_area=int('$SUBAPARC_AREA'), labels='${!aseglist}', ctx=None, add_string=None, mode='$SUBAPARC_MODE', cras_path='$CRAS_PATH', ref_vol_path='$ref_vol_path', consim_path='$out_consim_path', lut_path='$FREESURFER_HOME/FreeSurferColorLUT_INS.txt')"

    #Quality control snapshot
    python -m $SNAPSHOT --snapshot_name subaparc-aseg$SUBAPARC_AREA-$SUBAPARC_MODE-$h surf_annot $SURF/$h.aseg $LABEL/$h.aseg$SUBAPARC_AREA-$SUBAPARC_MODE.annot
done


popd



