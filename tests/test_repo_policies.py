import os
from pathlib import Path

import kubernetes
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_required_oss_files_exist():
    required_files = [
        "LICENSE",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CODE_OF_CONDUCT.md",
        ".github/workflows/ci.yml",
    ]
    for rel_path in required_files:
        assert (ROOT / rel_path).exists(), f"Missing required OSS file: {rel_path}"


def test_public_package_exports():
    from k8s_utils import (
        ConfigMap,
        Deployment,
        Ingress,
        Pod,
        Service,
        __version__,
    )

    assert ConfigMap.__name__ == "ConfigMap"
    assert Deployment.__name__ == "Deployment"
    assert Ingress.__name__ == "Ingress"
    assert Pod.__name__ == "Pod"
    assert Service.__name__ == "Service"
    assert __version__ == "1.2.0"


def test_installed_kubernetes_matches_ci_matrix():
    expected_major = os.environ.get("K8S_CLIENT_MAJOR")
    if not expected_major:
        pytest.skip("K8S_CLIENT_MAJOR is only set by the CI matrix")
    assert kubernetes.__version__.split(".")[0] == expected_major
