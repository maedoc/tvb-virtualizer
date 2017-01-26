#!/bin/bash

TMP=$ASEG_SURFS/tmp
if [ ! -d $TMP ]
then
    mkdir $TMP
fi
#Create surfaces around the aseg structures
for l in $ASEG_LIST
do
    lab0=$(printf %06d $l)

    # Pre-tessellate
    echo "==> Pre-tessellating: ${s}, ${lab0}"
    mri_pretess $MRI/aparc+aseg.mgz ${lab0} $MRI/norm.mgz $TMP/aseg-${lab0}.mgz

    # Tessellate
    echo "==> Tessellating: ${s}, ${lab0}"
    mri_tessellate $TMP/aseg-${lab0}.mgz ${lab0} $TMP/aseg-${lab0}-notsmooth

    mris_extract_main_component $TMP/aseg-${lab0}-notsmooth $TMP/aseg-${lab0}-notsmooth_main

    # Smooth
    echo "==> Smoothing: ${s}, ${lab0}"
    mris_smooth -nw $TMP/aseg-${lab0}-notsmooth_main $ASEG_SURFS/aseg-${lab0}

    #Transform from surface tkRAS coordinates to scanner RAS ones:
    #!!Probably not necesary anymore
    #mris_convert --to-scanner $ASEG_SURFS/aseg-${lab0} $ASEG_SURFS/aseg-ras-${lab0}

done
#rm -r $TMP


#Concatenate surfaces and create annotation:
#!!Probably not necessary for aseg-ras
for h in lh rh
do
    aseglist=ASEG_LIST_$h
    python -c "import bnm.recon.algo.reconutils; bnm.recon.algo.reconutils.aseg_surf_conc_annot('$ASEG_SURFS/aseg','$SURF/$h.aseg','$LABEL/$h.aseg.annot','${!aseglist}',lut_path='$FREESURFER_HOME/FreeSurferColorLUT.txt')"
done


#Snapshot for aseg surfs and annot:
python -m $SNAPSHOT --center_surface --snapshot_name aseg_t1_$TRGSUBJECT vol_surf $MRI/T1.nii.gz $SURF/{lh,rh}.aseg
for h in lh rh
do
    #freeview -f $SURF/$h.aseg:annot=aseg \
    #    -viewport 3D -ss $FIGS/aseg-$h-annot.png
    python -m $SNAPSHOT --snapshot_name aseg_annot_$h surf_annot $SURF/$h.aseg $LABEL/$h.aseg.annot

done