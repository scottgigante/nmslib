#!/bin/bash
set -e -x

# Install a system package required by our library
yum install -y atlas-devel
yum install -y gsl-devel
yum install -y boost-devel
yum install -y libgomp-devel

mkdir -p /io/python_bindings/wheelhouse/
for PYBIN in /opt/python/*/bin; do
    # Select python version corresponding to this test
    if [ $("${PYBIN}/python" --version 2>&1 | grep -c "Python ${PYTHON}") -eq 0 ]; then
        continue
    fi

    # Compile wheels
    cd /io/python_bindings
    "${PYBIN}/pip" install -r dev-requirements.txt
    "${PYBIN}/python" setup.py build_ext
    mkdir -p wheelhouse_tmp/${PYBIN}
    mkdir -p wheelhouse_repair/${PYBIN}
    "${PYBIN}/pip" wheel . -w wheelhouse_tmp/${PYBIN}

    # Bundle external shared libraries into the wheels
    auditwheel repair $(ls wheelhouse_tmp/${PYBIN}/*.whl) --plat $PLAT -w wheelhouse_repair/${PYBIN}

    # Install and test
    "${PYBIN}/pip" install nmspy --no-index -f wheelhouse_repair/${PYBIN}/
    cd /io/python_bindings/tests/
    "${PYBIN}/python" -m pytest

    # Clean up
    "${PYBIN}/pip" uninstall nmspy
    rm -rf ../build
    
    # Move wheel to output directory
    mv wheelhouse_repair/${PYBIN}/*.whl /io/python_bindings/wheelhouse/
done

