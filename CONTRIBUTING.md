# Contributing <!-- omit in toc -->

Thank you for your interest in improving this project. Your contributions are
appreciated.

In the following you can find a collection of frequently asked questions and
hopefully good answers.

- [How to setup local dev environment?](#how-to-setup-local-dev-environment)
- [How to start a development server?](#how-to-start-a-development-server)
- [How to release a new version?](#how-to-release-a-new-version)

Also consider taking a look at the development documentation at
[`docs/devel`](docs/devel).

## How to setup local dev environment?

### Poetry <!-- omit in toc -->

Ensure that [Python Poetry](https://python-poetry.org/) is installed. After
cloning this project (probably as a fork), install the environment and enter a
Poetry shell.

```sh
poetry install
poetry shell
```

Read [`docs/devel/poetry.md`](docs/devel/poetry.md) for more information.

### Pre-commit <!-- omit in toc -->

Setup the pre-commit hooks. Note that you don't have to install Pre-commit
manually. It is part of the dev dependencies managed by pre-commit.

```sh
pre-commit install --install-hooks
pre-commit install --install-hooks --hook-type commit-msg
```

Run all hooks to make sure things are alright.

```sh
pre-commit run -a
```

Read [`docs/devel/pre-commit.md`](docs/devel/pre-commit.md) for more
information.

### Tests <!-- omit in toc -->

Run the tests to make sure everything is setup correctly. You can either use the
helper script to trigger tests or execute `pytest` directly.

```sh
./scripts/test.sh
```

## How to start a development server?

Uvicorn is the recommended development server. It is installed as part of the
dependencies. You can either use the helper script to start a server or execute
`uvicorn` directly.

```sh
./scripts/uvicorn.sh
```

## How to release a new version?

For release management Release Please is used. Read
[`docs/devel/please-release.md`](docs/devel/please-release.md) for further
information. The general approach is described in the following.

Ensure that changes to be released are merged or pushed to the default branch.
Ensure that the relevant commits follow the conventional commits convention.

Wait for the GitHub Actions workflow `release-please.yaml` to finish.

Check the appropriate pull request managed by Release Please. The version is
determined by semantic versioning and conventional commits.

Add custom description to release notes and changelog

1. Checkout the Release Please pull request branch
2. Update the changelog file content.
3. Update the pull request description.

The custom block should look somewhat like this:

```txt
### 🍀 Summary 🍀

<One line summarizing changes.>

### ✨ Highlights ✨

<List of highlights with attributions.>
```

Finally, merge the Release Please pull request.
