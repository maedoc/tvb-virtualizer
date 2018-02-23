# -*- coding: utf-8 -*-

import os
from tvb.recon.io.elec import ElectrodeParser


def test_parse_asa_electrode_file():
    # XXX will need standard place for test & resource data files
    parser = ElectrodeParser()
    contents = parser.parse_asa_electrode_file(
        os.path.join('data', 'standard_1005.elc'))
    assert contents['reference_label'] == 'avg'
    assert contents['unit_position'] == 'mm'
    assert contents['number_positions'] == 346
    assert len(contents['positions']) == 346
    assert contents['positions'][0] == [-86.0761, -19.9897, -47.9860]
    assert contents['positions'][-1] == [85.7939, -25.0093, -68.0310]
    assert len(contents['labels']) == 346
    assert contents['labels'][0] == 'LPA'
    assert contents['labels'][-1] == 'A2'
