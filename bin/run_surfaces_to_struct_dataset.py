#!/usr/bin/env python3

import logging
import os
import sys

from tvb.recon.flow.surfaces_to_structural_datasets import SurfacesToStructuralDataset
from tvb.recon.cli.runner import SimpleRunner

def main():
    subjects_dir, subjid, source_lut, target_lut, weights_file, tract_lengths_file, out_file, out_surf = sys.argv[1:]

    logging.basicConfig(level=logging.INFO)
    runner = SimpleRunner()

    flow = SurfacesToStructuralDataset(
        os.path.join(subjects_dir, subjid, "surf"),
        os.path.join(subjects_dir, subjid, "label"),
        os.path.join(subjects_dir, subjid, "ascii"),
        source_lut,
        target_lut,
        weights_file,
        tract_lengths_file,
        out_file,
        out_surf
    )

    flow.run(runner)



if __name__ == "__main__":
    main()