#!/usr/bin/env bash

# Steps bellow worked for OS X Yosemite (10.10.5) Mid October 2016.

# Some packages can be downloaded with Brew directly
brew install cmake
brew install homebrew/science/libmatio
brew install eigen
brew install qt
brew linkapps qt
export PATH="/usr/local/opt/qt/bin:$PATH"

# Mrtrix needs to be installed from their repo
git clone https://github.com/MRtrix3/mrtrix3
cd mrtrix3
export EIGEN_CFLAGS="-isystem /usr/local/include/eigen3"
./configure
./build
export PATH="/WORK/BEM/software/mrtrix/release/bin:/WORK/BEM/software/mrtrix/scripts:$PATH"

# Download fslinstaller.py (registration needed) from here: http://fsl.fmrib.ox.ac.uk/fsldownloads/fsldownloadmain.html
python fslinstaller.py
export FSLDIR=/WORK/BEM/software/fsl

# Install MNE from dmg (after registration) http://www.nmr.mgh.harvard.edu/martinos/userInfo/data/MNE_register/index.php
export MNE_ROOT=/Applications/MNE-2.7.4-3378-MacOSX-x86_64
source ${MNE_ROOT}/bin/mne_setup

# Download FreeSurfer Nightly build and install: ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/dev
export FREESURFER_HOME=/Applications/freesurfer_dev
source ${FREESURFER_HOME}/SetUpFreeSurfer.sh