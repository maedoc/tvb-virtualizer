#!/bin/bash

#DWI preprocessing

#Make dwi folder and push dir there
mkdir $DMR
pushd $DMR

if [ "$DWI_REVERSED" = "no" ]
then
    if [ "$DWI_INPUT_FRMT" = "dicom" ]
    then
        #Convert dicoms to .mif
        mrconvert $DATA/DWI ./dwi_raw.mif
    fi

    #Preprocess with eddy correct (no topup applicable here)
    #ap direction doesn’t matter in this case of NOT reversed
    dwipreproc $DWI_PE_DIR ./dwi_raw.mif ./dwi.mif -rpe_none -nthreads $MRTRIX_THRDS

else
    if [ "$DWI_INPUT_FRMT" = "dicom" ]
    then
        #ELSEIF reversed:
        mrchoose 0 mrconvert $DATA/DWI ./dwi_raw.mif
        mrchoose 1 mrconvert $DATA/DWI ./dwi_raw_re.mif
    else
        mronvert $DATA/DWI/dwi_raw.nii.gz ./dwi_raw.mif
        mronvert $DATA/DWI/dwi_raw_re.nii.gz ./dwi_raw_re.mif
    fi
    dwipreproc $DWI_PE_DIR ./dwi_raw.mif ./dwi.mif -rpe_pair ./dwi_raw.mif ./dwi_raw_re.mif -nthreads $MRTRIX_THRDS
fi

#Create brain mask
dwi2mask ./dwi.mif ./mask.mif -nthreads $MRTRIX_THRDS
#Extract bzero…
dwiextract ./dwi.mif ./b0.nii.gz -bzero -nthreads $MRTRIX_THRDS

popd


