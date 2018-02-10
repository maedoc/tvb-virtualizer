import numpy
import nibabel
import scipy.ndimage

# XXX


def seeg_pos():
    # dilated image for labeling
    d4 = nibabel.load('elec_bin_d4.nii')
    img = d4.get_data()
    aff = d4.get_affine()

    lab_img, n = scipy.ndimage.label(img)
    lab = nibabel.nifti1.Nifti1Image(lab_img, aff)
    nibabel.save(lab, 'd4_lab.nii')

    # binarized without dilation
    bin_dat = nibabel.load('elec_bin.nii').get_data()

    # label the simple binarization
    lab_bin = lab_img * bin_dat

    lab_bin_nii = nibabel.nifti1.Nifti1Image(lab_bin, aff)
    nibabel.save(lab_bin_nii, 'lab_bin.nii')

    def xyz_lab(idx):
        "Get XYZ coords of voxels in label idx."
        vox_idx = numpy.argwhere(lab_bin == idx)
        return aff.dot(numpy.c_[vox_idx, numpy.ones(vox_idx.shape[0])].T)[:3].T

    xyz5 = xyz_lab(5)
    _, s, vt = numpy.linalg.svd(xyz5, 0)
    xi = vt[0].dot(xyz5.T)

    xyz5[numpy.argmin(xi)]
    #[Out]# array([    3.46777344,   158.53613281, -1054.70422363])
    xyz5[numpy.argmax(xi)]
    #[Out]# array([  -26.23730469,   149.66894531, -1048.70446777])

    # these positions match extrema of electrode on lab_bin.nii in freeview
    # given electrode spacing, we generate positions
