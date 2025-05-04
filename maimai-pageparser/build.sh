#!/bin/env bash

# Not tested!
# For non-nix users, you need to install gopy first

cd $(dirname $0)
rm -rf ./build
gopy pkg -output=./build maimai_pageparser
echo "from .maimai_pageparser import *" >./build/maimai_pageparser/__init__.py
make -C ./build install-pkg