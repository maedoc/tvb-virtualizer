import os
import sys
import warnings
from bnm.recon.algo.service.surface import SurfaceService
from bnm.recon.algo.service.volume import VolumeService
from bnm.recon.algo.service.subparcelation import SubparcellationService
from bnm.recon.algo.service.sensor import SensorService
from bnm.recon.algo.service.annotation import AnnotationService, DEFAULT_LUT

try:
    import gdist
except ImportError:
    warnings.warn('Geodesic distance module unavailable; please pip install gdist.')


SUBJECTS_DIR, SUBJECT, FREESURFER_HOME = [os.environ[key] for key in 'SUBJECTS_DIR SUBJECT FREESURFER_HOME'.split()]

surfaceService = SurfaceService()
volumeService = VolumeService()
subparcelatioService = SubparcellationService()
sensorService = SensorService()
annotationService=AnnotationService()


def gen_head_model():
    sensorService.gen_head_model()

#-----------------------------Freesurfer surfaces------------------------------

def convert_fs_to_brain_visa(fs_surf):
    surfaceService.convert_fs_to_brain_visa(fs_surf)

def compute_gdist_mat(surf_name='pial', max_distance=40.0):
    surfaceService.compute_gdist_mat(surf_name, max_distance)

def aseg_surf_conc_annot(surf_path,out_surf_path,annot_path,labels,lut_path=os.path.join(FREESURFER_HOME,'FreeSurferColorLUT.txt')):
    surfaceService.aseg_surf_conc_annot(surf_path, out_surf_path, annot_path, labels, lut_path)

#---------------------------------Volumes--------------------------------------

def vol_to_ext_surf_vol(in_vol_path, labels=None, ctx=None, out_vol_path=None,labels_surf=None,labels_inner='0'):
    volumeService.vol_to_ext_surf_vol(in_vol_path, labels, ctx, out_vol_path, labels_surf, labels_inner)

def mask_to_vol(in_vol_path,mask_vol_path,out_vol_path=None,labels=None,ctx=None,vol2mask_path=None,vn=1,th=0.999,labels_mask=None,labels_nomask='0'):
    volumeService.mask_to_vol(in_vol_path, mask_vol_path, out_vol_path, labels, ctx, vol2mask_path, vn, th, labels_mask, labels_nomask)

def label_with_dilation(to_label_nii_fname, dilated_nii_fname, out_nii_fname):
    volumeService.label_with_dilation(to_label_nii_fname, dilated_nii_fname, out_nii_fname)

def label_vol_from_tdi(tdi_nii_fname, out_fname, lo=0.5):
    volumeService.label_vol_from_tdi(tdi_nii_fname, out_fname, lo)

def remove_zero_connectivity_nodes(node_vol_path,con_mat_path,tract_length_path=None):
    volumeService.remove_zero_connectivity_nodes(node_vol_path, con_mat_path, tract_length_path)

def simple_label_config(aparc_fname, out_fname):
    volumeService.simple_label_config(aparc_fname, out_fname)

 #-------------------------Surfaces from/to volumes----------------------------

def sample_vol_on_surf(surf_path, vol_path, annot_path, out_surf_path, cras_path,
                         add_string='',vertex_neighbourhood=1, add_lbl=[],
                           lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT)):
    surfaceService.sample_vol_on_surf(surf_path, vol_path, annot_path, out_surf_path, cras_path,
                                      add_string,vertex_neighbourhood, add_lbl, lut_path)

#------------------Subparcellation-subsegmentation-----------------------------

def subparc_files(surf_path, annot_path, out_annot_parc_name, trg_area):
    subparcelatioService.subparc_files(surf_path, annot_path, out_annot_parc_name, trg_area)

def connectivity_geodesic_subparc(self, surf_path, annot_path, con_verts_idx, out_annot_path=None,
                                      labels=None, ctx=None, add_string=None,
                                      parc_area=100, con_sim_aff=1.0, geod_dist_aff=1.0,
                                      structural_connectivity_constraint=True, clustering_mode='divisive',
                                      cras_path=None, ref_vol_path=None, consim_path=None,
                                      in_lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT),
                                      out_lut_path=os.path.join(os.environ['FREESURFER_HOME'], DEFAULT_LUT)):
    subparcelatioService.connectivity_geodesic_subparc(surf_path, annot_path, con_verts_idx,
                                    out_annot_path=out_annot_path, labels=labels, ctx=ctx, add_string=add_string,
                                      parc_area=parc_area, con_sim_aff=con_sim_aff, geod_dist_aff=geod_dist_aff,
                                      structural_connectivity_constraint=structural_connectivity_constraint,
                                       clustering_mode=clustering_mode,
                                      cras_path=cras_path, ref_vol_path=ref_vol_path, consim_path=consim_path,
                                        in_lut_path=in_lut_path, out_lut_path=out_lut_path)

def node_connectivity_metric(con_mat_path,metric="cosine", out_consim_path=None):
    subparcelatioService.node_connectivity_metric(con_mat_path, metric, out_consim_path)

#-------------------------------Contacts---------------------------------------
def periodic_xyz_for_object(lab, val, aff, bw=0.1, doplot=False):
    sensorService.periodic_xyz_for_object(lab, val, aff, bw, doplot)


if __name__ == '__main__':
    cmd = sys.argv[1]

    if cmd == 'gdist':
        compute_gdist_mat(*sys.argv[2:])
    if cmd == 'subparc':
        subparc_files(*sys.argv[2:])

