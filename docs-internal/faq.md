# Frequently Asked Questions

<!--TOC-->

- [How to release a new version?](#how-to-release-a-new-version)
- [How to setup local dev environment?](#how-to-setup-local-dev-environment)
- [How does versioning work?](#how-does-versioning-work)

<!--TOC-->

## How to release a new version?

In general the release process is fully automated. The process takes places on
the default branch.

Do something (push, merge) on the remote default branch and wait for the finish
of the GitHub Actions workflow
[`primary.yaml`](../.github/workflows/primary.yaml).

According to the rules of semantic versioning and conventional commits a new
version might be released. This is handled by semantic-release.

If a new version has been released, edit the GitHub release notes to add
anything noteworthy beyond the automatically generated content. Also make sure
to add the same to the changelog. This last step is optional.

Read [`semantic-release.md`](semantic-release.md) for more information.

## How to setup local dev environment?

Ensure that [Python Poetry](https://python-poetry.org/) is installed. After
cloning this project (probably as a fork), install the environment and enter a
Poetry shell.

```sh
poetry install
poetry shell
```

Read [`poetry.md`](poetry.md) for more information.

Setup the pre-commit hooks.

```sh
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg
```

Read [`pre-commit.md`](pre-commit.md) for more information.

Execute the tests to make sure everything is alright. You can either use the
helper script to trigger tests or execute `pytest` directly.

```sh
./scripts/test.sh
```

Follow the usual Git workflow. Work on a dedicated branch instead of the trunk.
Something along the lines of trunk-based development is a good idea.

## How does versioning work?

This project adheres strictly to semantic versioning. In addition the release
process is completely automated with semantic-release (see
[`semantic-release.md`](semantic-release.md)).

Major releases occur fairly frequently due to chore tasks like deprecating
support for Python versions that have reached their end of life which is
technically a breaking change.
