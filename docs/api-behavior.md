# API Behavior

This page documents the current public class behavior in `k8s_utils`.

## CRUD support matrix

| Resource | Class | Create | Read/List | Update | Delete | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Deployment | `Deployment` | Yes | No | Yes | Yes | Update uses replace API call. |
| Service | `Service` | Yes | No | No | Yes | Service port fixed to `80`; method arg maps to `target_port`. |
| Ingress | `Ingress` | Yes | No | No | Yes | Name is `<app_name>-ingress` with opinionated nginx/cert-manager defaults. |
| ConfigMap | `ConfigMap` | Yes | No | Yes | Yes | Inline filename/content remains the default; no-arg calls serialize local `data`. |
| Pod | `Pod` | No | Yes (`get_pods`) | No | Yes | `get_pods` lists namespace pods. |

## Deployment

Constructor:

```python
Deployment(app_name, namespace="default", sa_enabled=True, config_file=None)
```

Methods:

- `add_env_from(configmap_name)`: Appends ConfigMap reference to container env sources.
- `create(image, command, image_pull_secrets=None, image_pull_policy=None, env_vars=None, volume_name=None, volume_mount_path=None, volume_configmap_name=None, volume_configmap_key=None, volume_configmap_path=None)`:
  Creates a namespaced deployment with label selector `app=<app_name>`.
- `update(...)`: Replaces namespaced deployment with the same payload structure as `create`.
- `delete()`: Deletes deployment with foreground propagation and 5-second grace period.

Behavior notes:

- `delete()` catches `ApiException` 404 and logs warning instead of raising.
- Volume mount is configured only when all `volume_*` fields are provided.
- `image_pull_policy` defaults to empty string when omitted.
- `image_pull_secrets` is omitted entirely when not provided.

## Service

Constructor:

```python
Service(app_name, namespace, sa_enabled=True, config_file=None)
```

Methods:

- `create(port)`: Creates a ClusterIP-style service selecting `app=<app_name>`,
  exposing `port=80`, and forwarding to `target_port=<port>`.
- `delete()`: Deletes namespaced service.

Behavior notes:

- `delete()` catches `ApiException` 404 and logs warning instead of raising.

## Ingress

Constructor:

```python
Ingress(app_name, namespace, domain_name, sa_enabled=True, config_file=None)
```

Methods:

- `create(port, service_name, username)`: Creates
  `<app_name>-ingress` in namespace with predefined nginx/cert-manager annotations.
- `delete()`: Deletes `<app_name>-ingress`.

Behavior notes:

- Host and TLS secret are generated as:
  `host=<username>.cdr.<domain_name>`, `secret=<username>-code-tls`.
- `delete()` catches `ApiException` 404 and logs warning instead of raising.
- nginx and cert-manager defaults are part of the intended public behavior.

## ConfigMap

Constructor:

```python
ConfigMap(name, namespace="default", sa_enabled=True, config_file=None)
```

Methods:

- `upsert_key_binary(name, content)`: Base64-encodes binary `content` into local `self.data`.
- `upsert_key(name, content)`: Stores value in local `self.data`.
- `delete_key(name)`: Removes key from local `self.data`.
- `create(filename=None, content=None)`: Creates a namespaced ConfigMap. If inline args are provided, it keeps the original single-key behavior. If omitted, it serializes the full local `data` map.
- `update(filename=None, content=None)`: Patches a namespaced ConfigMap. If inline args are provided, it keeps the original single-key behavior. If omitted, it serializes the full local `data` map.
- `delete()`: Deletes namespaced ConfigMap.

Behavior notes:

- `filename` and `content` must be provided together when used inline.
- Inline calls do not mutate `self.data`; stateful no-arg calls use the current
  contents of `self.data`.
- `delete()` catches `ApiException` 404 and logs warning instead of raising.

## Pod

Constructor:

```python
Pod(name, namespace="default", sa_enabled=True, config_file=None)
```

Methods:

- `get_pods()`: Lists pods in namespace and returns `pods.items`.
- `delete()`: Deletes pod by name in namespace.

Behavior notes:

- `delete()` catches `ApiException` 404 and logs warning instead of raising.
- `get_pods()` logs on `ApiException`; on error it returns `None` implicitly.
- Constructor follows `BaseConfig` auth selection and respects `config_file`.
