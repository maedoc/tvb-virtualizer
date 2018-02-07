#!/bin/bash

# TODO the act anat prepare fsl is single threaded, so
#   could be run in parallel over subjects
#   the rest is IO bound or parallelized within process

# options
root=$1
nthreads=8

echo "running on data root $root"
# sleep for 1 second
sleep 1

# paths
export FSLDIR=/usr/local/fsl
export FSLOUTPUTTYPE=NIFTI_GZ
export PATH=/usr/local/mrtrix3/bin:/usr/local/mrtrix3/scripts:/usr/local/fsl/bin/:$PATH


# script starts
pushd $root
t1=$root/T1w
dmr=$t1/Diffusion

# create TVB directory and pushd on it
mkdir TVB && pushd TVB

# prep diffusion
mrconvert $dmr/data.nii.gz dwi.mif -fslgrad $dmr/b{vecs,vals}
dwi2mask dwi.mif mask.mif
dwiextract dwi.mif lowb.mif -bzero
mrconvert lowb.mif lowb.nii.gz

# vol dmr analysis
dwi2response -nthreads $nthreads dwi.mif response.txt -mask mask.mif -sf sf-mask.mif
dwi2fod -nthreads $nthreads dwi.mif response.txt csd.mif -mask mask.mif
act_anat_prepare_fsl $t1/T1w_acpc_dc_restore.nii.gz act.mif
5tt2gmwmi act.mif gmwmi.mif

# tracking
tckgen -nthreads $nthreads -num 5000000 -seed_gmwmi gmwmi.mif -act act.mif -unidirectional -maxlength 250 -step 0.5 csd.mif brain.tck
tcksift -nthreads $nthreads brain.tck csd.mif brain-sift.tck -act act.mif -term_number 2000000

# connectome
conf=$(dirname $(dirname $(which mrconvert)))/src/connectome/config/fs_default.txt
labelconfig $t1/aparc+aseg.nii.gz $conf aparc+aseg.mif -lut_freesurfer ${FREESURFER_HOME}/FreeSurferColorLUT.txt
for metric in count meanlength
do
	tck2connectome brain-sift.tck aparc+aseg.mif $metric.csv -assignment_radial_search 2 -zero_diagonal -metric $metric
done

popd # TVB
popd # $root
