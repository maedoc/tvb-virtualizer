#!/bin/bash

DIR=$(cd $(dirname $0) && pwd)

if [ $# -ne 3 ]; then
    echo "Usage: $0 DAXFILE PEGASUS_PROPS PATIENT_ENV"
    exit 1
fi

DAXFILE=$1
PEGASUS_PROPS=$2
PATIENT_ENV=$3

source ${PATIENT_ENV}

# This command tells Pegasus to plan the workflow contained in 
# dax file passed as an argument. The planned workflow will be stored
# in the "submit" directory. The execution site is "local".

pegasus-plan --conf ${PEGASUS_PROPS} \
    --dax ${DAXFILE} \
    --dir ${PEGASUS_HOME}/submit \
    --cleanup leaf \
    --force \
    --sites condorpool \
    --submit
