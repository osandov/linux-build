"""
Configure and build the Linux kernel.
"""

import os
import shutil
import subprocess
import sys

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


def configure_kernel(args):
    """
    Configure the kernel.
    """

    if args.old_config:
        shutil.copyfile(args.old_config, os.path.join(args.source, '.config'))

    os.chdir(args.source)

    subprocess.check_call(['make', args.target])

    print('Run `%s make [options] %s` to build the kernel.' % (sys.argv[0], args.source))


def make_kernel(args):
    """
    Build the kernel.
    """

    os.chdir(args.source)

    make = subprocess.Popen(
        ['make', '-j', str(args.jobs)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    tee = subprocess.Popen(['tee', args.log], stdin=make.stdout)
    make.stdout.close()

    returncode = make.wait()
    if returncode:
        print('make exited with status %d' % returncode, file=sys.stderr)
        sys.exit(returncode)

    returncode = tee.wait()
    if returncode:
        print('tee exited with status %d' % returncode, file=sys.stderr)
        sys.exit(returncode)

    print('Run `sudo %s install [options] %s` to install the kernel.' % (sys.argv[0], args.source))
