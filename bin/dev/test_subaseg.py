import os
(FREESURFER_HOME, SUBJECTS_DIR, SUBJECT, SUBJ_DIR, DMR,
 SEGMENT, ASEG_LIST, ASEG_LIST_lh, ASEG_LIST_rh, SURF_VN, VOL_VN, SURF, LABEL, MRI,
 SUBAPARC_AREA, STRUCTURAL_CONNECTIVITY_CONSTRAINT, CON_SIM_AFF, GEOD_DIST_AFF,
 T1_VOX2RASTKR_PATH, CRAS_PATH, VOX, STRMLNS_SIFT_NO) =\
    [os.environ[key] for key in 'FREESURFER_HOME SUBJECTS_DIR SUBJECT SUBJ_DIR DMR \
    SEGMENT ASEG_LIST ASEG_LIST_lh ASEG_LIST_rh SURF_VN VOL_VN SURF LABEL MRI  \
    SUBAPARC_AREA STRUCTURAL_CONNECTIVITY_CONSTRAINT CON_SIM_AFF GEOD_DIST_AFF \
     T1_VOX2RASTKR_PATH CRAS_PATH VOX STRMLNS_SIFT_NO'.split()]

#ASEG_LIST="8 10 11 12 13 16 17 18 26 47 49 50 51 52 53 54 58"
#ASEG_SURF="/Users/dionperd/CBR/VEP/JUNG/JUNG/aseg_surf"
import bnm.recon.algo.service.subparcelation as subaparc
import nibabel
import numpy as np

#Inputs:
surf='lh.aseg'
labels=ASEG_LIST_lh
surf_path=os.path.join(os.environ['SURF'], surf)
annot_path=os.path.join(os.environ['LABEL'], surf+'.annot')
con_verts_idx = os.path.join(os.environ['SEGMENT'], surf+'-mask-idx.npy')
out_annot_path=os.path.join(os.environ['LABEL'], surf+'_CONSIM'+CON_SIM_AFF+'_GEODIST'+GEOD_DIST_AFF+'.annot')
parc_area=float(SUBAPARC_AREA)
con_sim_aff=float(CON_SIM_AFF)*0.0
geod_dist_aff=float(GEOD_DIST_AFF)
if STRUCTURAL_CONNECTIVITY_CONSTRAINT == 'True':
    structural_connectivity_constraint = True
elif STRUCTURAL_CONNECTIVITY_CONSTRAINT == 'False':
    structural_connectivity_constraint = False
else:
    raise ValueError
cras_path=CRAS_PATH
ref_vol_path=os.path.join(os.environ['SEGMENT'], 'tdi_lbl-v3-in-t1.nii.gz')
consim_path=os.path.join(os.environ['SEGMENT'], 'consim-vol-counts5M-v3.npy')

subaparc_service=subaparc.SubparcellationService()
subaparc_service.connectivity_geodesic_subparc(surf_path, annot_path, con_verts_idx, out_annot_path,
                                      labels=labels, hemi=None, ctx=None,
                                      parc_area=parc_area, con_sim_aff=con_sim_aff, geod_dist_aff=geod_dist_aff,
                                       structural_connectivity_constraint=structural_connectivity_constraint,
                                      cras_path=cras_path, ref_vol_path=ref_vol_path, consim_path=consim_path,
                                      lut_path=os.path.join(os.environ['FREESURFER_HOME'], 'FreeSurferColorLUT.txt'))