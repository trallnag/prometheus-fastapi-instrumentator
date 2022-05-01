# Poetry

Used for Python dependency management and packaging. Must be installed manually.

- <https://python-poetry.org/>
- <https://github.com/python-poetry/poetry>

Whenever this repository is cloned, the environment needs an initial install.

```sh
poetry install
```

This installs dependencies including development dependencies. You can jump into
the created environment.

```sh
poetry shell
```

Poetry is configured via [`../pyproject.toml`](../pyproject.toml). In general
Poetry related configuration should be done via the Poetry CLI.

The lockfile [`../poetry.lock`](../poetry.lock) should never be touched
manually. Note that [`../requirements.txt`](../requirements.txt) is not a
default part of Poetry and only included for compatibility with systems that
don't understand `pyproject.toml`. The `requirements.txt` is kept up-to-date via
a pre-commit hook.

Here are a few commonly used commands.

```sh
# Setup shell so that you can run commands inside the environment.
poetry shell

# Run arbitrary commands inside the environment without a Poetry shell.
poetry run pre-commit run -a
```
