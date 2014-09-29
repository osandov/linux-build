linux-build
===========
linux-build.py is a script for easily downloading, compiling, and installing
the Linux kernel. I built it mostly to take the tediousness out of the download
and installation steps. It does very little for you beyond that, and at any
step, things can be done manually.

This is how I use it to install the latest RC kernel (see build-latest-rc.sh):

```sh
VERSION="$(linux-build.py list -n 1 mainline)"
linux-build.py download "$VERSION"
linux-build.py config --old-config ~/linux-config "linux-$VERSION" olddefconfig
linux-build.py make "linux-$VERSION"
sudo linux-build.py install "linux-$VERSION" mainline
```

Note: this interface isn't stable; I'm still tweaking it as I figure out what
my use cases are.
