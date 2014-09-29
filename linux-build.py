#!/usr/bin/env python3

"""
Build and install the latest Linux kernel release candidate.
"""

import argparse

from multiprocessing import cpu_count

from linuxbuild.download import list_releases, download_latest_release
from linuxbuild.make import CONFIG_TARGETS, configure_kernel, make_kernel
from linuxbuild.install import install_kernel


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Build and install the Linux kernel.')
    subparsers = parser.add_subparsers(
        title='build phases', description='phases in the build process', dest='phase')

    parser_list = subparsers.add_parser('list', help='list available kernel releases')
    parser_list.add_argument(
        '--limit', '-n', type=int, default=0,
        help='number of releases to show per moniker (defaults to 0, for all)')
    parser_list.add_argument(
        'moniker', metavar='MONIKER', nargs='?',
        help='kernel release category (e.g., mainline, stable, longterm)')
    parser_list.set_defaults(func=list_releases)

    parser_download = subparsers.add_parser('download', help='download the kernel source')
    parser_download.add_argument(
        '--skip-verify', action='store_true',
        help="don't verify the source tarball")
    parser_download.add_argument('version', metavar='VERSION', help='kernel release version')
    parser_download.set_defaults(func=download_latest_release)

    parser_config = subparsers.add_parser('config', help='configure the kernel')
    parser_config.add_argument(
        '--old-config', '-O', metavar='CONFIG', help='old .config file to copy')
    parser_config.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_config.add_argument(
        'target', metavar='TARGET', choices=CONFIG_TARGETS,
        help='configuration target (e.g., menuconfig, oldconfig, olddefconfig)')
    parser_config.set_defaults(func=configure_kernel)

    parser_make = subparsers.add_parser('make', help='build the kernel')
    parser_make.add_argument(
        '--jobs', '-j', type=int, default=cpu_count() - 1,
        help='number of make jobs to run simultaneously (defaults to number of CPU cores - 1)')
    parser_make.add_argument(
        '--log', '-l', default='make.log', help='log file for make stdout and stderr')
    parser_make.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_make.set_defaults(func=make_kernel)

    parser_install = subparsers.add_parser('install', help='install the kernel')
    # TODO: more arguments so this works for more than Arch Linux on x86.
    parser_install.add_argument('source', metavar='SOURCEDIR', help='kernel source directory')
    parser_install.add_argument('name', metavar='NAME', help='installed kernel name')
    parser_install.set_defaults(func=install_kernel)

    args = parser.parse_args()
    args.func(args)
