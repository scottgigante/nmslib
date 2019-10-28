#!/bin/bash
set -e -x

# Install a system package required by our library
yum install -y atlas-devel
yum install -y gsl-devel
yum install -y boost-devel
yum install -y libgomp

cd /io/python_bindings
mkdir -p wheelhouse_tmp/
# Compile wheels
for PYBIN in /opt/python/*/bin; do
    if [ $("${PYBIN}/python" --version 2>&1 | grep -c "Python ${PYTHON}") -eq 0 ]; then
        continue
    fi
    "${PYBIN}/pip" install -r dev-requirements.txt
    "${PYBIN}/python" setup.py build_ext
    "${PYBIN}/pip" wheel . -w wheelhouse_tmp/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse_tmp/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/python_bindings/wheelhouse/
done

# Install packages and test
for PYBIN in /opt/python/*/bin/; do
    if [ $("${PYBIN}/python" --version 2>&1 | grep -c "Python ${PYTHON}") -eq 0 ]; then
        continue
    fi
    "${PYBIN}/pip" install nmspy --no-index -f /io/python_bindings/wheelhouse
    cd /io/python_bindings/tests/
    "${PYBIN}/python" -m pytest
done

