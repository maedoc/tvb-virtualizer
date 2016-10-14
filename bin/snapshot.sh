#!/bin/bash

function refreshSnapshotNumber {

	SNAPSHOT_NUMBER=$(($SNAPSHOT_NUMBER+1))

}

if [ $# -gt 0 ]; then

	export SNAPSHOT_NUMBER

	if [ -z $SNAPSHOT_NUMBER ]; then
		SNAPSHOT_NUMBER=0
	fi

	matrixFileName="matrix.txt"
	mri_info --vox2ras $SUBJ_DIR/mri/T1.mgz --o $matrixFileName

    #    It needs to haven bnm.recon in Python Path
    #   python setup.py develop/install
    source activate bnm-recon
    refreshSnapshotNumber
    python -m bnm.recon.snapshot "$@"

else

	echo "No arguments given!"
	exit 1

fi