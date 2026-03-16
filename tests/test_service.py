import pytest
from kubernetes.client import ApiException

from tests.conftest import make_api_exception


class TestServiceInit:
    def test_init_sets_app_name_and_namespace(self, service):
        assert service.app_name == "test-svc"
        assert service.namespace == "test-ns"


class TestServiceCreateBody:
    def test_create_body_service_port_always_80(self, service, mock_core_api):
        service.create(port=8080)
        call_kwargs = mock_core_api.create_namespaced_service.call_args.kwargs
        body = call_kwargs["body"]
        assert body.spec.ports[0].port == 80

    def test_create_body_target_port_equals_arg(self, service, mock_core_api):
        service.create(port=8080)
        call_kwargs = mock_core_api.create_namespaced_service.call_args.kwargs
        body = call_kwargs["body"]
        assert body.spec.ports[0].target_port == 8080

    def test_create_body_protocol_is_tcp(self, service, mock_core_api):
        service.create(port=3000)
        call_kwargs = mock_core_api.create_namespaced_service.call_args.kwargs
        body = call_kwargs["body"]
        assert body.spec.ports[0].protocol == "TCP"

    def test_create_body_selector_uses_app_name(self, service, mock_core_api):
        service.create(port=3000)
        call_kwargs = mock_core_api.create_namespaced_service.call_args.kwargs
        body = call_kwargs["body"]
        assert body.spec.selector == {"app": "test-svc"}


class TestServiceApiCalls:
    def test_create_calls_api_with_correct_namespace(self, service, mock_core_api):
        service.create(port=8080)
        mock_core_api.create_namespaced_service.assert_called_once()
        call_kwargs = mock_core_api.create_namespaced_service.call_args.kwargs
        assert call_kwargs["namespace"] == "test-ns"

    def test_create_propagates_api_exception(self, service, mock_core_api):
        mock_core_api.create_namespaced_service.side_effect = make_api_exception(409)
        with pytest.raises(ApiException):
            service.create(port=8080)

    def test_delete_calls_api(self, service, mock_core_api):
        service.delete()
        mock_core_api.delete_namespaced_service.assert_called_once()
        call_kwargs = mock_core_api.delete_namespaced_service.call_args.kwargs
        assert call_kwargs["name"] == "test-svc"
        assert call_kwargs["namespace"] == "test-ns"

    def test_delete_404_does_not_raise(self, service, mock_core_api):
        mock_core_api.delete_namespaced_service.side_effect = make_api_exception(404)
        service.delete()  # should not raise

    @pytest.mark.parametrize("status_code", [400, 403, 500, 503])
    def test_delete_non_404_raises(self, service, mock_core_api, status_code):
        mock_core_api.delete_namespaced_service.side_effect = make_api_exception(
            status_code
        )
        with pytest.raises(ApiException) as exc_info:
            service.delete()
        assert exc_info.value.status == status_code
