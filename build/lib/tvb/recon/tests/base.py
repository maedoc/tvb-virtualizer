# -*- coding: utf-8 -*-

import os
import shutil
import unittest
import tempfile
from .. import logger


# TODO use tempfile.TemporaryDirectory?
here = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(here, '..', '..', '..', 'data')
temporary_folder = os.path.join(data_path, 'temp')


def get_data_file(*args):
    file_path = os.path.join(data_path, *args)
    if not os.path.exists(file_path):
        raise IOError("File not found %s" % file_path)
    return file_path


def get_temporary_files_path(*args):
    if not os.path.exists(temporary_folder):
        os.makedirs(temporary_folder)
    file_path = os.path.join(temporary_folder, *args)
    return file_path


def remove_temporary_test_files():
    shutil.rmtree(temporary_folder)


class BaseTest(unittest.TestCase):
    """
    Base test case handles temporary files and restoring old environment.

    """

    @classmethod
    def setUpClass(cls):
        cls.logger = logger.get_logger(cls.__name__)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_env = os.environ.copy()

    def temp_file_path(self, *args):
        return os.path.join(self.temp_dir.name, *args)

    def tearDown(self):
        self.temp_dir.cleanup()
        self.restore_old_env()

    def restore_old_env(self):
        new_env_keys = set(os.environ.keys())
        old_env_keys = set(self.old_env.keys())
        for key in (new_env_keys - old_env_keys):
            del os.environ[key]
        for key in old_env_keys.intersection(new_env_keys):
            os.environ[key] = self.old_env[key]
