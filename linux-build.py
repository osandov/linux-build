#!/usr/bin/env python3

"""
Build and install the latest Linux kernel release candidate.
"""

import argparse
import sys

from multiprocessing import cpu_count

from linuxbuild.download import list_releases, download_release
from linuxbuild.make import CONFIG_TARGETS, configure_kernel, make_kernel
from linuxbuild.install import INITRDS, BOOTLOADERS, install_kernel
from linuxbuild.uninstall import uninstall_kernel


def main():
    parser = argparse.ArgumentParser(
        description='Build and install the Linux kernel.')
    subparsers = parser.add_subparsers(
        title='build phases', description='phases in the build process', dest='phase')
    subparsers.required = True

    parser_list = subparsers.add_parser('list', help='list available kernel releases')
    parser_list.add_argument(
        '--limit', '-n', type=int, default=0,
        help='number of releases to show per moniker (defaults to 0, for all)')
    parser_list.add_argument(
        'moniker', metavar='MONIKER', nargs='?',
        help='kernel release category (e.g., mainline, stable, longterm)')
    parser_list.set_defaults(func=cmd_list)

    parser_download = subparsers.add_parser('download', help='download the kernel source')
    parser_download.add_argument(
        '--skip-verify', action='store_true',
        help="don't verify the source tarball")
    parser_download.add_argument('version', metavar='VERSION', help='kernel release version')
    parser_download.set_defaults(func=cmd_download)

    parser_config = subparsers.add_parser('config', help='configure the kernel')
    parser_config.add_argument(
        '--old-config', '-O', metavar='CONFIG', help='old .config file to copy')
    parser_config.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_config.add_argument(
        'target', metavar='TARGET', choices=CONFIG_TARGETS,
        help='configuration target (e.g., menuconfig, oldconfig, olddefconfig)')
    parser_config.set_defaults(func=cmd_config)

    parser_make = subparsers.add_parser('make', help='build the kernel')
    parser_make.add_argument(
        '--jobs', '-j', type=int, default=cpu_count(),
        help='number of make jobs to run simultaneously (defaults to number of CPU cores)')
    parser_make.add_argument(
        '--log', '-l', default='make.log', help='log file for make stdout and stderr')
    parser_make.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_make.set_defaults(func=cmd_make)

    parser_install = subparsers.add_parser('install', help='install the kernel')
    parser_install.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_install.add_argument('name', metavar='NAME', help='installed kernel name')
    parser_install.add_argument(
        '--initrd', '-i', choices=INITRDS, required=True, help='initial ramdisk scheme')
    parser_install.add_argument(
        '--bootloader', '-b', choices=BOOTLOADERS, required=True, help='bootloader')
    parser_install.set_defaults(func=cmd_install)

    parser_uninstall = subparsers.add_parser('uninstall', help='uninstall the kernel')
    parser_uninstall.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_uninstall.add_argument('name', metavar='NAME', help='installed kernel name')
    parser_uninstall.add_argument(
        '--initrd', '-i', choices=INITRDS, required=False, help='initial ramdisk scheme')
    parser_uninstall.add_argument(
        '--bootloader', '-b', choices=BOOTLOADERS, required=False, help='bootloader')
    parser_uninstall.set_defaults(func=cmd_uninstall)

    args = parser.parse_args()
    args.func(args)


def cmd_list(args):
    list_releases(args.moniker, args.limit)


def cmd_download(args):
    source = download_release(args.version, not args.skip_verify)
    print()
    print('Run `%s config [options] %s TARGET` to configure the kernel.' % (sys.argv[0], source))


def cmd_config(args):
    configure_kernel(args.source, args.target, args.old_config)
    print()
    print('Run `%s make [options] %s` to build the kernel.' % (sys.argv[0], args.source))


def cmd_make(args):
    make_kernel(args.source, args.log, args.jobs)
    print()
    print('Run `sudo %s install [options] %s` to install the kernel.' % (sys.argv[0], args.source))


def cmd_install(args):
    install_kernel(args.source, args.name, initrd=args.initrd, bootloader=args.bootloader)


def cmd_uninstall(args):
    uninstall_kernel(args.source, args.name, initrd=args.initrd, bootloader=args.bootloader)


if __name__ == '__main__':
    main()
