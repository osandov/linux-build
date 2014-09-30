"""
Install the Linux kernel.
"""

import os
import subprocess

from linuxbuild import _prompt_yes_no, _echo_call

# Initial file system creation tools that the installer knows about.
INITRDS = [
    'mkinitcpio',  # Arch Linux initramfs tool
]

# Bootloaders that the installer knows about.
BOOTLOADERS = [
    'grub',  # GNU GRand Unified Bootloader
]

# TODO: add support for more initrd schemes/bootloaders.


def install_kernel(source, name, initrd, bootloader):
    """
    Install the kernel.

    Arguments:
    source -- Kernel source directory
    name -- Name of the installed kernel
    """

    assert initrd in INITRDS
    assert bootloader in BOOTLOADERS

    os.chdir(source)

    kernelrelease = subprocess.check_output(['make', '-s', 'kernelrelease'])
    kernelrelease = kernelrelease.decode('utf-8').strip()

    image_name = subprocess.check_output(['make', '-s', 'image_name'])
    image_name = image_name.decode('utf-8').strip()

    if not _prompt_yes_no('Install %s as %s?' % (kernelrelease, name)):
        raise ValueError('User aborted.')

    # Install the kernel modules.
    _echo_call(['make', 'modules_install'])

    # Install the kernel image.
    _echo_call(['cp', image_name, '/boot/vmlinuz-%s' % name])

    # Create the initial ramdisk.
    if initrd == 'mkinitcpio':
        _echo_call(
            ['mkinitcpio', '-k', kernelrelease, '-c', '/etc/mkinitcpio.conf',
             '-g', '/boot/initramfs-%s.img' % name])
    else:
        assert False

    # Update the bootloader.
    if bootloader == 'grub':
        _echo_call(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])
    else:
        assert False

    print()
    print('Linux %s installed as %s.' % (kernelrelease, name))
