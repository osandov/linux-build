"""
Install the Linux kernel.
"""

import os
import subprocess

from linuxbuild import _echo_call


def install_kernel(source, name):
    """
    Install the kernel.

    Arguments:
    source -- Kernel source directory
    name -- Name of the installed kernel
    """

    os.chdir(source)

    kernelrelease = subprocess.check_output(['make', '-s', 'kernelrelease'])
    kernelrelease = kernelrelease.decode('utf-8').strip()

    # Install the kernel modules.
    _echo_call(['make', 'modules_install'])

    # Install the kernel image.
    _echo_call(['cp', 'arch/x86/boot/bzImage', '/boot/vmlinuz-%s' % name])

    # Create the initramfs image.
    _echo_call(
        ['mkinitcpio', '-k', kernelrelease, '-c', '/etc/mkinitcpio.conf',
         '-g', '/boot/initramfs-%s.img' % name])

    # Update GRUB.
    _echo_call(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
