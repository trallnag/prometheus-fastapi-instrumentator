# Development

This document is targeted at project developers. It helps people to make their
first steps. It also serves as a general entry to development documentation like
tooling configuration and usage.

## Requirements

Your environment should fulfill the following basic requirements:

- [Python](https://www.python.org). See [`pyproject.toml`](pyproject.toml) for
  the minimum required version.
- [Poetry](https://python-poetry.org). Python packaging and dependency managed
  tool.
- [Pre-commit](https://pre-commit.com). For managing and maintaining pre-commit
  Git hooks. Optional.
- [Task](https://taskfile.dev). Task runner as simple alternative to Make.
  Optional.
- Unix-like. Not required by itself, but assumed as the standard.

In addition to the following sections in this document, note that the
[`devel`](devel) directory contains more documentation including further
information about the tooling listed above.

## Initial Setup

### Python Environment

Ensure that [Python Poetry](https://python-poetry.org) is installed. After
cloning this repo (probably your own fork) execute:

```sh
poetry install
```

Read [`devel/poetry.md`](devel/poetry.md) for more info.

### Pre-commit Hooks

Ensure that [pre-commit](https://pre-commit.com) is installed globally. Setup
the pre-commit hooks:

```sh
pre-commit install --install-hooks
pre-commit install --install-hooks --hook-type commit-msg
```

Run all hooks to make sure things are alright:

```sh
pre-commit run -a
```

Read [`devel/pre-commit.md`](devel/pre-commit.md) for more info.

### Running Tests

Ensure that [Task](https://taskfile.dev) is installed. Run tests to make sure
everything is setup correctly:

```sh
task test
```

Read [`devel/task.md`](devel/task.md) for more info.
