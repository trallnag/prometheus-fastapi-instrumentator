# Poetry

Used for Python dependency management and packaging. Must be installed manually.

- [python-poetry.org](https://python-poetry.org)
- [github.com/python-poetry/poetry](https://github.com/python-poetry/poetry)

Whenever this repository is cloned, the environment needs to be installed. Same
goes for pulling changes that include dependency updates. The following command
installs dependencies including development dependencies:

```
poetry install
```

You can jump into the created environment:

```
poetry shell
```

Another alternative is to prepend commands with `poetry run`.

Poetry is configured via [`../pyproject.toml`](../pyproject.toml). In general
Poetry related configuration should be done via the Poetry CLI.

The lockfile [`../poetry.lock`](../poetry.lock) should never be adjusted by
hand.

## Housekeeping

### Update dependencies

To automatically update dependencies and bump versions in `pyproject.toml`,
plugins can be used. For example
[poetry-plugin-up](https://github.com/MousaZeidBaker/poetry-plugin-up). To
install the plugin, execute:

```
poetry self add poetry-plugin-up
```

Now it can be used like this:

```
poetry up
```

### Update Poetry itself

```
poetry self update
```

## Cheat Sheet

### Setup shell

```
poetry shell
```

### Run arbitrary commands

```
poetry run <command>
```
