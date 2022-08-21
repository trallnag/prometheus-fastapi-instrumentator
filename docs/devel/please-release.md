# Please Release

Used for semi-automatically releasing new versions. Only used within GitHub
Actions, so no local setup required.

- <https://github.com/googleapis/release-please>
- <https://github.com/google-github-actions/release-please-action>

Under the hood,
[conventional-changelog](https://github.com/conventional-changelog/conventional-changelog)
is an integral component of Release Please.

All configuration related to Release Please is contained in the
`release-please.yaml` GitHub Actions workflow.

## Cheat Sheet

### Add custom description before release

As of today (2022-08-15) it is not possible out of the box to add custom
description to the release notes and changelog before releasing. There's an
feature request open for this
[here](https://github.com/googleapis/release-please/issues/1274).

But there is a manual "hack" around this missing feature.

1. Checkout the Release Please pull request branch
2. Update the changelog file content.
3. Update the pull request description.

Make sure to do this right before you are ready to release. Else the manually
injected content will be scrambled.

### Recommended custom info block

Use a block along the following lines to augument the automatically generated
release notes and changelog.

```txt
### 🍀 Summary 🍀

<One line summarizing changes.>


### ✨ Highlights ✨

<List of highlights with attributions.>


```

The duplicate newlines mirror the behavior of Release Please.
