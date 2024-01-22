RDFox PyPI distribution
=======================

This repository contains the script used to repackage the [releases][rdfoxdl] of the [RDFox triplestore][rdfox] as [Python binary wheels][wheel]. This document is intended for maintainers; see the [package README][pkgreadme] for rationale and usage instructions.

The repackaged artifacts are published as the [rdfox PyPI package][pypi].

These Python packages are unofficial distributions of the RDFox binaries for the convenience of installing particular versions when projects are already using Python tooling.

Credit: adapted from https://github.com/ziglang/zig-pypi

[rdfox]: https://www.oxfordsemantic.tech/product
[rdfoxdl]: https://www.oxfordsemantic.tech/downloads
[wheel]: https://github.com/pypa/wheel
[pkgreadme]: README.pypi.md
[pypi]: https://pypi.org/project/rdfox/

Preparation
-----------

The script requires Python 3.5 or later.

Install the dependencies:

```shell
python -m venv venv
. venv/bin/activate
pip install wheel twine libarchive-c
```

The `libarchive-c` Python library requires the native [libarchive][] library to be available.

[libarchive]: https://libarchive.org/

Building wheels
---------------

Run the repackaging script:

```shell
python make_wheels.py --help
usage: make_wheels.py [-h] [--version VERSION] [--suffix SUFFIX] [--outdir OUTDIR]
                      [--platform {win64-x86_64,macOS-x86_64,macOS-arm64,linux-i386-linux,linux-x86_64,linux-arm64}]

Repackage official RDFox downloads as Python wheels.

options:
  -h, --help            show this help message and exit
  --version VERSION     version to package, use `latest` for latest release, `master` for nightly build
  --suffix SUFFIX       wheel version suffix
  --outdir OUTDIR       target directory
  --platform {win64-x86_64,macOS-x86_64,macOS-arm64,linux-i386-linux,linux-x86_64,linux-arm64}
                        platform to build for, can be repeated
```

This command will download the RDFox release archives for every supported platform and convert them to binary wheels, which are placed under `dist/`. The RDFox version and platforms can be passed as arguments.

The process of converting release archives to binary wheels is deterministic, and the output of the script should be bit-for-bit identical regardless of the environment and platform it runs under. To this end, it prints the SHA256 hashes of inputs and outputs. The hashes of the outputs will match the ones on the [PyPI downloads page][pypidl].

[pypidl]: https://pypi.org/project/rdfox/#files

Uploading wheels
----------------

Run the publishing utility:

```shell
twine dist/*
```

This command will upload the binary wheels built in the previous step to PyPI.

Changes in version numbers
--------------------------

RDFox has started using an alphabetical suffix to denote a patch release (e.g. `6.3a`). As a Python package version, this would be interpreted as an alpha release (`6.3a0`), which is sorted before the previous release `6.3`. Therefore, alphabetic suffices are converted to numerical patch versions (e.g. `6.3a` becomes `6.3.1`).

Github Actions
--------------

The `publish.yml` workflow can be manually triggered and will build and publish packages for a new RDFox version directly on Github.

License
-------

This script is distributed under the terms of the [MIT license](LICENSE.txt).
