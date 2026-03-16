import logging
from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client import ApiException

from tests.conftest import make_api_exception


class TestPodInit:
    def test_pod_init_uses_incluster_config_when_sa_enabled_true(self):
        from k8s_utils.pod import Pod

        with (
            patch("k8s_utils.base.config.load_incluster_config") as mock_incluster,
            patch("k8s_utils.base.config.load_kube_config") as mock_kube_config,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            Pod(name="test", namespace="ns", sa_enabled=True)
            mock_incluster.assert_called_once()
            mock_kube_config.assert_not_called()

    def test_pod_init_sa_enabled_false_calls_load_kube_config_once(self):
        from k8s_utils.pod import Pod

        with (
            patch("k8s_utils.base.config.load_kube_config") as mock_load,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            Pod(name="test", namespace="ns", sa_enabled=False)
            mock_load.assert_called_once_with(config_file=None)

    def test_pod_init_passes_config_file_when_provided(self):
        from k8s_utils.pod import Pod

        with (
            patch("k8s_utils.base.config.load_kube_config") as mock_load,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            Pod(
                name="test",
                namespace="ns",
                sa_enabled=False,
                config_file="/tmp/custom-kubeconfig",
            )
            mock_load.assert_called_once_with(config_file="/tmp/custom-kubeconfig")


class TestGetPods:
    def test_get_pods_calls_list_namespaced_pod(self, pod, mock_core_api):
        mock_core_api.list_namespaced_pod.return_value = MagicMock(items=[])
        pod.get_pods()
        mock_core_api.list_namespaced_pod.assert_called_once_with(namespace="test-ns")

    def test_get_pods_returns_items_list(self, pod, mock_core_api):
        fake_items = [MagicMock(), MagicMock()]
        mock_core_api.list_namespaced_pod.return_value = MagicMock(items=fake_items)
        result = pod.get_pods()
        assert result == fake_items

    def test_get_pods_returns_none_on_api_exception(self, pod, mock_core_api):
        mock_core_api.list_namespaced_pod.side_effect = make_api_exception(500)
        result = pod.get_pods()
        assert result is None

    def test_get_pods_logs_error_on_api_exception(self, pod, mock_core_api, caplog):
        mock_core_api.list_namespaced_pod.side_effect = make_api_exception(500)
        with caplog.at_level(logging.ERROR):
            pod.get_pods()
        assert "error" in caplog.text.lower()


class TestPodDelete:
    def test_delete_calls_api_with_name_and_namespace(self, pod, mock_core_api):
        pod.delete()
        mock_core_api.delete_namespaced_pod.assert_called_once_with(
            "test-pod", "test-ns"
        )

    def test_delete_404_does_not_raise(self, pod, mock_core_api):
        mock_core_api.delete_namespaced_pod.side_effect = make_api_exception(404)
        pod.delete()  # should not raise

    def test_delete_404_logs_warning(self, pod, mock_core_api, caplog):
        mock_core_api.delete_namespaced_pod.side_effect = make_api_exception(404)
        with caplog.at_level(logging.WARNING):
            pod.delete()
        assert "not found" in caplog.text.lower()

    @pytest.mark.parametrize("status_code", [400, 403, 500, 503])
    def test_delete_non_404_raises(self, pod, mock_core_api, status_code):
        mock_core_api.delete_namespaced_pod.side_effect = make_api_exception(
            status_code
        )
        with pytest.raises(ApiException) as exc_info:
            pod.delete()
        assert exc_info.value.status == status_code
