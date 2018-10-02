#!/usr/bin/env bash

source ${ANACONDA_ACTIVATE} ${PYTHON3_ENVIRONMENT}

export FREESURFER_HOME
export SUBJECTS_DIR
export SUBJECT=$6

python <<EOF
from tvb.recon.algo.reconutils import compute_seeg_regions_inv_square_gain_matrix
compute_seeg_regions_inv_square_gain_matrix("$1", "$2", "$3", "$4", "$5")
EOF
