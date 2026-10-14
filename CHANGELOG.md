# Changelog

> Reconstructed from git history on 2026-09-14. Entries below were derived from commit
> subjects rather than written at release time, so they summarise what changed but may not
> capture every user-visible detail. Entries from the next release onward are written as part
> of the release.

This project uses two-component release tags (`v1.0`) and three-component package versions
(`1.0.0`); the two refer to the same release.

## Unreleased

## 1.2.0 — 2026-10-14 (tag `v1.2`)

### Fixed

- `ConfigMap.create` works with kubernetes 37. The body carried a top-level `namespace`
  key, which is not a ConfigMap field. kubernetes 37 validates request bodies
  (`extra="forbid"`) and rejected it, while older clients sent it and the API server
  ignored it. The namespace now sits in `metadata`, where Kubernetes defines it. 1.1.0
  missed this because its tests mocked the API classes.

### Changed

- Every helper is now also tested through the real kubernetes API classes, with only the
  HTTP pool stubbed, so client-side request validation and error mapping run on 36 and 37.

## 1.1.0 — 2026-10-14 (tag `v1.1`)

### Fixed

- `Deployment.create`/`update` work with kubernetes 37, whose client models are pydantic
  and reject a `V1Deployment` built without `spec`. Deployment and Service bodies are now
  built whole; the serialized manifests are unchanged from 1.0.0 on kubernetes 36 and 37.

### Changed

- `Deployment` bodies carry typed `V1VolumeMount`/`V1KeyToPath` models instead of plain
  dicts, so callers read `volume_mounts[0].mount_path` rather than `["mountPath"]`.
- CI runs the test suite against kubernetes 36 and 37.
- The dev lock moves to kubernetes 37.0.1.
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
