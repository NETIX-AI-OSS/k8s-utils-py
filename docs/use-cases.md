# Use Cases

## 1. Scripted app rollout with config injection

Use when a script needs to push application config and launch a workload quickly.

### Inputs

- App name, namespace, image, container command.
- Config payload (`filename`, `content`) for ConfigMap.
- Optional mount details (`volume_*`) when config must be mounted as a file.

### Class sequence

1. `ConfigMap.create(filename, content)`
2. `Deployment.add_env_from(configmap_name)` (optional)
3. `Deployment.create(image, command, ...)`
4. `Service.create(port)` (optional if service exposure is needed)
5. `Ingress.create(port, service_name, username)` (optional external entrypoint)

### Expected outcome

- ConfigMap exists with requested data.
- Deployment is created and references config via env or mounted file.
- Service and Ingress route traffic if created.

Optional alternative:

- Build a multi-key ConfigMap with `upsert_key*()` and call `create()` without
  inline args when you want to serialize the full local `data` map.

### Failure points to watch

- Missing namespace permissions for create operations.
- Incomplete volume arguments for deployment mount path.
- Ingress DNS/TLS assumptions not matching your cluster setup.
- AGPL obligations may matter if you expose modified versions of this tooling as
  part of a network-accessible service.

## 2. In-cluster operational automation with service account (SA)

Use when this package runs inside Kubernetes (CronJob, Job, controller-like script).

### Inputs

- `sa_enabled=True`
- Namespace scope and resource names.
- Service account + RBAC permissions.

### Class sequence

1. Instantiate wrappers with `sa_enabled=True`.
2. Call `create`, `update`, `delete`, and `get_pods` methods as needed.

### Expected outcome

- In-cluster auth is loaded via `load_incluster_config()`.
- API calls execute using pod service account identity.

### Failure points to watch

- RBAC denies list/create/update/delete operations.
- Workload service account not mounted or misconfigured.
- Incorrect `sa_enabled` choice for the runtime environment.

## 3. Cleanup and maintenance workflows

Use for idempotent cleanup scripts and maintenance operations.

### Inputs

- Resource names and namespaces.
- Desired operation (`update` for Deployment/ConfigMap, `delete` for all supported resources).

### Class sequence

1. `Deployment.update(...)` or `ConfigMap.update(...)` for maintenance change.
2. `Ingress.delete()`, `Service.delete()`, `Deployment.delete()`,
   `ConfigMap.delete()`, `Pod.delete()` for cleanup.

### Expected outcome

- Existing resources are updated or removed.
- Delete operations handle missing resources gracefully in most wrappers.

### Failure points to watch

- Update operations replacing immutable fields can fail server-side.
- NotFound handling differs by method (`delete` methods generally absorb 404).
- Cleanup order matters if finalizers or dependent resources are involved.
