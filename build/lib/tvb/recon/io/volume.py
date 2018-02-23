# -*- coding: utf-8 -*-

import nibabel
import h5py
from tvb.recon.logger import get_logger
from tvb.recon.model.volume import Volume


class ABCVolumeIO(object):
    """
    This will define the behaviour needed for a volume io.
    """

    def read(self, volume_path):
        raise NotImplementedError()

    def write(self, out_volume_path, volume):
        raise NotImplementedError()


class VolumeIO(ABCVolumeIO):
    """
    This class reads content of a NIFTI file and returns a Volume Object
    """

    logger = get_logger(__name__)

    def read(self, volume_path):
        image = nibabel.load(volume_path)
        header = image.header
        data = image.get_data()
        affine_matrix = image.affine
        self.logger.info("The affine matrix extracted from volume %s is %s" % (
            volume_path, affine_matrix))

        return Volume(data, affine_matrix, header)

    def write(self, out_volume_path, volume):
        image = nibabel.Nifti1Image(
            volume.data, volume.affine_matrix, volume.header)
        nibabel.save(image, out_volume_path)


class H5VolumeIO(ABCVolumeIO):
    """
    This class reads content of a H5 file and returns a Volume Object
    """

    logger = get_logger(__name__)

    def read(self, volume_path):
        h5_file = h5py.File(volume_path, 'r', libver='latest')
        data = h5_file['/data'][()]
        h5_file.close()
        return Volume(data, [], None)
