# Adapted from https://github.com/ziglang/zig-pypi by Rick Lupton

import string
import argparse
import os
import stat
import hashlib
import urllib.request
from pathlib import Path
from email.message import EmailMessage
from wheel.wheelfile import WheelFile, get_zipinfo_datetime
from zipfile import ZipInfo, ZIP_DEFLATED
import libarchive # from libarchive-c


# Translate RDFox platforms into Python platform descriptions
RDFOX_PYTHON_PLATFORMS = {
    'win64-x86_64': 'win_amd64',
    'macOS-x86_64': 'macosx_10_9_x86_64',
    'macOS-arm64':  'macosx_11_0_arm64',
    'linux-x86_64': 'manylinux_2_12_x86_64.manylinux2010_x86_64.musllinux_1_1_x86_64',
    'linux-arm64':  'manylinux_2_17_aarch64.manylinux2014_aarch64.musllinux_1_1_aarch64',
}

RDFOX_DOWNLOAD_BASE_URL = "https://rdfox-distribution.s3.eu-west-2.amazonaws.com/release/"


class ReproducibleWheelFile(WheelFile):
    def writestr(self, zinfo, *args, **kwargs):
        # Copied from WheelFire.writestr
        if not isinstance(zinfo, ZipInfo):
            zinfo = ZipInfo(
                zinfo, date_time=get_zipinfo_datetime()
            )
            zinfo.compress_type = self.compression
            zinfo.external_attr = (0o664 | stat.S_IFREG) << 16

        zinfo.date_time = (1980,1,1,0,0,0)
        zinfo.create_system = 3
        super().writestr(zinfo, *args, **kwargs)


def make_message(headers, payload=None):
    msg = EmailMessage()
    for name, value in headers.items():
        if isinstance(value, list):
            for value_part in value:
                msg[name] = value_part
        else:
            msg[name] = value
    if payload:
        msg.set_payload(payload)
    return msg


def write_wheel_file(filename, contents):
    with ReproducibleWheelFile(filename, 'w') as wheel:
        for member_info, member_source in contents.items():
            if not isinstance(member_info, ZipInfo):
                member_info = ZipInfo(member_info)
                member_info.external_attr = 0o644 << 16
            member_info.file_size = len(member_source)
            member_info.compress_type = ZIP_DEFLATED
            wheel.writestr(member_info, bytes(member_source))
    return filename


def write_wheel(out_dir, *, name, version, tag, metadata, description, contents, entry_points):
    wheel_name = f'{name}-{version}-{tag}.whl'
    dist_info  = f'{name}-{version}.dist-info'

    return write_wheel_file(os.path.join(out_dir, wheel_name), {
        **contents,
        f'{dist_info}/METADATA': make_message({
            'Metadata-Version': '2.1',
            'Name': name,
            'Version': version,
            **metadata,
        }, description),
        f'{dist_info}/WHEEL': make_message({
            'Wheel-Version': '1.0',
            'Generator': 'ziglang make_wheels.py',
            'Root-Is-Purelib': 'false',
            'Tag': tag,
        }),
        f'{dist_info}/entry_points.txt': entry_points,
    })


def write_rdfox_wheel(out_dir, *, version, platform, archive):
    contents = {}
    contents['rdfox/__init__.py'] = b''


    with libarchive.memory_reader(archive) as archive:
        for entry in archive:
            entry_name = '/'.join(entry.name.split('/')[1:])
            if entry.isdir or not entry_name:
                continue

            zip_info = ZipInfo(f'rdfox/{entry_name}')
            zip_info.external_attr = (entry.mode & 0xFFFF) << 16
            contents[zip_info] = b''.join(entry.get_blocks())

            if entry_name.startswith('RDFox'):
                contents['rdfox/__main__.py'] = f'''\
import os, sys
def main():
    argv = [os.path.join(os.path.dirname(__file__), "{entry_name}"), *sys.argv[1:]]
    if os.name == 'posix':
        os.execv(argv[0], argv)
    else:
        import subprocess; sys.exit(subprocess.call(argv))
if __name__ == "__main__":
    main()
'''.encode('ascii')

    with open('README.pypi.md') as f:
        description = f.read()

    entry_points = b'''\
[console_scripts]
RDFox = rdfox.__main__:main
'''

    return write_wheel(out_dir,
        name='rdfox',
        version=version,
        tag=f'py3-none-{platform}',
        metadata={
            'Summary': 'RDFox is a high performance knowledge graph and semantic reasoning engine.',
            'Description-Content-Type': 'text/markdown',
            'Classifier': [],
            'Project-URL': [
                'Homepage, https://www.oxfordsemantic.tech/product',
                'Source Code, https://github.com/ricklupton/rdfox-pypi',
                'Bug Tracker, https://github.com/ricklupton/rdfox-pypi/issues',
            ],
            'Requires-Python': '~=3.5',
        },
        description=description,
        contents=contents,
        entry_points=entry_points,
    )


def rdfox_version_to_python_version(rdfox_version):
    last_char = rdfox_version[-1].lower()
    if last_char in string.ascii_lowercase:
        patch_version = 1 + string.ascii_lowercase.index(last_char)
        return rdfox_version[:-1] + f".{patch_version}"
    return rdfox_version


def fetch_and_write_rdfox_wheels(
    rdfox_version, outdir='dist/', wheel_version_suffix='', platforms=tuple()
):
    Path(outdir).mkdir(exist_ok=True)
    if not platforms:
        platforms = list(RDFOX_PYTHON_PLATFORMS)

    for rdfox_platform in platforms:
        python_platform = RDFOX_PYTHON_PLATFORMS[rdfox_platform]
        rdfox_url = (
            RDFOX_DOWNLOAD_BASE_URL +
            f"v{rdfox_version}/" +
            f"RDFox-{rdfox_platform}-{rdfox_version}.zip"
        )

        with urllib.request.urlopen(rdfox_url) as request:
            rdfox_archive = request.read()
            rdfox_archive_hash = hashlib.sha256(rdfox_archive).hexdigest()
            # if rdfox_archive_hash != expected_hash:
            #     print(rdfox_url, "SHA256 hash mismatch!")
            #     raise AssertionError
            print(f'{hashlib.sha256(rdfox_archive).hexdigest()} {rdfox_url}')

        wheel_version = rdfox_version_to_python_version(rdfox_version)
        wheel_path = write_rdfox_wheel(outdir,
            version=wheel_version + wheel_version_suffix,
            platform=python_platform,
            archive=rdfox_archive)
        with open(wheel_path, 'rb') as wheel:
            print(f'  {hashlib.sha256(wheel.read()).hexdigest()} {wheel_path}')

def get_argparser():
    parser = argparse.ArgumentParser(prog=__file__, description="Repackage official RDFox downloads as Python wheels")
    parser.add_argument('--version', required=True, help="version to package")
    parser.add_argument('--suffix', default='', help="wheel version suffix")
    parser.add_argument('--outdir', default='dist/', help="target directory")
    parser.add_argument('--platform', action='append', choices=list(RDFOX_PYTHON_PLATFORMS.keys()),
                        default=[], help="platform to build for, can be repeated")
    return parser

def main():
    args = get_argparser().parse_args()
    fetch_and_write_rdfox_wheels(rdfox_version=args.version,
                                 outdir=args.outdir,
                                 wheel_version_suffix=args.suffix, platforms=args.platform)

if __name__ == '__main__':
    main()
