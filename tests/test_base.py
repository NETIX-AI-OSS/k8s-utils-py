from unittest.mock import MagicMock, patch


class TestBaseConfigInClusterMode:
    def test_incluster_mode_calls_load_incluster_config(self):
        from k8s_utils.base import BaseConfig

        with (
            patch("k8s_utils.base.config.load_incluster_config") as mock_incluster,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            BaseConfig(sa_enabled=True, config_file=None)
            mock_incluster.assert_called_once()

    def test_incluster_mode_does_not_call_load_kube_config(self):
        from k8s_utils.base import BaseConfig

        with (
            patch("k8s_utils.base.config.load_incluster_config"),
            patch("k8s_utils.base.config.load_kube_config") as mock_kube_config,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            BaseConfig(sa_enabled=True, config_file=None)
            mock_kube_config.assert_not_called()


class TestBaseConfigKubeconfigMode:
    def test_kubeconfig_mode_calls_load_kube_config(self):
        from k8s_utils.base import BaseConfig

        with (
            patch("k8s_utils.base.config.load_kube_config") as mock_kube_config,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            BaseConfig(sa_enabled=False, config_file=None)
            mock_kube_config.assert_called_once_with(config_file=None)

    def test_kubeconfig_mode_passes_config_file_arg(self):
        from k8s_utils.base import BaseConfig

        with (
            patch("k8s_utils.base.config.load_kube_config") as mock_kube_config,
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            BaseConfig(sa_enabled=False, config_file="/tmp/kube")
            mock_kube_config.assert_called_once_with(config_file="/tmp/kube")


class TestBaseConfigApiAttributes:
    def test_apps_api_attribute_set(self):
        from k8s_utils.base import BaseConfig

        mock_apps = MagicMock()
        with (
            patch("k8s_utils.base.config.load_kube_config"),
            patch("k8s_utils.base.client.AppsV1Api", return_value=mock_apps),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch("k8s_utils.base.client.NetworkingV1Api"),
        ):
            bc = BaseConfig(sa_enabled=False, config_file=None)
            assert bc.apps_api is mock_apps

    def test_core_api_and_networking_api_attributes_set(self):
        from k8s_utils.base import BaseConfig

        mock_core = MagicMock()
        mock_net = MagicMock()
        with (
            patch("k8s_utils.base.config.load_kube_config"),
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api", return_value=mock_core),
            patch(
                "k8s_utils.base.client.NetworkingV1Api",
                return_value=mock_net,
            ),
        ):
            bc = BaseConfig(sa_enabled=False, config_file=None)
            assert bc.api is mock_core
            assert bc.networking_api is mock_net
