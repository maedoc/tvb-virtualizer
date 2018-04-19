# -*- coding: utf-8 -*-

# imports
from __future__ import absolute_import
import os
import logging
import logging.config


OUTPUT_FOLDER = "output"
LOG_FILE = os.path.join(OUTPUT_FOLDER, 'tvb.log')


def _ensure_log_folder_exists():
    """ Ensure output folder exists if not create one."""
    if not os.path.exists(OUTPUT_FOLDER):
        os.mkdir(OUTPUT_FOLDER)


def get_logger(parent_module):
    """
    Build a logger instance and return it.
    We do not no fancy things, but we want to keep all logging done from a central place,
    in case we need to refactor in the future.
    """
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    _ensure_log_folder_exists()

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
