# Pre-Commit

Used for maintaining Git hooks. Installed and managed by Poetry.

- <https://pre-commit.com/>
- <https://github.com/pre-commit/pre-commit>

Whenever this repository is initially cloned, the following should be executed:

    pre-commit install --install-hooks
    pre-commit install --install-hooks --hook-type commit-msg

Pre-commit should now run on every commit. It is also used in GitHub Actions.

Pre-commit is configured via
[`../.pre-commit-config.yaml`](../.pre-commit-config.yaml).

## Cheat Sheet

Run pre-commit against all files.

    pre-commit run -a

Run specific hook against all files.

    pre-commit run <hook> -a
