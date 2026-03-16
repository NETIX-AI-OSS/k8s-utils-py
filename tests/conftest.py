from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client import ApiException


@pytest.fixture
def mock_apps_api():
    return MagicMock()


@pytest.fixture
def mock_core_api():
    return MagicMock()


@pytest.fixture
def mock_networking_api():
    return MagicMock()


@pytest.fixture
def deployment(mock_apps_api, mock_core_api, mock_networking_api):
    from k8s_utils.deployment import Deployment

    with (
        patch("k8s_utils.base.config.load_kube_config"),
        patch("k8s_utils.base.client.AppsV1Api", return_value=mock_apps_api),
        patch("k8s_utils.base.client.CoreV1Api", return_value=mock_core_api),
        patch(
            "k8s_utils.base.client.NetworkingV1Api",
            return_value=mock_networking_api,
        ),
    ):
        d = Deployment(app_name="test-app", namespace="test-ns", sa_enabled=False)
    return d


@pytest.fixture
def service(mock_core_api):
    from k8s_utils.service import Service

    with (
        patch("k8s_utils.base.config.load_kube_config"),
        patch("k8s_utils.base.client.AppsV1Api"),
        patch("k8s_utils.base.client.CoreV1Api", return_value=mock_core_api),
        patch("k8s_utils.base.client.NetworkingV1Api"),
    ):
        s = Service(app_name="test-svc", namespace="test-ns", sa_enabled=False)
    return s


@pytest.fixture
def ingress(mock_networking_api):
    from k8s_utils.ingress import Ingress

    with (
        patch("k8s_utils.base.config.load_kube_config"),
        patch("k8s_utils.base.client.AppsV1Api"),
        patch("k8s_utils.base.client.CoreV1Api"),
        patch(
            "k8s_utils.base.client.NetworkingV1Api",
            return_value=mock_networking_api,
        ),
    ):
        i = Ingress(
            app_name="test-app",
            namespace="test-ns",
            domain_name="example.com",
            sa_enabled=False,
        )
    return i


@pytest.fixture
def configmap(mock_core_api):
    from k8s_utils.configmap import ConfigMap

    with (
        patch("k8s_utils.base.config.load_kube_config"),
        patch("k8s_utils.base.client.AppsV1Api"),
        patch("k8s_utils.base.client.CoreV1Api", return_value=mock_core_api),
        patch("k8s_utils.base.client.NetworkingV1Api"),
    ):
        cm = ConfigMap(name="test-cm", namespace="test-ns", sa_enabled=False)
    return cm


@pytest.fixture
def pod(mock_core_api):
    from k8s_utils.pod import Pod

    with (
        patch("k8s_utils.base.config.load_kube_config"),
        patch("k8s_utils.base.client.AppsV1Api"),
        patch("k8s_utils.base.client.CoreV1Api", return_value=mock_core_api),
        patch("k8s_utils.base.client.NetworkingV1Api"),
    ):
        p = Pod(name="test-pod", namespace="test-ns", sa_enabled=False)
    return p


def make_api_exception(status: int) -> ApiException:
    exc = ApiException(status=status)
    exc.status = status
    return exc
