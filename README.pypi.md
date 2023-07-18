RDFox PyPI distribution
=======================

[RDFox][rdfox] is a knowledge graph and semantic reasoning engine from Oxford Semantic Technologies. This [rdfox-pypi][pypi] Python package is an unofficial redistribution of the RDFox binaries so they can be used as a dependency of Python projects.

[rdfox]: https://www.oxfordsemantic.tech/product
[pypi]: https://pypi.org/project/rdfox/

Usage
-----

To run RDFox from the command line, use:

```shell
python -m rdfox
```

To run RDFox from a Python program, use `sys.executable` to locate the Python binary to invoke. For example:

```python
import sys, subprocess

subprocess.call([sys.executable, "-m", "rdfox"])
```

License
-------

RDFox requires a licence from Oxford Semantic Technologies.
