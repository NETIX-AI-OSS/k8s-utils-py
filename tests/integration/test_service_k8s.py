import pytest
from kubernetes.client import ApiException

from k8s_utils.service import Service

pytestmark = pytest.mark.k8s


class TestServiceIntegration:
    def test_create_and_delete_roundtrip(self, k8s_api, k8s_namespace):
        svc = Service(app_name="test-svc", namespace=k8s_namespace, sa_enabled=False)

        # Create with target port 8080
        svc.create(port=8080)

        # Verify
        result = k8s_api["core"].read_namespaced_service(
            name="test-svc", namespace=k8s_namespace
        )
        port_spec = result.spec.ports[0]
        assert port_spec.port == 80
        assert port_spec.target_port == 8080
        assert result.spec.selector == {"app": "test-svc"}

        # Delete
        svc.delete()

        with pytest.raises(ApiException) as exc_info:
            k8s_api["core"].read_namespaced_service(
                name="test-svc", namespace=k8s_namespace
            )
        assert exc_info.value.status == 404

    def test_delete_nonexistent_is_graceful(self, k8s_namespace):
        svc = Service(
            app_name="does-not-exist", namespace=k8s_namespace, sa_enabled=False
        )
        svc.delete()  # Should not raise
