#!/bin/bash

pushd $BEM

#
#	ctx-lh	ctx-rh	subcort
#SEEG
#EEG
#MEG
#
#

# Parcellations to be used should be given as inputs.
#vols=$*
#Sensors as well
#sensors=$*

#Apply vols to gains for per-vol lead fields
#TODO
for vol in $vols
do
    for sensors in SEEG EEG MEG
    do
        #TODO
        python -c "import reconutils; reconutils.parc_gain('$MRI/$vol','./$sensors')"
    done
done

popd