"""
Download a kernel source tarball from kernel.org.
"""

import http.client
import json
import os
import os.path
import subprocess
import sys
import urllib.parse
import urllib.request

from collections import OrderedDict

from linuxbuild import _prompt_yes_no


def list_releases(args):
    """
    List currently available releases.
    """

    releases = get_releases()

    if args.moniker is None:
        releases_by_moniker = OrderedDict()

        for release in releases['releases']:
            releases_by_moniker.setdefault(release['moniker'], []).append(release)

        first = True
        for moniker, r in releases_by_moniker.items():
            if not first:
                print()
            first = False

            print('%s:' % moniker)
            for release in r[:args.limit] if args.limit > 0 else r:
                print(release['version'])
    else:
        r = get_releases_by_moniker(releases, args.moniker)
        for release in r[:args.limit] if args.limit > 0 else r:
            print(release['version'])


def download_latest_release(args):
    """
    Download, verify, and decompress the given kernel release from kernel.org,
    returning the untarred source path.
    """

    print('Getting release information...')
    releases = get_releases()
    version = args.version

    for release in releases['releases']:
        if release['version'] == version:
            break
    else:
        print('Version %s not found.' % version, file=sys.stderr)
        sys.exit(1)

    print('Found version %s.' % (version))
    if not _prompt_yes_no('Download and extract?'):
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


def get_releases():
    """
    Get the latest kernel release information, provided by kernel.org.
    """

    with urllib.request.urlopen('https://www.kernel.org/releases.json') as f:
        return json.loads(f.read().decode('utf-8'), object_pairs_hook=OrderedDict)


def get_releases_by_moniker(releases, moniker):
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
