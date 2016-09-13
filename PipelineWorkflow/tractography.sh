#!/bin/bash

pushd $DMR

#Tractography
#some more/alternative options?: -backtrack -crop_at_gmwmi -seed_dynamic wm_fod.mif -cutoff 0.06
opt="-seed_gmwmi ./gmwmi.mif -act ./5tt.mif -unidirectional -maxlength $STRMLNS_MAX_LEN -step $STRMLNS_STEP"
tckgen -number $STRMLNS_NO -nthreads $MRTRIX_THRDS $opt ./wm_fod.mif ./$STRMLNS_NO.tck

#SIFT filter
tcksift ./$STRMLNS_NO.tck ./wm_fod.mif ./$STRMLNS_SIFT_NO.tck -act ./5TT.mif -term_number $STRMLNS_SIFT_NO -nthreads $MRTRIX_THRDS


#Visual check (track density image -tdi):
tckmap ./$STRMLNS_SIFT_NO.tck ./tdi.mif -vox 5 #vox: size of bin
mrview ./t1-in-d.nii.gz -overlay.load ./tdi.mif &
mrview ./t1-in-d.nii.gz -overlay.load ./$STRMLNS_SIFT_NO.tck -overlay.opacity 0.5

popd