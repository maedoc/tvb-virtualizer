# -*- coding: utf-8 -*-

import pytest
import numpy as np


# TODO tests using hcp 100307 & anon mrs dataset

# we can't really unit test FS, FSL or MRtrix3 but we can test
# formatting, custom algos and test-retest consistency.
# later, we can test setup as well.


@pytest.mark.skip(reason="require testing datasets")
def test_roi_areas():
    # $ mris_anatomical_stats -a label/lh.aparc.annot -b hcp10037 lh > stats.txt
    stats = np.loadtxt('stats.txt')
    fs_roi_areas = stats[:, 1]
    my_roi_areas = np.array([roi_area(i, vfm, v_roi)
                             for i in r_[1:35] if i != 3])
    assert np.testing.allclose(fs_roi_areas, my_roi_areas)
