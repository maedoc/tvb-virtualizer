# -*- coding: utf-8 -*-

"""
Prepare bnm Python package for setup.
"""

import shutil
from setuptools import setup, find_packages


setup(
    name="bnm",
    description="Brain Network Models - Reconstruction tool from structural MR scans",
    packages=find_packages(),
    version="1.0",
    license="Apache 2.0",
    author="BNM Team",
    install_requires=["numpy", "nibabel", "matplotlib", "meshcut", "pegasus-wms"]
)

shutil.rmtree('bnm.egg-info', True)
