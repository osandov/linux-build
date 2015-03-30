"""
Uninstall the Linux kernel.
"""

import os
import subprocess

from linuxbuild import _prompt_yes_no, _echo_call
from linuxbuild.install import INITRDS, BOOTLOADERS

# TODO: add support for more initrd schemes/bootloaders.


def uninstall_kernel(source, name, initrd, bootloader):
    """
    Uninstall the kernel.

    Arguments:
    source -- Kernel source directory
    name -- Name of the installed kernel, or None if the kernel image and
    ramdisk should not be uninstalled
    initrd -- Initial ramdisk scheme, or None if the ramdisk should not be
    uninstalled
    bootloader -- Bootloader scheme, or None if the bootloader should not be
    reconfigured
    """

    assert initrd is None or initrd in INITRDS
    assert bootloader is None or bootloader in BOOTLOADERS

    os.chdir(source)

    kernelrelease = subprocess.check_output(['make', '-s', 'kernelrelease'])
    kernelrelease = kernelrelease.decode('utf-8').strip()

    if name is None:
        if not _prompt_yes_no('Uninstall %s?' % kernelrelease):
            raise ValueError('User aborted.')
    else:
        if not _prompt_yes_no('Uninstall %s named %s?' % (kernelrelease, name)):
            raise ValueError('User aborted.')

    # Uninstall the kernel modules.
    _echo_call(['rm', '-r', '/lib/modules/%s' % kernelrelease])

    # Uninstall the kernel image.
    if name is not None:
        _echo_call(['rm', '/boot/vmlinuz-%s' % name])

        # Remove the initial ramdisk.
        if initrd == 'mkinitcpio':
            _echo_call(['rm', '/boot/initramfs-%s.img' % name])
        elif initrd is not None:
            assert False

    # Update the bootloader.
    if bootloader == 'grub':
        _echo_call(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
    elif bootloader is not None:
        assert False

    # Remove the source tree and old tarballs.
    os.chdir('..')
    _echo_call(['rm', '-r', source])
    _echo_call(['rm', '%s.tar' % source, '%s.tar.xz' % source, '%s.tar.sign' % source])
