#!/bin/bash

#Sub-parcellation and sub-segmentation
cd $SUBJ_DIR
for area in $SUBAPARC_AREA
do
    for h in lh rh
    do
        python -c “import reconutils; reconutils.subparc_files(“$h”,“aparc”,“aparc$area”,$area)”
        #or equivalently if PYTHONPATH is NOT set:
        #python $CODE/reconutils.py subparc $h aparc aparc$area $area
    done


    #TODO: sub-segmentation of aseg
    #aseg2surf etc...

    #Create aparc+asseg
    mri_aparc2aseg --s ${SUBJECT} --aseg aseg$area --annot aparc$area

done