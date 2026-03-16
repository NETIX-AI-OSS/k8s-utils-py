import pytest
from kubernetes.client import ApiException

from k8s_utils.ingress import Ingress
from k8s_utils.service import Service

pytestmark = pytest.mark.k8s


class TestIngressIntegration:
    def test_create_and_delete_roundtrip(self, k8s_api, k8s_namespace):
        # Ingress needs a backend service to reference
        svc = Service(
            app_name="test-ing-svc", namespace=k8s_namespace, sa_enabled=False
        )
        svc.create(port=8080)

        ing = Ingress(
            app_name="test-ing",
            namespace=k8s_namespace,
            domain_name="example.com",
            sa_enabled=False,
        )

        ing.create(port=80, service_name="test-ing-svc", username="testuser")

        # Verify
        result = k8s_api["networking"].read_namespaced_ingress(
            name="test-ing-ingress", namespace=k8s_namespace
        )
        assert result.spec.rules[0].host == "testuser.cdr.example.com"
        assert result.spec.tls[0].hosts == ["testuser.cdr.example.com"]
        assert result.metadata.annotations["kubernetes.io/ingress.class"] == "nginx"

        # Delete
        ing.delete()

        with pytest.raises(ApiException) as exc_info:
            k8s_api["networking"].read_namespaced_ingress(
                name="test-ing-ingress", namespace=k8s_namespace
            )
        assert exc_info.value.status == 404

        # Cleanup service
        svc.delete()

    def test_delete_nonexistent_is_graceful(self, k8s_namespace):
        ing = Ingress(
            app_name="does-not-exist",
            namespace=k8s_namespace,
            domain_name="example.com",
            sa_enabled=False,
        )
        ing.delete()  # Should not raise
