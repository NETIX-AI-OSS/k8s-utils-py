from unittest.mock import MagicMock, patch

import pytest
from kubernetes.client import ApiException

from tests.conftest import make_api_exception


class TestIngressInit:
    def test_init_sets_domain_name(self, ingress):
        assert ingress.domain_name == "example.com"

    def test_init_annotations_contains_nginx_ingress_class(self, ingress):
        assert ingress.annotations["kubernetes.io/ingress.class"] == "nginx"

    def test_init_annotations_contains_cert_manager_issuer(self, ingress):
        assert (
            ingress.annotations["cert-manager.io/cluster-issuer"] == "letsencrypt-prod"
        )


class TestIngressCreateBody:
    def test_create_host_format(self, ingress, mock_networking_api):
        ingress.create(port=80, service_name="test-svc", username="alice")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        rule = body.spec.rules[0]
        assert rule.host == "alice.cdr.example.com"

    def test_create_tls_hosts_and_secret_name(self, ingress, mock_networking_api):
        ingress.create(port=80, service_name="test-svc", username="alice")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        tls = body.spec.tls[0]
        assert tls.hosts == ["alice.cdr.example.com"]
        assert tls.secret_name == "alice-code-tls"

    def test_create_ingress_name_has_suffix(self, ingress, mock_networking_api):
        ingress.create(port=80, service_name="test-svc", username="alice")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        assert body.metadata.name == "test-app-ingress"

    def test_create_backend_port_and_service_name(self, ingress, mock_networking_api):
        ingress.create(port=8080, service_name="my-svc", username="bob")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        backend = body.spec.rules[0].http.paths[0].backend
        assert backend.service.port.number == 8080
        assert backend.service.name == "my-svc"

    def test_create_path_type_is_prefix_slash(self, ingress, mock_networking_api):
        ingress.create(port=80, service_name="test-svc", username="alice")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        path_obj = body.spec.rules[0].http.paths[0]
        assert path_obj.path == "/"
        assert path_obj.path_type == "Prefix"

    def test_create_api_version_is_networking_v1(self, ingress, mock_networking_api):
        ingress.create(port=80, service_name="test-svc", username="alice")
        call_kwargs = mock_networking_api.create_namespaced_ingress.call_args.kwargs
        body = call_kwargs["body"]
        assert body.api_version == "networking.k8s.io/v1"

    def test_create_propagates_api_exception(self, ingress, mock_networking_api):
        mock_networking_api.create_namespaced_ingress.side_effect = make_api_exception(
            409
        )
        with pytest.raises(ApiException):
            ingress.create(port=80, service_name="test-svc", username="alice")

    @pytest.mark.parametrize(
        "username,domain,expected_host",
        [
            ("alice", "example.com", "alice.cdr.example.com"),
            ("bob", "mysite.io", "bob.cdr.mysite.io"),
            ("charlie", "dev.internal", "charlie.cdr.dev.internal"),
        ],
    )
    def test_create_host_formula_parametrized(self, username, domain, expected_host):
        from k8s_utils.ingress import Ingress

        mock_net = MagicMock()
        with (
            patch("k8s_utils.base.config.load_kube_config"),
            patch("k8s_utils.base.client.AppsV1Api"),
            patch("k8s_utils.base.client.CoreV1Api"),
            patch(
                "k8s_utils.base.client.NetworkingV1Api",
                return_value=mock_net,
            ),
        ):
            ing = Ingress(
                app_name="app",
                namespace="ns",
                domain_name=domain,
                sa_enabled=False,
            )
        ing.create(port=80, service_name="svc", username=username)
        body = mock_net.create_namespaced_ingress.call_args.kwargs["body"]
        assert body.spec.rules[0].host == expected_host


class TestIngressDelete:
    def test_delete_uses_ingress_name_suffix(self, ingress, mock_networking_api):
        ingress.delete()
        call_kwargs = mock_networking_api.delete_namespaced_ingress.call_args.kwargs
        assert call_kwargs["name"] == "test-app-ingress"

    def test_delete_uses_initialized_networking_api(self, ingress, mock_networking_api):
        ingress.delete()
        mock_networking_api.delete_namespaced_ingress.assert_called_once()

    def test_delete_404_does_not_raise(self, ingress, mock_networking_api):
        mock_networking_api.delete_namespaced_ingress.side_effect = make_api_exception(
            404
        )
        ingress.delete()  # should not raise

    @pytest.mark.parametrize("status_code", [400, 403, 500, 503])
    def test_delete_non_404_raises(self, ingress, mock_networking_api, status_code):
        mock_networking_api.delete_namespaced_ingress.side_effect = make_api_exception(
            status_code
        )
        with pytest.raises(ApiException) as exc_info:
            ingress.delete()
        assert exc_info.value.status == status_code
