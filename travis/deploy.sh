#!/bin/bash

git clean -fxd
git clean -fXd   
mv .pypirc ~/.pypirc
$PIP install --user twine
if [ "$TRAVIS_OS_NAME" == "linux" ]; then
    # manylinux build
    echo "Building manylinux wheels with auditwheel and docker"
    for PLAT in manylinux1_x86_64 manylinux1_i686 manylinux2010_x86_64; do
        DOCKER_IMAGE=quay.io/pypa/$PLAT
        if [ "$PLAT" == "manylinux1_i686" ]; then
            PRE_CMD=linux32
        else
            PRE_CMD=""
        fi
        docker pull $DOCKER_IMAGE
    docker run --rm -v `pwd`:/io -e PLAT=$PLAT -e PYTHON=$PYTHON $DOCKER_IMAGE $PRE_CMD /io/travis/build-wheels.sh
    done
    WHEEL_DIR="wheelhouse"
else
    # os x build
    echo "Building Mac OS wheels natively"
    set -x
    cd python_bindings
    echo "cd success"
    $PIP install --user -r dev-requirements.txt
    echo "pip success"
    $PY setup.py build_ext
    echo "build success"
    $PY setup.py sdist bdist_wheel
    echo "wheel success"
    WHEEL_DIR="dist"
    cd ..
fi
cd python_bindings
$PY -m twine upload -r pypi -p $PYPI_PASSWORD --skip-existing ${WHEEL_DIR}/*
