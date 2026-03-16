# Security Policy

## Supported versions

Only the latest version on the default branch is considered supported for
security fixes.

## Reporting a vulnerability

Do not open public GitHub issues for suspected vulnerabilities.

If the repository is hosted on GitHub with Security Advisories enabled, use a
private vulnerability report. If that workflow is not available, contact the
repository maintainers privately before disclosing details publicly.

When reporting, include:

- affected file paths or APIs
- reproduction steps
- impact assessment
- any suggested mitigation

## Scope notes

This project wraps Kubernetes APIs. Secure deployment still depends on cluster
configuration, RBAC, secret handling, ingress controller policy, cert-manager
configuration, and the calling environment. Consumers should review those layers
separately from this library.
