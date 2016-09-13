# TODO break into several modules in package


import os
import sys
import glob
import numpy as np
import nibabel
import scipy.io
import scipy.cluster
import warnings
import nibabel.freesurfer


try:
    import gdist
except ImportError:
    warnings.warn('Geodesic distance module unavailable; please pip install gdist.')


SUBJECTS_DIR, SUBJECT = [os.environ[key] for key in 'SUBJECTS_DIR SUBJECT'.split()]


def parse_asa_electrode_file(fname):
    "Parse an ASA electrode format file."
    contents = {'positions': [], 'labels': []}
    with open(fname, 'r') as fd:
        lines = (l for l in fd.readlines())
        # parse header
        for line in lines:
            if line.startswith('#'):
                continue
            parts = line.strip().split()
            if line.startswith('ReferenceLabel'):
                contents['reference_label'] = parts[1]
            elif line.startswith('UnitPosition'):
                contents['unit_position'] = parts[1]
            elif line.startswith('NumberPositions'):
                contents['number_positions'] = int(parts[1])
            elif line.startswith('Positions'):
                break
            else:
                raise Exception('unknown header line: %r' % (line,))
        # parse positions
        for line, _ in zip(lines, range(contents['number_positions'])):
            contents['positions'].append(
                    [float(coord) for coord in line.strip().split()])
        # parse labels
        #assert next(lines).strip() == 'Labels'
        [contents['labels'].append(line.strip()) for line in lines]
    return contents


def test_parse_asa_electrode_file():
    contents = parse_asa_electrode_file('standard_1005.elc')
    assert contents['reference_label'] == 'avg'
    assert contents['unit_position'] == 'mm'
    assert contents['number_positions'] == 346
    assert len(contents['positions']) == 346
    assert contents['positions'][0] == [-86.0761, -19.9897, -47.9860]
    assert contents['positions'][-1] == [85.7939, -25.0093, -68.0310]
    assert len(contents['labels']) == 346
    assert contents['labels'][0] == 'LPA'
    assert contents['labels'][-1] == 'A2'


def vertex_normals(v, f):
    vf = v[f]
    fn = np.cross(vf[:,1] - vf[:, 0], vf[:, 2] - vf[:, 0])
    vf = [set() for _ in range(len(v))]
    for i, fi in enumerate(f):
        for j in fi:
            vf[j].add(i)
    vn = np.zeros_like(v)
    for i, fi in enumerate(vf):
        fni = fn[list(fi)]
        norm = fni.sum(axis=0)
        norm /= np.sqrt((norm**2).sum())
        vn[i] = norm
    return vn


def write_brain_visa_surf(fname, v, f):
    vn = vertex_normals(v, f)
    with open(fname, 'w') as fd:
        fd.write('- %d\n' % len(vn))
        for (vx, vy, vz), (nx, ny, nz) in zip(v, vn):
            fd.write('%f %f %f %f %f %f\n' % (vx, vy, vz, nx, ny, nz))
        fd.write('- %d %d %d\n' % ((len(f),)*3))
        for i, j, k in f:
            fd.write('%d %d %d\n' % (i, j, k))


def convert_fs_to_brain_visa(fs_surf):
    v, f = nibabel.freesurfer.read_geometry(fs_surf)
    write_brain_visa_surf(fs_surf + '.tri', v, f)


def annot_path(hemi, annot_name):
    annot_fname = '%s.%s.annot' % (hemi, annot_name)
    annot_path = os.path.join(SUBJECTS_DIR, SUBJECT, 'label', annot_fname)
    return annot_path


def read_annot(hemi, annot_name):
    return nibabel.freesurfer.read_annot(annot_path(hemi, annot_name))


def write_annot(hemi, annot_name, labels, ctab, names):
    return nibabel.freesurfer.write_annot(annot_path(hemi, annot_name), labels, ctab, names)


def read_surf(hemi, name):
    surf_fname = '%s.%s' % (hemi, name)
    surf_path = os.path.join(SUBJECTS_DIR, SUBJECT, 'surf', surf_fname)
    return nibabel.freesurfer.read_geometry(surf_path)


def annot_to_lut(hemi, annot_name, lut_path):
    _, ctab, names = read_annot(hemi, annot_name)
    with open(lut_path, 'w') as fd:
        for name, (r, g, b, a, id) in zip(names, ctab):
            fd.write('%d\t%s\t%d %d %d %d\n' % (id, name, r, g, b, a))


def annot_to_conn_conf(hemi, annot_name, conn_conf_path):
    _, _, names = read_annot(hemi, annot_name)
    with open(conn_conf_path, 'w') as fd:
        for id, name in enumerate(names):
            fd.write('%d\t%s\n' % (id, name))


def compute_gdist_mat(surf_name='pial', max_distance=40.0):
    max_distance = float(max_distance) # in case passed from sys.argv
    for h in 'rl':
        surf_path = '%s/%s/surf/%sh.%s' % (SUBJECTS_DIR, SUBJECT, h, surf_name)
        v, f = nibabel.freesurfer.read_geometry(surf_path)
        mat_path = '%s/%s/surf/%sh.%s.gdist.mat' % (SUBJECTS_DIR, SUBJECT, h, surf_name)
        mat = gdist.local_gdist_matrix(v, f.astype('<i4'), max_distance=40.0)
        scipy.io.savemat(mat_path, {'gdist': mat})


def convert_bem_to_tri():
    surfs_glob = '%s/%s/bem/watershed/*_surface-low' % (SUBJECTS_DIR, SUBJECT)
    for surf_name in glob.glob(surfs_glob):
        utils.convert_fs_to_brain_visa(surf_name)


def gen_head_model():
    surfs_glob = '%s/%s/bem/watershed/*_surface-low.tri' % (SUBJECTS_DIR, SUBJECT)
    surfs = glob.glob(surfs_glob)

    if len(surfs) == 0:
        raise Exception('tri surfaces not found!')

    hm_base = '%s/%s/bem/head_model' % (SUBJECTS_DIR, SUBJECT)
    hm_temp = """# Domain Description 1.1

Interfaces 3

Interface Skull: "{0}_outer_skull_surface-low.tri"
Interface Cortex: "{0}_inner_skull_surface-low.tri"
Interface Head: "{0}_outer_skin_surface-low.tri"

Domains 4

Domain Scalp: Skull -Head
Domain Brain: -Cortex
Domain Air: Head
Domain Skull: Cortex -Skull
""".format('%s/%s/bem/watershed/%s' % (SUBJECTS_DIR, SUBJECT, SUBJECT))

    hm_geom = hm_base + '.geom'
    with open(hm_geom, 'w') as fd:
        fd.write(hm_temp)
    print ('%s written.' % (hm_geom,))

    hm_cond = hm_base + '.cond'
    with open(hm_cond, 'w') as fd:
        fd.write("""# Properties Description 1.0 (Conductivities)

Air         0.0
Scalp       1
Brain       1
Skull       0.03
""")
    print ('%s written.' % (hm_cond,))


def tri_area(tri):
    i, j, k = np.transpose(tri, (1, 0, 2))
    ij = j - i
    ik = k - i
    return np.sqrt(np.sum(np.cross(ij, ik)**2, axis=1)) / 2.0



def make_subparc(v, f, annot, roi_names, trg_area=100.0):
    # TODO subcort subparc with geodesic on bounding gmwmi
    # TODO normalize fiber counts by relevant gmwmi area

    # build vertex -> face list map
    vfm = [set([]) for _ in v]
    for i, face in enumerate(f):
        for j in face:
            vfm[j].add(i)
    vfm = np.array(vfm)

    # make new annotation
    new_annot = annot.copy()
    new_names = [] # such that new_names[new_annot[i]] is correct name for i'th vertex
    next_aval = 1
    for i in np.unique(annot):
        name = roi_names[i]
        mask = annot == i

        # "unknown", just skip
        if i == -1:
            new_annot[mask] = 0
            new_names.append(name)
            continue

        # indices of faces in ROI
        rfi = set([])
        for face_set in vfm[mask]:
            rfi.update(face_set)
        rfi = np.array(list(rfi))

        # empty roi
        if rfi.size == 0:
            continue

        # compute area of faces in roi
        roi_area = np.sum(tri_area(v[f[rfi]]))

        # choose k for desired roi area
        k = int(roi_area / trg_area) + 1
        assert k>=1

        # cluster centered vertices
        v_roi = v[mask]
        _, i_lab = scipy.cluster.vq.kmeans2(v_roi - v_roi.mean(axis=0), k)

        # update annot
        new_annot[mask] = next_aval + i_lab
        next_aval += k
        new_names += ['%s-%d' % (name.decode('ascii'), j) for j in range(k)]

    # create random colored ctab
    new_ctab = np.random.randint(255, size=(len(new_names), 5))
    r, g, b, _, _ = new_ctab.T
    new_ctab[:, 3] = 0
    new_ctab[:, 4] = r + 256 * g + 256 * 256 * b # fs magic values

    return new_annot, new_ctab, new_names


def subparc_files(hemi, parc_name, out_parc_name, trg_area):
    trg_area = float(trg_area)
    v, f = read_surf(hemi, 'sphere')
    lab, ctab, names = read_annot(hemi, parc_name)
    new_lab, new_ctab, new_names = make_subparc(v, f, lab, names)
    write_annot(hemi, out_parc_name, new_lab, new_ctab, new_names)


def label_with_dilation(to_label_nii_fname, dilated_nii_fname, out_nii_fname):
    "Label one nifti with its dilation, cf seeg-ct.sh"
    # TODO could make dilation with ndimage also.
    import nibabel, scipy.ndimage
    mask = nibabel.load('CT-mask.nii.gz')
    dil_mask = nibabel.load('CT-dil-mask.nii.gz')
    lab, n = scipy.ndimage.label(dil_mask.get_data())
    print('[label_with_dilation] %d objects found.' % (n, ))
    lab_mask_nii = nibabel.nifti1.Nifti1Image(lab * mask.get_data(), mask.affine)
    nibabel.save(lab_mask_nii, 'CT-lab-mask.nii.gz')


def gen_dipole_triplets(pos):
    pos3 = np.repeat(pos, 3, axis=0)
    ori3 = np.tile(np.eye(3), (len(pos), 1))
    return pos3, ori3


def gen_dipoles(pos, ori_or_face=None, out_fname=None):
    "Generate dipoles (or equiv. file) for OpenMEEG."
    if ori_or_face is None:
        pos, ori = gen_dipole_triplets(pos)
    else:
        if ori_or_face.dtype in np.floattypes:
            ori = ori_or_face
        else:
            ori = gen_vertex_normals(v=pos, f=ori_or_face)
    np.savetxt(out_fname, np.c_[pos, ori], fmt='%f')


import pylab as pl, numpy as np
def periodic_xyz_for_object(lab, val, aff, bw=0.1, doplot=False):
    "Find blob centers for object in lab volume having value val."
    # TODO handle oblique with multiple spacing
    # vox coords onto first mode
    vox_idx = np.argwhere(lab == val)
    xyz = aff.dot(np.c_[vox_idx, np.ones(vox_idx.shape[0])].T)[:3].T
    xyz_mean = xyz.mean(axis=0)
    xyz -= xyz_mean
    u, s, vt = np.linalg.svd(xyz, 0)
    xi = u[:, 0] * s[0]
    # histogram and ft to find spacing and offset
    bn, bxi_ = np.histogram(xi, np.r_[min(xi) - 0.5 : max(xi) + 0.5 : bw])
    bxi = bxi_[:-1] + bw / 2.0
    w = np.r_[1.0 : 6.0 : 1000j]
    f = (1.0 / w)[:, None]
    Bf = (np.exp(-2 * np.pi * 1j * bxi * f) * bn * bw).sum(axis=-1)
    i_peak = np.argmax(np.abs(Bf))
    theta = np.angle(Bf[i_peak])
    print("[periodic_xyz_for_object]", val, 1/f[i_peak][0], theta)
    xi_o = -theta / (2 * np.pi * f[i_peak])
    xi_pos = np.r_[xi_o : xi.max() : w[i_peak]]
    xi_neg = np.r_[-xi_o : -xi.min() : w[i_peak]]
    xi_pos = np.sort(np.r_[-xi_neg, xi_pos[1:]])
    xyz_pos = np.c_[xi_pos, np.zeros((len(xi_pos), 2))].dot(vt) + xyz_mean
    if doplot:
        pl.figure()
        pl.subplot(2, 1, 1)
        pl.plot(bxi, bn)
        pl.subplot(2, 1, 2)
        pl.plot(w, np.abs(Bf))
        pl.subplot(2, 1, 1)
        cos_arg = 2*np.pi*f[i_peak]*bxi + theta
        pl.plot(bxi, np.cos(cos_arg)*bn.std()+bn.mean(), 'k--', alpha=0.5)
        [pl.axvline(xp, color='r') for xp in xi_pos];
        pl.show()
    return xyz_pos




def label_vol_from_tdi(tdi_nii_fname, out_fname, lo=1):
    "Make label volume from tckmap output."
    nii = nibabel.load(tdi_nii_fname)
    tdi = nii.get_data().copy()
    mask = tdi > lo
    tdi[~mask] = 0
    tdi[mask] = np.r_[:mask.sum()]
    out_nii = nibabel.nifti1.Nifti1Image(tdi, nii.affine)
    nibabel.save(out_nii, out_fname)


def simple_label_config(aparc_fname, out_fname):
    "Rewrite label volume to have contiguous values like mrtrix' labelconfig."
    aparc = nibabel.load(aparc_fname)
    vol = aparc.get_data()
    uval = np.unique(vol)
    uval_map = np.r_[:uval.max() + 1]
    uval_map[uval] = np.r_[:uval.size]
    uvol = uval_map[vol]
    uparc = nibabel.nifti1.Nifti1Image(uvol, aparc.affine)
    nibabel.save(uparc, out_fname)


if __name__ == '__main__':
    cmd = sys.argv[1]

    if cmd == 'gdist':
        compute_gdist_mat(*sys.argv[2:])
    if cmd == 'subparc':
        subparc_files(*sys.argv[2:])

