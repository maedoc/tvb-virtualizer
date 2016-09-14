#!/bin/bash

# Workflow for generating forward models (gain matrices) for s/M/EEG.

# TODO visualization for BEM surfaces, sources & sensors
# TODO generate subcortical sources
# TODO average pial and white surface for cortical generator surface

if [[ -z "$SUBJECT" ]]; then echo "SUBJECT?"; exit 1; fi

# move to subject topic folder
pushd $SUBJECTS_DIR/$SUBJECT/bem

# orient sensors via parcellation, use default or config
# with a label->sensor map, compute rotation, then use ray intersect with
# scalp surface for EEG and inflate for MEG. Sensors should be equidistant
# to scalp surface while satisfying the label->sensor association.

# generate BEM surfaces
mne_watershed_bem

# decimate surfaces
for surf in subjects/tvb/bem/watershed/*_surface
do
    time mris_decimate -d 0.1 ${surf} ${surf}-low
done

python<<EOF
import os
subj = os.environ['SUBJECT']
import pyqtgraph as pg
import pyqtgraph.opengl as gl
import nibabel.freesurfer
app = pg.mkQApp()
win = gl.GLViewWidget()
win.show()
def plotsurf(fname, **kwds):
    v, f = nibabel.freesurfer.read_geometry(fname)
    md = gl.MeshData(vertexes=v, faces=f)
    mi = gl.GLMeshItem(meshdata=md, drawEdges=True, drawFaces=False, **kwds)
    win.addItem(mi)
bem_templ = 'watershed/{subj}_{surf}_surface-low'
for surf in 'brain inner_skull outer_skull outer_skin'.split():
    plotsurf(bem_templ.format(subj=subj, surf=surf))
plotsurf('../surf/lh.pial.fsaverage5', color='r')
app.exec_()
EOF

# inspect

freeview -v ../mri/T1.mgz -f watershed/*-low -viewport coronal

# convert them to BrainVisa format
for surf in *_surface-low
do
    python<<EOF
import utils
utils.convert_fs_to_brain_visa("$surf")
EOF
done

# build head matrix

python -c "import utils; utils.gen_head_model()"

#pushd ${SUBJECTS_DIR}/${SUBJECT}/bem
om_assemble -HM head_model.geom head_model.cond head.mat # 2m32s
om_minverser head.mat head-inv.mat # 3m30s
#popd

# convert cortical surfaces format
for h in rh lh; do
    cp ../surf/$h.pial.fsaverage5 ./cortical-$h
    python -c "import utils; utils.convert_fs_to_brain_visa('cortical-$h')"
done

# make source model for subcortical NOT DONE YET
python -c "import utils; utils.gen_subcort_sources()"
om_assemble -DipSourceMat head_model.{geom,cond} $subcortical.{dip,dsm}

# source model for cortical hemispheres
for h in rh lh; do
    om_assemble -SurfSourceMat head_model.{geom,cond} cortical-$h.{tri,ssm}
done

# make sensor models
om_assemble -h2em head_model.{geom,cond} EEG.sensors EEG.h2em
om_assemble -h2mm head_model.{geom,cond} MEG.sensors MEG.h2mm

seeg_sensor_file=../seeg/seeg.xyz

om_assemble -h2ipm head_model.{geom,cond} $seeg_sensor_file seeg.h2ipm

for h in lh rh;
do
    om_assemble -ds2ipm head_model.{geom,cond} cortical-$h.dip \
        $seeg_sensor_file seeg-$h.ds2ipm
    om_gain -InternalPotential head-inv.mat cortical-$h.ssm \
        seeg.h2ipm seeg-$h.ds2ipm seeg-$h.gain.mat
done

# plot gain matrix
python<<EOF
import h5py, pylab as pl, numpy as np
linop = h5py.File('seeg.gain.mat')['/linop'][:]
print(linop.shape)
pl.hist(np.log(np.abs(linop.ravel())),100)
pl.show()
EOF


# make gain matrices per source / sensor pair
for source_model in subcortical.dsm cortical-{lh,rh}.ssm
do
    for sensor_mode in EEG MEG
    do
        om_gain -$sensor_mode head-inv.mat $source_model $sensor_mode.* \
            $sensor_mode.gain.mat
    done
done


#          ctx-lh   ctx-rh   subcort
#           
#  SEEG
#  EEG
#  MEG
#  ...

# gen parc gain at run time like in TVB
