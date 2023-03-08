# Release

This document describes the release process and is targeted at maintainers.

## Preparation

Pick a name for the new release. It must follow
[Semantic Versioning](https://semver.org):

```shell
VERSION=1.0.1
```

Make sure that the "Unreleased" section in the [changelog](CHANGELOG.md) is
up-to-date. Feel free to adjust entries for example by adding additional
examples or highlighting breaking changes.

Move the content of the "Unreleased" section that will be included in the new
release to a new section with an appropriate title for the release. Should the
"Unreleased" section now be empty, add "Nothing." to it.

Set the `__version__` variable in `__init__.py` to `$VERSION`:

```shell
sed -i "/^__version__/c\__version__ = \"$VERSION\"" src/*/__init__.py
grep -n -H __version__ src/*/__init__.py
```

Bump the version using Poetry:

```shell
poetry version $VERSION
```

Continue with the next section.

## Trigger

Commit the changes. Make sure to sign the commit:

```shell
git add CHANGELOG.md src/*/__init__.py pyproject.toml
git commit -S -m "chore: Prepare release v$VERSION"
git log --show-signature -1
```

Push changes:

```shell
git push origin master
```

Check
[workflow runs](https://github.com/trallnag/prometheus-fastapi-instrumentator/actions?query=branch%3Amaster)
in GitHub Actions and ensure everything is fine.

Tag the latest commit with an annotated and signed tag:

```shell
git tag -s v$VERSION -m ""
git show v$VERSION
```

Make sure that the tree looks good:

```shell
git log --graph --oneline --all -n 5
```

Push the tag itself:

```shell
git push origin v$VERSION
```

This triggers the
[release workflow](https://github.com/trallnag/prometheus-fastapi-instrumentator/actions/workflows/release.yaml)
which will build a package, publish it to PyPI, and draft a GitHub release.
Monitor the workflow run:

```shell
gh workflow view release --web
```

## Wrap Up

Ensure that the new package version has been published to PyPI
[here](https://pypi.org/project/prometheus-fastapi-instrumentator).

Go to the release page of this project on GitHub
[here](https://github.com/trallnag/prometheus-fastapi-instrumentator/releases)
and review the automatically created release draft.

Set the release title to "$VERSION / $DATE". For example "1.0.0 / 2023-01-01".

Add release notes by extracting them from the [changelog](CHANGELOG.md).

Publish the release draft.
