# -*- coding: utf-8 -*-

import enum


SNAPSHOTS_DIRECTORY_ENVIRON_VAR = 'FIGS'
SNAPSHOT_NUMBER_ENVIRON_VAR = 'SNAPSHOT_NUMBER'
SURFACES_DIRECTORY_ENVIRON_VAR = 'SURF'


class Projections(enum.Enum):
    sagittal = 'sagittal'
    coronal = 'coronal'
    axial = 'axial'


SAGITTAL = Projections.sagittal.value
CORONAL = Projections.coronal.value
AXIAL = Projections.axial.value

PROJECTIONS = [SAGITTAL, CORONAL, AXIAL]

PLANE_NORMALS = {
    SAGITTAL: (1, 0, 0),
    CORONAL: (0, 1, 0),
    AXIAL: (0, 0, 1)
}

X_Y_INDEX = {
    SAGITTAL: [1, 2],
    CORONAL: [0, 2],
    AXIAL: [0, 1]
}

ORIGIN = [0, 0, 0]

SNAPSHOT_NAME = "snapshot"
SNAPSHOT_EXTENSION = ".png"
SNAPSHOTS_DIRECTORY = "snapshots"
GIFTI_EXTENSION = ".gii"
H5_EXTENSION = ".h5"
NPY_EXTENSION = ".npy"

CENTER_RAS_FS_SURF = 'cras'
CENTER_RAS_GIFTI_SURF = ['VolGeomC_R', 'VolGeomC_A', 'VolGeomC_S']

MRI_DIRECTORY = 'MRI'
T1_RAS_VOLUME = 'T1_RAS'
CC_POINT_FILE = "$SUBJ_DIR/scripts/ponscc.cut.log"

FS_TO_CONN_INDICES_MAPPING_PATH = "data/mapping_FS_88.txt"
