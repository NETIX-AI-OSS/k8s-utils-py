# k8s-utils-py

Opinionated Kubernetes resource helpers for Python automation.

This project wraps a narrow slice of the Kubernetes Python client for teams that
prefer small imperative rollout scripts over templating systems. The public API
is intentionally biased toward:

- namespace-scoped app rollout helpers
- `uv`-first local development
- nginx/cert-manager ingress conventions
- simple CRUD-style methods over raw Kubernetes objects

## Project scope

This is not a generic Kubernetes abstraction layer. In particular, `Ingress`
keeps cluster-specific defaults on purpose:

- nginx ingress annotations are applied automatically
- TLS uses `cert-manager.io/cluster-issuer=letsencrypt-prod`
- public hosts follow `<username>.cdr.<domain_name>`
- TLS secrets follow `<username>-code-tls`

If those conventions do not match your environment, treat `Ingress` as a
reference implementation rather than a general-purpose helper.

## License

This repository is licensed under the GNU Affero General Public License v3.0.
If you modify the software and make it available for network use, the AGPL
requires you to offer the corresponding source to users of that service. See
[LICENSE](LICENSE) for the full text.

## Source install

This repository is not set up as a public package release yet. Install from
source instead:

```bash
git clone <your-fork-or-origin-url>
cd k8s-utils-py
uv sync --group dev
```

## Quickstart

```python
from k8s_utils import ConfigMap, Deployment

config = ConfigMap(name="example-config", namespace="default", sa_enabled=False)
config.create(filename="app.json", content='{"key":"value"}')

deployment = Deployment(app_name="example-app", namespace="default", sa_enabled=False)
deployment.add_env_from("example-config")
deployment.create(
    image="nginx:latest",
    command=["/bin/sh", "-c", "sleep 3600"],
)
```

`ConfigMap.create(filename, content)` and `ConfigMap.update(filename, content)`
keep the original single-key inline behavior by default. If you want to build a
full payload from local state, use the `upsert_key()` helpers first and then
call `create()` or `update()` with no inline args:

1. build state with `upsert_key()` / `upsert_key_binary()`
2. call `create()` or `update()`

## Auth modes

- `sa_enabled=True` loads in-cluster service-account credentials
- `sa_enabled=False` loads kubeconfig, optionally from `config_file`

All resource wrappers follow the same auth selection logic, including `Pod`.

## Resource coverage

| Resource | Class | Create | Update | Delete | Notes |
| --- | --- | --- | --- | --- | --- |
| Deployment | `Deployment` | Yes | Yes | Yes | Supports `env_vars`, `env_from`, and optional ConfigMap volume mount. |
| Service | `Service` | Yes | No | Yes | Exposes service port `80` and maps to the provided `target_port`. |
| Ingress | `Ingress` | Yes | No | Yes | Intentionally opinionated around nginx, cert-manager, and `cdr` host naming. |
| ConfigMap | `ConfigMap` | Yes | Yes (`patch`) | Yes | Inline `create(filename, content)` remains the default; `create()` / `update()` without args serialize local `data`. |
| Pod | `Pod` | No | No | Yes | Supports `get_pods()` and delete operations only. |

## Development

```bash
# Install dependencies
uv sync --group dev

# Unit tests (mocked, no cluster needed)
uv run pytest

# Lint
uv run ruff check .
uv run black --check .

# Integration tests against current kubeconfig context
uv run pytest --k8s
```

Integration tests create a temporary namespace (`k8s-utils-test-<id>`), run
create/update/delete round-trips against real Kubernetes APIs, and tear down the
namespace on completion. The `--k8s` flag only runs tests marked with `k8s`.

## Documentation

- [Use Cases](docs/use-cases.md)
- [Architecture and Patterns](docs/architecture-and-patterns.md)
- [Auth and Runtime Context](docs/auth-and-runtime-context.md)
- [API Behavior](docs/api-behavior.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
