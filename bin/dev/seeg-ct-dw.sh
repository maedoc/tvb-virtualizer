#!/bin/bash

# workflow for identifying electrode contact positions from CT and FS recon
# comments with XXX below are visual inspections to do

# script arguments
electrode_intensity_threshold=$CT_ELEC_INTENSITY_TH #=2000, magic value, may need adjustment

# check arguments
if [ -z "$CT" ]
then
    echo "CT=/path/to/ct seeg-ct.sh"
    exit 1
fi

# set up topic folder insider subject folder
seeg_dir=$SEEG
pushd $seeg_dir

#CT input pre-processing
# convert source CT to standard format (input could be e.g. DICOM folder)
#if [ "$CT_INPUT_FRMT" = "dicom" ]
#then #CT=a folder
mri_convert $CT ./CT.nii.gz --out_orientation RAS -rt nearest

#else#CT=path to a file CT.nii.gz or CT.nii
#    mri_convert $CT ./CT.nii.gz --out_orientation RAS -rt nearest
#fi

# standardize image orientation
fslreorient2std ./CT.nii.gz ./CT-reo.nii.gz

# TODO rewrite slightly for resized T1 usage
# TODO set up testing on jenkins

for image in T1 brain #aparc+aseg
do
    # convert FS images to Nifti for use with FSL
    mri_convert $MRI/$image.mgz $MRI/$image.nii.gz --out_orientation RAS -rt nearest
    # AND standardize image orientations
    fslreorient2std $MRI/$image.nii.gz $MRI/$image-reo.nii.gz
    # upsampling T1 and brain
    mrresize $MRI/$image-reo.nii.gz ./$image-big.nii.gz -scale 2
done

# align to original res first
# resize and applyxfm to CT into resized image
# register CT to T1 space
flirt -in ./CT-reo.nii.gz \
    -ref  ./T1-big.nii.gz \
    -omat ./c2t.mat \
    -out  ./CT-in-T1.nii.gz \
    -dof  12 \
    -searchrx -180 180 \
    -searchry -180 180 \
    -searchrz -180 180 \
    -cost mutualinfo \
    -searchcost mutualinfo


#Visual checks
#interactive
mrview ./T1-big.nii.gz
#screenshot
# XXX check registration, should fit
#freeview -v ./T1-big.nii.gz ./CT-in-T1.nii.gz:opacity=0.5:colormap=jet \
#    -viewport sagittal -layout 1 -screenshot $FIGS/ss00-CT-in-T1.png
source snapshot.sh 2vols ./T1-big.nii.gz ./CT-in-T1.nii.gz

# invert CT to T1 transform
convert_xfm -omat ./t2c.mat -inverse ./c2t.mat

# move FS images to CT space (mainly brain mask, others for viz)
for image in T1 brain #aparc+aseg
do
    opts="-applyxfm -init ./t2c.mat -ref ./CT-reo.nii.gz"
    # for the volume region mapping, turn off interpolation:
#if [[ $image == "aparc+aseg" ]]
#then
#       opts="$opts -interp nearestneighbour"
#    fi
    # apply transform
    flirt $opts -in $MRI/$image-reo.nii.gz -out $image-in-ct.nii.gz
done

#Visual checks (screenshot)
# XXX check brain on CT, should fit
#freeview -v CT-reo.nii.gz brain-in-ct.nii.gz:opacity=0.5:colormap=jet \
#    -viewport axial -layout 1 -screenshot $FIGS/ss01-brain-in-CT.png
source snapshot.sh 2vols CT-reo.nii.gz brain-in-ct.nii.gz

# binarize brain with erosion to avoid false positives
mri_binarize --erode 8 \
    --i brain-big.nii.gz \
    --o brain-mask.nii.gz \
    --min 10

#Visual checks (screenshot)
# XXX check mask on CT, ovals should line up
#freeview -v CT-reo.nii.gz brain-mask.nii.gz:opacity=0.5:colormap=jet \
#    -viewport axial -layout 1 -screenshot $FIGS/ss02-brain-mask.png
source snapshot.sh 2vols CT-reo.nii.gz brain-mask.nii.gz

# apply mask to ct
mri_binarize --i CT-in-T1.nii.gz --o CT-mask.nii.gz \
    --min $electrode_intensity_threshold \
    --mask brain-mask.nii.gz

#Visual checks (screenshot)
# check CT electrode mask, if luck otherwise do it interactively to be sure
# XXX CT-mask should highlight the electrodes only, neatly separated
# TODO navigate to axial slice where mask most nonzeros
#freeview -v CT-reo.nii.gz CT-mask.nii.gz:opacity=0.5:colormap=jet \
#    -viewport axial -layout 1 -screenshot $FIGS/ss03-ct-mask.png
source snapshot.sh 2vols CT-reo.nii.gz CT-mask.nii.gz

# dilate mask for labeling
mri_binarize --i CT-mask.nii.gz --o CT-dil-mask.nii.gz \
    --min 0.5 --dilate 4 --erode 2

# XXX check dilation (TODO autonav best slice)
#freeview -v CT-reo.nii.gz CT-mask.nii.gz:opacity=0.4:colormap=jet \
#    CT-dil-mask.nii.gz:colormap=hot:opacity=0.4 \
#    -viewport axial -screenshot $FIGS/ss04-ct-dil-mask.png
source snapshot.sh 3vols CT-reo.nii.gz CT-mask.nii.gz CT-dil-mask.nii.gz

# label dil mask and apply to mask
# XXX reported number of electrodes should match implantation schema
python -c "import tvb.recon.algo.reconutils; tvb.recon.algo.reconutils.label_with_dilation('CT-mask.nii.gz', 'CT-dil-mask.nii.gz', 'CT-lab-mask.nii.gz')"

#Visual checks (screenshot)
# XXX check that labels have different colors, in mrview if possible
# TODO use nibabel to generate subplots per electrode
#freeview -v CT-reo.nii.gz CT-lab-mask.nii.gz:opacity=0.5:colormap=jet \
#    -viewport axial -screenshot $FIGS/ss05-ct-dil-mask.png
source snapshot.sh 2vols CT-reo.nii.gz CT-lab-mask.nii.gz

# find contact positions
# and load CT-lab-mask.nii.gz
python<<EOF
import nibabel, numpy as np, bnm.recon.algo.reconutils
nii = nibabel.load('CT-lab-mask.nii.gz')
lab_bin = nii.get_data()
aff = nii.affine
ulab = np.unique(lab_bin)
ulab = ulab[ulab > 0]
ul_to_pos = {}
all_pos = []
for ul in ulab[ulab > 0]:
    xyz_pos = bnm.recon.algo.reconutils.periodic_xyz_for_object(lab_bin, ul, aff)
    all_pos.append(xyz_pos)
all_pos = np.concatenate(all_pos, axis=0)
np.savetxt('seeg_xyz.txt', all_pos, fmt='%f')
EOF


# TODO multispaced electrodes like oblique should have weird spectra
# TODO rm electrode artifact in acquisition plane by deconv?

