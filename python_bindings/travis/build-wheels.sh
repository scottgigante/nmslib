#!/bin/bash
set -e -x

# Install a system package required by our library
yum install -y atlas-devel

cwd=$(pwd)
cd /io
# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -r /io/dev-requirements.txt
    "${PYBIN}/python" setup.py build_ext
    "${PYBIN}/pip" wheel /io/ -w ${cwd}/wheelhouse/
done
cd $cwd

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    "${PYBIN}/pip" install nmspy --no-index -f /io/wheelhouse
    "${PYBIN}/python" -c 'import nmspy; print(nmspy.__version__)'
done
