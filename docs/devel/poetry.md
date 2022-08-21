# Poetry

Used for Python dependency management and packaging. Must be installed manually.

- <https://python-poetry.org/>
- <https://github.com/python-poetry/poetry>

Whenever this repository is cloned, the environment needs to be installed. Same
goes for pulling changes that include dependency updates.

    poetry install

This installs dependencies including development dependencies. You can jump into
the created environment.

    poetry shell

Poetry is configured via [`../pyproject.toml`](../pyproject.toml). In general
Poetry related configuration should be done via the Poetry CLI.

The lockfile [`../poetry.lock`](../poetry.lock) should never be adjusted by
hand.

## Cheat Sheet

Setup shell so that you can run commands inside the environment.

    poetry shell

Run arbitrary commands inside the environment without a Poetry shell.

    poetry run pre-commit run -a
