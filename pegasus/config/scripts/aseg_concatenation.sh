#!/usr/bin/env bash

# set source to anaconda
source //anaconda/bin/activate tvb_recon_python3_env

# export
export FREESURFER_HOME
source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
export SUBJECT=$5

# run python and import reconutils, aseg, annot and set lut_path to $4
python -c "import tvb.recon.algo.reconutils; tvb.recon.algo.reconutils.aseg_surf_conc_annot('$PWD','$1','$2','$3',lut_path='$4')"