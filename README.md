linux-build
===========
linux-build.py is a script for easily downloading, compiling, and installing
the Linux kernel. I built it mostly to take the tediousness out of the download
and installation steps. It does very little for you beyond that, and at any
step, things can be done manually.

This is how I use it to install the latest RC kernel:

```
linux-build.py download mainline
linux-build.py config --old-config linux-3.17-rc6/.config linux-3.17-rc7 olddefconfig
linux-build.py make -j8 linux-3.17-rc7
sudo linux-build.py install linux-3.17-rc7 mainline
```

Note: this interface isn't stable; I'm still tweaking it as I figure out what
my use cases are.
