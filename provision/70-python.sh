#!/usr/bin/env bash

# bootstrap recent Python, assuming sane dev env & ssl headers

# if on macos check for ssl header, suggest install
if [[ "$(uname)" == "Darwin" ]]
then
    echo "[70-python.sh] uname is Darwin, checking for openssl headers.."
    if [[ -f /usr/local/opt/openssl/include/openssl/ssl.h ]]
    then
        echo "[70-python.sh] openssl headers present, good to go."
        export LDFLAGS="-L/usr/local/opt/openssl/lib $LDFLAGS"
        export CFLAGS="-I/usr/local/opt/openssl/include $CFLAGS"
        echo "[70-python.sh] LDFLAGS=$LDFLAGS"
        echo "[70-python.sh] CFLAGS=$CFLAGS"
    else
        echo "[70-python.sh] openssl headers not found."
        echo "[70-python.sh] consider \`brew install openssl\`."
    fi
fi

set -eu
set -o pipefail

export PREFIX=${PREFIX:-"/work/env"}
mkdir -p $PREFIX/src
pushd $PREFIX/src

    # this is awkward. but, it avoids having to know where the script is
    cat > soname-bzip.patch <<EOF
38c38
< 	\$(CC) -shared -Wl,-soname -Wl,libbz2.so.1.0 -o libbz2.so.1.0.6 \$(OBJS)
---
> 	\$(CC) -shared -o libbz2.so.1.0.6 \$(OBJS)
EOF

    if [[ ! -z $(which jupyter) ]]
    then
        echo "[70-python.sh] jupyter found, not setting up Python env."
        exit 0
    else
        echo "[70-python.sh] building Python env."
    fi

    j=${j:-"6"}

    zver=1.2.11
    zlib_url=http://zlib.net/zlib-$zver.tar.gz

    bzver=1.0.6
    bzip_url=http://www.bzip.org/$bzver/bzip2-$bzver.tar.gz

    sql_url=https://sqlite.org/2017/sqlite-autoconf-3160200.tar.gz

    pyver=3.6.0
    Py_url=https://www.python.org/ftp/python/$pyver/Python-$pyver.tgz

    for pkg in zlib bzip sql Py
    do
        if [[ -z "$(which curl)" ]]
        then
            wget $(eval echo \$${pkg}_url)
        else
            curl -O $(eval echo \$${pkg}_url)
        fi
        tar xzf ${pkg}*
        pushd ${pkg}*
        if [[ $pkg == "bzip" ]]
        then
            patch Makefile-libbz2_so ../soname-bzip.patch
            make -j$j -f Makefile-libbz2_so
            make -j$j install PREFIX=$PREFIX
            cp libbz2.so* $PREFIX/lib
        else
            ./configure --prefix=$PREFIX
            make -j$j
            make install
        fi
        popd
    done


    py_pkgs="numpy scipy matplotlib cython scikit-learn pandas h5py nibabel"
    py_pkgs="$py_pkgs nibabel anytree trimesh flake8 mypy mne jupyterlab"
    py_pkgs="$py_pkgs gdist pytest pytest-cov autopep8"

    for pkg in $py_pkgs
    do
        echo "pip installing $pkg"
        $PREFIX/bin/pip3 install $pkg
    done

    if [[ -d /vagrant ]]
    then
        $PREFIX/bin/jupyter serverextension enable --py jupyterlab --sys-prefix

        # consider focusing on jupyter/notebook for visualizations are required

        # finally set up recon tools package for work
        echo TODO pushd /vagrant
        echo TODO $PREFIX/bin/python setup.py develop
    fi

popd # $PREFIX/src
