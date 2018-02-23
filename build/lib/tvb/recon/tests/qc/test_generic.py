# -*- coding: utf-8 -*-

from tvb.recon.io.generic import GenericIO
from tvb.recon.tests.base import get_data_file


def test_read_cc_point():
    generic_io = GenericIO()
    file_path = get_data_file("fsaverage_modified",
                              "scripts", "ponscc.cut.log")
    cc_point = generic_io.read_cc_point(file_path, GenericIO.point_line_flag)
    assert cc_point == [100.0, 100.0, 100.0, 1]
