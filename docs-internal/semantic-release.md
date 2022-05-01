# Semantic-Release

Used for automatically releasing new versions. Only relevant within CI/CD, so no
local setup required.

- <https://semantic-release.gitbook.io/semantic-release/>
- <https://github.com/semantic-release/semantic-release>

Configuration of semantic-release takes place in multiple places:

- [`../.releaserc.json`](../.releaserc.json): Semantic-release is configured in
  this file. For example the plugins used or plugin specific configuration.
  Currently this project uses the Conventional Commits preset, a bunch of
  additonal types and a few additional release rules.
- [`../node/`](../node/): Dependency management for the semantic-release
  environment. At runtime in CI/CD pipeline the `package.json` and lock file are
  copied to the root of the project.
- [`../.github/workflows/primary.yaml`](../.github/workflows/primary.yaml): Here
  semantic-release is actually executed.
