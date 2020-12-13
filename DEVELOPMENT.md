<!-- omit in toc -->
# Development

This document contains information regarding the development.

<!-- omit in toc -->
## Table of Contents

- [Automatic API Documentation](#automatic-api-documentation)
- [Manual Documentation](#manual-documentation)
- [Testing Framework](#testing-framework)
- [Makefile](#makefile)

## Automatic API Documentation

Everything in the code base is more or less covered by Docstrings. [Pdoc3](https://pypi.org/project/pdoc3/)
is used to generate a simple HTML based documentation. The documentation is
generated to `/docs` and is hosted with GitHub Pages. It does not support
multiple versions and always reflects the latest state on the master branch.

To generate API docs, use `bash run.sh docs`.

## Manual Documentation

For manual docs [`README.md`](/README.md) is used.

## Testing Framework

Pytest is used for testing. Run tests with `bash run.sh test`. There are more
fine-grained functions available in `run.sh`. Slow test functions shall be
annotated with the `slow` tag.

## Makefile

The Bash script [`run.sh`](/run.sh) is used as a replacement for a Makefile.
It contains multiple functions that help with development ranging from building
documentation to running tests with coverage report creation.

* All functions must start with an underscore.
* New options must be added to the help function and to the switch case tree.
* To see all available options, run `bash run.sh help`.
