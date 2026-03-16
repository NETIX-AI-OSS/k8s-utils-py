# Auth and Runtime Context

This package supports two runtime auth modes through `sa_enabled`:

- `sa_enabled=True`: use Kubernetes in-cluster service-account credentials.
- `sa_enabled=False`: use kubeconfig from local or mounted config file.

## How auth mode is selected

`BaseConfig.__init__(sa_enabled, config_file)` executes:

- `config.load_incluster_config()` when `sa_enabled=True`
- `config.load_kube_config(config_file=config_file)` when `sa_enabled=False`

Then it initializes:

- `AppsV1Api`
- `CoreV1Api`
- `NetworkingV1Api`

## When to use each mode

| Environment | Suggested mode | Why |
| --- | --- | --- |
| In-cluster automation (Jobs, CronJobs, pods) | `sa_enabled=True` | Native workload identity; no kubeconfig distribution needed. |
| Local development and debugging | `sa_enabled=False` | Reuses developer kubeconfig contexts. |
| CI/CD runner outside cluster | `sa_enabled=False` | Uses explicit kubeconfig or injected credentials. |
| Hybrid scripts (sometimes local, sometimes in-cluster) | Context-driven | Set mode by runtime environment variables or deployment profile. |

## Neutral SA guidance

Service accounts are usually the default fit for in-cluster automation, while
kubeconfig remains practical for local development and external operations.
Choose based on execution environment and credential management policy.

## Minimal RBAC and least-privilege checklist

- Scope access to required namespaces only.
- Grant only required verbs (`get`, `list`, `create`, `patch`, `update`, `delete`)
  per resource type.
- Separate service accounts by automation purpose when feasible.
- Avoid broad cluster-wide roles for namespace-scoped jobs.
- Validate that delete/update verbs are explicitly intentional.

## Runtime caveat

`Pod` now follows the same auth selection path as every other wrapper:

- `sa_enabled=True` only loads in-cluster config
- `sa_enabled=False` loads kubeconfig and respects `config_file`
