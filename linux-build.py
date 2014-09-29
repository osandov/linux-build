#!/usr/bin/env python3

"""
Build and install the latest Linux kernel release candidate.
"""

import argparse
import http.client
import json
import os
import os.path
import shutil
import subprocess
import sys
import urllib.request
import urllib.parse

from multiprocessing import cpu_count


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


def main():
    parser = argparse.ArgumentParser(
        description='Build and install the latest Linux kernel release candidate.')
    subparsers = parser.add_subparsers(
        title='build phases', description='phases in the build process', dest='phase')

    parser_download = subparsers.add_parser('download', help='download the kernel source')
    parser_download.add_argument(
        '--skip-verify', action='store_true',
        help="don't verify the source tarball")
    parser_download.add_argument(
        'moniker', metavar='MONIKER',
        help='kernel release category (e.g., mainline, stable, longterm)')
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
        '--jobs', '-j', type=int, default=cpu_count(),
        help='number of make jobs to run simultaneously (defaults to number of CPU cores)')
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


def download_latest_release(args):
    """
    Download, verify, and decompress the latest kernel release with the given
    moniker, returning the untarred source path.
    """

    print('Getting release information...')
    releases = get_releases()
    moniker = args.moniker

    releases = get_release_by_moniker(releases, moniker)
    if not releases:
        print('No %s releases found.' % moniker, file=sys.stderr)
        sys.exit(1)

    release = get_latest_release(releases)
    print('Latest %s kernel is %s.' % (moniker, release['version']))
    if not prompt_yes_no('Download and extract?'):
        sys.exit(1)

    print()
    print('Downloading release...')
    source_xz = download_release_source(release)
    print('Downloaded release to %s.' % source_xz)

    print()
    print('Decompressing release...')
    source_tarball = decompress_release_source(source_xz)
    print('Decompressed tarball to %s.' % source_tarball)

    if not args.skip_verify:
        print()
        print('Verifying release...')
        verify_release_source(release)
        print('Release verified successfully.')

    print()
    print('Untarring release...')
    source_path = untar_release_source(source_tarball)
    print('Extracted source to %s.' % source_path)

    print()
    print('Run `%s config [options] %s` to configure the kernel.' % (sys.argv[0], source_path))


def prompt_yes_no(prompt, default='yes'):
    """
    Prompt yes or no to a question.
    """
    if default is None:
        default = ''
        prompt_yn = '[y/n]'
    elif default == 'yes':
        prompt_yn = '[Y/n]'
    elif default == 'no':
        prompt_yn = '[y/N]'
    else:
        raise ValueError('invalid default')
    while True:
        answer = input('%s %s ' % (prompt, prompt_yn)).strip().lower()
        if not answer:
            answer = default
        if answer.startswith('y'):
            return True
        elif answer.startswith('n'):
            return False


def get_releases():
    """
    Get the latest kernel release information, provided by kernel.org.
    """

    with urllib.request.urlopen('https://www.kernel.org/releases.json') as f:
        return json.loads(f.read().decode('utf-8'))


def get_release_by_moniker(releases, moniker):
    """
    Get a list of kernel releases with the given moniker.
    """

    return [release for release in releases['releases'] if release['moniker'] == moniker]


def get_latest_release(release_list):
    """
    Get the latest release in a list of releases.
    """

    return max(release_list, key=lambda x: x['released']['timestamp'])


def download_release_source(release):
    """
    Downlad the given kernel release source and signature into the current
    directory and return the path the source was downloaded to.
    """

    source = release['source']
    source_parse = urllib.parse.urlparse(source)
    assert source_parse.scheme == 'https'
    source_xz = os.path.basename(source_parse.path)

    # Workaround because curl errors out when you try to continue a download of
    # a fully-downloaded file :(
    try:
        stat = os.stat(source_xz)
        conn = http.client.HTTPSConnection(source_parse.netloc)
        conn.request('HEAD', source_parse.path)
        res = dict(conn.getresponse().getheaders())
        content_length = int(res['Content-Length'])
        if content_length == stat.st_size:
            print('Tarball already downloaded.')
            return source_xz
    except FileNotFoundError:
        pass

    # Use curl so we get continuation and a progress bar without having to
    # implement any of it :)
    subprocess.check_call(['curl', '-C', '-', '-o', source_xz, source])

    return source_xz


def decompress_release_source(source_xz):
    """
    Decompress the kernel source at the given path, returning the decompressed
    tarball path.
    """

    dest_path, ext = os.path.splitext(source_xz)
    assert ext == '.xz'  # TODO: support other compression types?

    with open(source_xz, 'rb') as src, open(dest_path, 'wb') as dst:
        subprocess.check_call(['xz', '-cd'], stdin=src, stdout=dst)

    return dest_path


def verify_release_source(release):
    """
    Verify the given kernel release source tarball. The decompressed source
    tarball must be in the current directory.
    """

    pgp = release['pgp']
    pgp_parse = urllib.parse.urlparse(pgp)
    assert pgp_parse.scheme == 'https'
    pgp_path = os.path.basename(pgp_parse.path)

    urllib.request.urlretrieve(pgp, pgp_path)

    subprocess.check_call(['gpg', '--verify', pgp_path])


def untar_release_source(source_tarball):
    """
    Untar the given kernel release source tarball into the current directory,
    returning the untarred path.
    """

    path, ext = os.path.splitext(source_tarball)
    subprocess.check_call(['tar', '-xf', source_tarball])

    # All we can do is assume the resulting path has the same name as the
    # tarball.
    return path


def configure_kernel(args):
    """
    Configure the kernel.
    """

    os.chdir(args.source)

    if args.old_config:
        shutil.copyfile(args.old_config, '.config')

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
        print('make exited with status %d' % returcode, file=sys.stderr)
        sys.exit(returncode)

    returncode = tee.wait()
    if returncode:
        print('tee exited with status %d' % returcode, file=sys.stderr)
        sys.exit(returncode)

    print('Run `sudo %s install [options] %s` to install the kernel.' % (sys.argv[0], args.source))


def install_kernel(args):
    """
    Install the kernel.
    """

    def echo_call(args):
        print(' '.join(args))
        subprocess.check_call(args)

    os.chdir(args.source)

    kernelrelease = subprocess.check_output(['make', '-s', 'kernelrelease'])
    kernelrelease = kernelrelease.decode('utf-8').strip()

    # Install the kernel modules.
    echo_call(['make', 'modules_install'])

    # Install the kernel image.
    echo_call(['cp', 'arch/x86/boot/bzImage', '/boot/vmlinuz-%s' % args.name])

    # Create the initramfs image.
    echo_call(
        ['mkinitcpio', '-k', kernelrelease, '-c', '/etc/mkinitcpio.conf',
         '-g', '/boot/initramfs-%s.img' % args.name])

    # Update GRUB.
    echo_call(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'])

if __name__ == '__main__':
    main()
