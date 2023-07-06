#!/bin/bash

PRECICE_PREFIX=~/software/prefix # set this to your selected prefix
export PATH=$PRECICE_PREFIX/bin:$PATH
export LD_LIBRARY_PATH=$PRECICE_PREFIX/lib:$LD_LIBRARY_PATH
export CPATH=$PRECICE_PREFIX/include:$CPATH
# Enable detection with pkg-config and CMake
export PKG_CONFIG_PATH=$PRECICE_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH
export CMAKE_PREFIX_PATH=$PRECICE_PREFIX:$CMAKE_PREFIX_PATH

_main "$@"