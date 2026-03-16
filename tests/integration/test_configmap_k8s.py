import pytest
from kubernetes.client import ApiException

from k8s_utils.configmap import ConfigMap

pytestmark = pytest.mark.k8s


class TestConfigMapIntegration:
    def test_create_update_delete_roundtrip(self, k8s_api, k8s_namespace):
        cm = ConfigMap(name="test-cm", namespace=k8s_namespace, sa_enabled=False)

        # Create
        cm.create("app.conf", "key=value1")

        # Verify via direct API
        result = k8s_api["core"].read_namespaced_config_map(
            name="test-cm", namespace=k8s_namespace
        )
        assert result.data["app.conf"] == "key=value1"

        # Update (patch)
        cm.update("app.conf", "key=value2")

        result = k8s_api["core"].read_namespaced_config_map(
            name="test-cm", namespace=k8s_namespace
        )
        assert result.data["app.conf"] == "key=value2"

        # Delete
        cm.delete()

        with pytest.raises(ApiException) as exc_info:
            k8s_api["core"].read_namespaced_config_map(
                name="test-cm", namespace=k8s_namespace
            )
        assert exc_info.value.status == 404

    def test_delete_nonexistent_is_graceful(self, k8s_namespace):
        cm = ConfigMap(name="does-not-exist", namespace=k8s_namespace, sa_enabled=False)
        cm.delete()  # Should not raise
