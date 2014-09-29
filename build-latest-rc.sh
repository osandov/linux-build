#!/bin/sh

usage () {
    USAGE_STRING="Usage: $0 [-i]
       $0 -h

Build and optionally install the latest Linux RC kernel.

Installation:
  -i    Also install the kernel (requires sudo)

Miscellaneous:
  -h    Display this help message and exit"

    case "$1" in
        out)
            echo "$USAGE_STRING"
            exit 0
            ;;
        err)
            echo "$USAGE_STRING" >&2
            exit 1
            ;;
    esac
}

while getopts ":ih" OPT; do
    case "$OPT" in
        i)
            INSTALL=1
            ;;
        h)
            usage "out"
            ;;
        *)
            usage "err"
            ;;
    esac
done

set -e

VERSION="$(linux-build.py list -n 1 mainline)"
linux-build.py download "$VERSION"
linux-build.py config --old-config ~/linux-config "linux-$VERSION" olddefconfig
cp "linux-$VERSION"/.config ~/linux-config
linux-build.py make "linux-$VERSION"
if [ ! -z "$INSTALL" ]; then
    sudo linux-build.py install "linux-$VERSION" mainline
fi
