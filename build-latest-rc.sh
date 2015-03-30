#!/bin/sh

usage () {
    USAGE_STRING="Usage: $0 [-i] OLDCONFIG
       $0 -h

Build and optionally install the latest Linux RC kernel.

Installation:
  -i    Also install the kernel, assuming mkinitcpio and grub (requires sudo)

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

shift $((OPTIND - 1))
if [ $# -ne 1 ]; then
	usage "err"
fi

OLDCONFIG="$1"

set -e

VERSION="$(linux-build.py list -n 1 mainline)"
linux-build.py download "$VERSION"
linux-build.py config --old-config "$OLDCONFIG" "linux-$VERSION" olddefconfig
cp "linux-$VERSION"/.config "$OLDCONFIG"
linux-build.py make "linux-$VERSION"
if [ ! -z "$INSTALL" ]; then
    sudo linux-build.py install --initrd=mkinitcpio --bootloader=grub "linux-$VERSION" mainline
fi
rm "linux-${VERSION}.tar" "linux-${VERSION}.tar.xz" "linux-${VERSION}.tar.sign"
