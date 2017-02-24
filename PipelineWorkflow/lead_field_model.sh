#!/bin/bash


#Co-register the CT and T1 images
pushd $MRI
regopt="-dof 12 -searchrx -180 180 -searchry -180 180 -searchrz -180 180 -cost mutualinfo"
flirt -in $DATA/ct.nii.gz .gz-ref ./T1.nii.gz -omat $BEM/ct2t1.mat -out $BEM/ct-in-t1.nii.gz $regopt
popd

pushd $BEM

#Generate BEM surfaces
mne_watershed_bem --subject $SUBJECT

#Decimate BEM surfaces (LOOP)
for surf in ./watershed/*_surface
do
    mris_decimate -d 0.1 ${surf} ${surf}-low
done

#Visual check: surfaces should NOT INTERSECT!
freeview -v $MRI/T1.nii.gz -f ./watershed/*-low -viewport coronal
#TODO: 3D gui visual check

#Convert BEM surfaces to BrainVisa format
for surf in *surface-low
do
    python -c "import reconutils; reconutils.convert_fs_to_brain_visa('$surf')"
done

#Generate and invert head model
python -c “import reconutils; reconutils.gen_head_model()”
om_assemble -HM ./head_model.geom ./head_model.cond ./head.mat # 2m32s
om_minverser ./head.mat ./head-inv.mat # 3m30s


#Sources surfaces to tri
for h in rh lh
do
    cp ../surf/$h.pial.fsaverage5 ./cortical-$h
    python -c "import reconutils; reconutils.convert_fs_to_brain_visa('cortical-$h')"
done

#Cortical sources surfaces model
for h in rh lh; do do
om_assemble -SurfSourceMat ./head_model.geom ./head_model.cond ./cortical-$h.tri ./cortical-$h.ssm # 2m32s
done

#Subcortical volume sources (list of dipoles)
#TODO:
python -c "import reconutils; reconutils.gen_subcort_sources()"

#Subcortical volume sources model
for h in rh lh
do
    om_assemble -DipSourceMat ./head_model.geom ./head_model.cond ./subcortical-$h.dip ./subcortical-$h.dsm # 2m32s
done

#Sensor models...
om_assemble -h2em ./head_model.geom ./head_model.cond ./EEG_sensors ./EEG.h2em # 2m32s
om_assemble -h2mm ./head_model.geom /.head_model.cond ./MEG_sensors ./MEG.h2mm # 2m32s

#...and lead fields for EEG and MEG
for source_model in subcortical.dsm cortical-lh.ssm cortical-rh.ssm
do
    for sensor_mode in EEG MEG
    do
        om_gain -$sensor_mode ./head-inv.mat $source_model $sensor_mode.* ./$sensor_mode_gain.mat
    done
done

#...and for SEEG:
for h in lh rh;
do
    om_assemble -ds2ipm ./head_model.{geom,cond} ./cortical-$h.dip ./SEEG_sensors ./seeg-$h.ds2ipm
    om_gain -InternalPotential ./head-inv.mat ./cortical-$h.ssm ./seeg.h2ipm ./seeg-$h.ds2ipm ./seeg-$h_gain.mat
done


#Visual check:
# plot gain matrix
python<<EOF
import h5py, pylab as pl, numpy as np
linop = h5py.File('seeg_gain.mat')['/linop'][:]
print(linop.shape)
pl.hist(np.log(np.abs(linop.ravel())),100)
pl.show()
EOF

#
#	ctx-lh	ctx-rh	subcort
#SEEG
#EEG
#MEG
#
#

