# Changelog

> Reconstructed from git history on 2026-09-14. Entries below were derived from commit
> subjects rather than written at release time, so they summarise what changed but may not
> capture every user-visible detail. Entries from the next release onward are written as part
> of the release.

This project uses two-component release tags (`v1.0`) and three-component package versions
(`1.0.0`); the two refer to the same release.

## Unreleased

### Changed

- Raised the minimum supported Python from 3.12 to 3.14.
- Migrated formatting from black to `ruff format`.
- Added mypy to pre-commit and to the dev dependency group.
- Declared the project venv for pyright in `pyproject.toml`.
- Collapsed multi-line comments to single-line across the package.
- Cleaned up docs, license headers and docstrings.
- CI: added explicit workflow permissions (security hardening).
- CI: migrated `ubuntu-latest` jobs to the `build-only` runner.

## 1.0.0 — 2026-03-16 (tag `v1.0`)

- Initial open-source release of the shared Kubernetes helper utilities.
