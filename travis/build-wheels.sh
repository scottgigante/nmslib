#!/bin/bash
set -e -x

# Install a system package required by our library
yum install -y atlas-devel

cwd=$(pwd)
cd /io/python_bindings
# Compile wheels
for PYBIN in /opt/python/*/bin; do
    if [ $("${PYBIN}/python" --version | sed 's/\.//g' | grep -c "Python ${PYTHON}") -eq 0 ]; then
        continue
    fi
    "${PYBIN}/pip" install -r dev-requirements.txt
    "${PYBIN}/python" setup.py build_ext
    "${PYBIN}/pip" wheel . -w ${cwd}/wheelhouse/
done
cd $cwd

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/python_bindings/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    if [ $("${PYBIN}/python" --version | sed 's/\.//g' | grep -c "Python ${PYTHON}") -eq 0 ]; then
        continue
    fi
    "${PYBIN}/pip" install nmspy --no-index -f /io/python_bindings/wheelhouse
    "${PYBIN}/python" -c 'import nmspy; print(nmspy.__version__)'
done

