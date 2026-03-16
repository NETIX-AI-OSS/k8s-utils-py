# Contributing

Thanks for contributing to `k8s-utils-py`.

## Ground rules

- By contributing, you agree that your work will be licensed under the GNU
  Affero General Public License v3.0.
- Keep changes focused. Small, reviewable pull requests are preferred.
- Update tests and docs when public behavior changes.
- Do not remove or weaken the documented ingress conventions unless the change
  explicitly re-scopes the package.

## Local setup

```bash
uv sync --group dev
```

## Development workflow

```bash
uv run ruff check .
uv run black --check .
uv run pytest
```

Integration tests are opt-in and require a working kubeconfig context:

```bash
uv run pytest --k8s
```

These tests create and delete temporary namespaces. Run them only against a
cluster where that is acceptable.

## Pull request checklist

- Add or update tests for behavior changes.
- Update `README.md` and docs in `docs/` when public usage changes.
- Preserve Python 3.12 compatibility.
- Keep public API changes explicit in the PR description.
- Mention any Kubernetes assumptions introduced or changed.

## Release expectations

This repository is currently source-install first. Do not update installation
docs to claim a public package release unless the release workflow and package
distribution are actually in place.
