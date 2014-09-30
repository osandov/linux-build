"""
Configure and build the Linux kernel.
"""

import os
import shutil
import subprocess

# Configuration make targets (from Linux make help).
CONFIG_TARGETS = [
    'config',
    'nconfig',
    'menuconfig',
    'xconfig',
    'gconfig',
    'oldconfig',
    'localmodconfig',
    'localyesconfig',
    'silentoldconfig',
    'defconfig',
    'savedefconfig',
    'allnoconfig',
    'allyesconfig',
    'allmodconfig',
    'alldefconfig',
    'randconfig',
    'listnewconfig',
    'olddefconfig',
]


def configure_kernel(source, target, old_config=None):
    """
    Configure the kernel.

    Arguments:
    source -- Kernel source directory
    target -- Kernel configuration target. Must be one of CONFIG_TARGETS
    old_config -- Old configuration file to copy
    """

    assert target in CONFIG_TARGETS

    if old_config:
        shutil.copyfile(old_config, os.path.join(source, '.config'))

    os.chdir(source)

    subprocess.check_call(['make', target])


def make_kernel(source, log=None, jobs=1):
    """
    Build the kernel.

    Arguments:
    source -- Kernel source directory
    log -- Log file for stdout and stderr from make
    jobs -- Number of jobs to run simultaneously (i.e., make -j)
    """

    os.chdir(source)

    make_args = ['make', '-j', str(jobs)]
    make = subprocess.Popen(make_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    tee_args = ['tee', log]
    tee = subprocess.Popen(tee_args, stdin=make.stdout)
    make.stdout.close()

    returncode = make.wait()
    if returncode:
        raise subprocess.CalledProcessError(cmd=make_args, returncode=returncode)

    returncode = tee.wait()
    if returncode:
        raise subprocess.CalledProcessError(cmd=tee_args, returncode=returncode)
