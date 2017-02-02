#!/usr/bin/env bash

set -eu
set -o pipefail

export PREFIX=${PREFIX:-"/work/env"}

if [[ ! -z $(echo $PATH | grep '/vagrant/bin') ]]
then
    echo "[00-system.sh] found /vagrant/bin in \$PATH, skipping setup."
    exit 0
fi

# TODO port to ansible

apt-get update && apt-get upgrade -y

# http://neuro.debian.net/install_pkg.html?p=fsl-complete
wget -O- http://neuro.debian.net/lists/xenial.de-m.full | sudo tee /etc/apt/sources.list.d/neurodebian.sources.list
apt-key adv --recv-keys --keyserver hkp://pgp.mit.edu:80 0xA5D32F012649A5A9
apt-get update

apt-get install -y cmake tcsh libeigen3-dev liblapack-dev libblas-dev libssl-dev fsl-complete

# setup work partition
if [[ -d $PREFIX ]]
then
    echo "$PREFIX setup, skipping."
else
    parted /dev/sdc mklabel msdos
    parted /dev/sdc mkpart primary 512 100%
    mkfs.xfs /dev/sdc1
    
    prefix_base=$(dirname $PREFIX)
    mkdir $prefix_base
    echo "/dev/sdc1 $prefix_base xfs noatime,nobarrier 0 0" >> /etc/fstab
    mount $prefix_base
    mkdir $PREFIX
    chown -R ubuntu:ubuntu $prefix_base
fi
    
# setup /work/env/lib as system wide library location
echo /work/env/lib > /etc/ld.so.conf.d/work.conf
ldconfig

cp /vagrant/provision/jupyter-lab.service /etc/systemd/system/

cat >> /etc/bash.bashrc <<EOF
export PREFIX=$PREFIX
export FREESURFER_HOME=\$PREFIX/freesurfer
export SUBJECTS_DIR=/work/data
export PATH=\$PREFIX/bin:\$PATH
source \$FREESURFER_HOME/FreeSurferEnv.sh

export MRT3=\$PREFIX/src/mrtrix3
export PATH=\$MRT3/release/bin:\$MRT3/scripts:\$PATH

export PATH=\$PREFIX/mne/bin:\$PATH
export MNE_ROOT=\$PREFIX/mne
source \$MNE_ROOT/bin/mne_setup_sh

export PATH=/vagrant/bin:\$PATH
EOF
