#!/usr/bin/env python

import time
import argparse
from Pegasus.DAX3 import ADAG
from bnm.recon.pegasus.config import Configuration
from bnm.recon.pegasus.flirt import step_coregister_t1_dwi
from bnm.recon.pegasus.t1 import steps_recon_all
from bnm.recon.pegasus.diffusion import steps_dwi_preproc
from bnm.recon.pegasus.utils import write_dax


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a BNM flow")
    parser.add_argument("patient_file")
    args = parser.parse_args()

    dax = ADAG("BNM")
    dax.metadata("name", "Brain Network Model Reconstruction WorkFlow")
    dax.metadata("created-at", time.ctime())
    dax.metadata("flow-configuration", args.patient_file)
    config = Configuration(args.patient_file)

    relevant_t1_job = steps_recon_all(dax, config)
    relevant_dwi_job = steps_dwi_preproc(dax, config.diffusion)
    step_coregister_t1_dwi(dax, config, relevant_t1_job, relevant_dwi_job)

    write_dax(dax, config.main_dax_path)
