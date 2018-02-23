# -*- coding: utf-8 -*-

import os
import sys
import numpy
from tvb.recon.io.generic import GenericIO
from tvb.recon.logger import get_logger
from tvb.recon.model.constants import SNAPSHOT_NAME, SNAPSHOT_EXTENSION, SNAPSHOTS_DIRECTORY_ENVIRON_VAR, \
    SNAPSHOT_NUMBER_ENVIRON_VAR


class FreeViewController(object):
    logger = get_logger(__name__)
    generic_io = GenericIO()

    target_screenshot_name = SNAPSHOT_NAME
    target_file = "slices.txt"
    cameraPositionsFileName = "cameraPositions.txt"
    in_point_file = "$SUBJ_DIR/scripts/ponscc.cut.log"
    point_line_flag = "CC-CRS"
    in_matrix_file = 'matrix.txt'

    folder_figures = os.environ[SNAPSHOTS_DIRECTORY_ENVIRON_VAR]

    def write_snapshot_camera_positions(self, projection):
        """
        TODO
        """
        count_number = int(os.environ[SNAPSHOT_NUMBER_ENVIRON_VAR])
        file_ref = open(self.cameraPositionsFileName, 'wb')
        png_path = self._get_image_name(count_number, projection, "1")
        file_ref.write("-cam Azimuth 0 Elevation 0 -ss %s\n" % png_path)
        png_path = self._get_image_name(count_number, projection, "2")
        file_ref.write("-cam Azimuth 90 Elevation 0 -ss %s\n" % png_path)
        png_path = self._get_image_name(count_number, projection, "3")
        file_ref.write("-cam Azimuth 180 Elevation 0 -ss %s\n" % png_path)
        png_path = self._get_image_name(count_number, projection, "4")
        file_ref.write("-cam Azimuth 270 Elevation 0 -ss %s\n" % png_path)
        png_path = self._get_image_name(count_number, projection, "5")
        file_ref.write("-cam Azimuth 0 Elevation 90 -ss %s\n" % png_path)
        png_path = self._get_image_name(count_number, projection, "6")
        file_ref.write("-cam Azimuth 0 Elevation 180 -ss %s\n" % png_path)
        file_ref.write(" -quit")
        file_ref.close()
        self.logger.info("It was written  " + self.cameraPositionsFileName)

    def _get_image_name(self, count_number, projection, suffix):
        return os.path.join(self.folder_figures, self.target_screenshot_name + str(
            count_number) + projection + suffix + SNAPSHOT_EXTENSION)

    def prepare_screenshot(self):
        matrix = self.generic_io.read_transformation_matrix(
            self.in_matrix_file)
        self.logger.info("Read idx2rsa matrix: %s" % matrix)

        vector = self.generic_io.read_cc_point(
            self.in_point_file, self.point_line_flag)
        self.logger.info("Read vector: %s" % vector)

        a = numpy.array(matrix)
        b = numpy.array(vector)
        ras_vector = a.dot(b)
        self.logger.info("Computed RAS vector: %s" % ras_vector)

        ras_string = ' '.join(map(str, ras_vector[:-1]))
        self._write_screenshot_command(
            self.target_file, self.target_screenshot_name, projection, ras_string)

    def _write_screenshot_command(
            self, file_path, shot_name, projection, ras_position):
        """
        Open slices.txt file and write the current screen-shot instruction: target_file_name and position
        """
        count_number = int(os.environ[SNAPSHOT_NUMBER_ENVIRON_VAR])
        file_ref = open(file_path, 'wb')
        png_path = os.path.join(self.folder_figures, shot_name +
                                str(count_number) + projection + SNAPSHOT_EXTENSION)
        file_ref.write("-ras %s -ss %s" % (ras_position, png_path))
        file_ref.write(" -quit")
        file_ref.close()
        self.logger.info("It was written " + file_path)


if __name__ == '__main__':
    # TODO images are moved if opened with -ras option and maybe they should be re-centered.
    # TODO calls to this file should be reviewed and avoid computing RAS
    # vector every time a call is made.

    projection = sys.argv[1]
    controller = FreeViewController()
    if projection == 'surface_annotation':
        controller.write_snapshot_camera_positions(projection)
    else:
        controller.prepare_screenshot()
