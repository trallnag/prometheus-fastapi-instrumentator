# Pre-Commit

Used for maintaining Git hooks. Installed as part of the development
dependencies with Poetry.

- <https://pre-commit.com/>
- <https://github.com/pre-commit/pre-commit>

Whenever this repository is cloned, the following commands must be executed
after the virtual environment has been installed with Poetry:

```sh
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
```

Pre-commit should now run automatically on every commit. It is also executed via
GitHub Actions and the respective pipelines should fail on hook fails.

Pre-commit is configured via
[`../.pre-commit-config.yaml`](../.pre-commit-config.yaml).

Note that many hooks in the config are of the local type. This allows us to
manage dependencies like `black` with Poetry while also using them from
pre-commit.

Here are a few commonly used commands. Note that you must prefix these commands
with `poetry run` if you aren't in a Poetry shell with `poetry shell`.

```sh
# Run pre-commit against all files.
pre-commit run -a

# Run only the flake8 hook against all files.
pre-commit run flake8 -a
```
