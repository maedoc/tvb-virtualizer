# -*- coding: utf-8 -*-

import os
import time
import logging
import logging.config


OUTPUT_FOLDER = "output"
LOG_FILE = os.path.join(OUTPUT_FOLDER, 'bnm.log')


def get_logger(parent_module):
    """
    Build a logger instance and return it.
    We do not no fancy things, but we want to keep all logging done from a central place,
    in case we need to refactor in the future.
    """
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)

    logger = logging.getLogger(parent_module)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def generate_uq_file_name(parent_folder, name_pattern):
    file_name = name_pattern.replace("*", str(time.clock()))
    return os.path.join(parent_folder, file_name)


def write_dax(adag, dax_file_name):
    # Write the DAX to stdout
    logger = get_logger(__name__)
    logger.info("Writing DAX into %s: %s" % (dax_file_name, adag))
    with open(dax_file_name, "w") as f:
        adag.writeXML(f)
