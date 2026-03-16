import pytest

from k8s_utils.configmap import ConfigMap
from k8s_utils.deployment import Deployment
from tests.integration.conftest import wait_for_deletion

pytestmark = pytest.mark.k8s


class TestDeploymentIntegration:
    def test_create_update_delete_roundtrip(self, k8s_api, k8s_namespace):
        dep = Deployment(app_name="test-dep", namespace=k8s_namespace, sa_enabled=False)

        # Create with busybox
        dep.create(
            image="busybox:1.36",
            command=["sleep", "3600"],
            image_pull_policy="IfNotPresent",
        )

        # Verify
        result = k8s_api["apps"].read_namespaced_deployment(
            name="test-dep", namespace=k8s_namespace
        )
        assert result.spec.template.spec.containers[0].image == "busybox:1.36"

        # Update to nginx
        dep.update(
            image="nginx:alpine",
            command=None,
            image_pull_policy="IfNotPresent",
        )

        result = k8s_api["apps"].read_namespaced_deployment(
            name="test-dep", namespace=k8s_namespace
        )
        assert result.spec.template.spec.containers[0].image == "nginx:alpine"

        # Delete
        dep.delete()

        wait_for_deletion(
            lambda: k8s_api["apps"].read_namespaced_deployment(
                name="test-dep", namespace=k8s_namespace
            )
        )

    def test_create_with_env_vars(self, k8s_api, k8s_namespace):
        dep = Deployment(
            app_name="test-dep-env", namespace=k8s_namespace, sa_enabled=False
        )
        env = {"MY_VAR": "hello", "OTHER_VAR": "world"}

        dep.create(
            image="busybox:1.36",
            command=["sleep", "3600"],
            image_pull_policy="IfNotPresent",
            env_vars=env,
        )

        result = k8s_api["apps"].read_namespaced_deployment(
            name="test-dep-env", namespace=k8s_namespace
        )
        container = result.spec.template.spec.containers[0]
        env_map = {e.name: e.value for e in container.env}
        assert env_map["MY_VAR"] == "hello"
        assert env_map["OTHER_VAR"] == "world"

        # Cleanup
        dep.delete()
        wait_for_deletion(
            lambda: k8s_api["apps"].read_namespaced_deployment(
                name="test-dep-env", namespace=k8s_namespace
            )
        )

    def test_create_with_configmap_volume(self, k8s_api, k8s_namespace):
        # Create ConfigMap first
        cm = ConfigMap(name="vol-cm", namespace=k8s_namespace, sa_enabled=False)
        cm.create("settings.ini", "debug=true")

        dep = Deployment(
            app_name="test-dep-vol", namespace=k8s_namespace, sa_enabled=False
        )
        dep.create(
            image="busybox:1.36",
            command=["sleep", "3600"],
            image_pull_policy="IfNotPresent",
            volume_name="config-vol",
            volume_mount_path="/etc/config",
            volume_configmap_name="vol-cm",
            volume_configmap_key="settings.ini",
            volume_configmap_path="settings.ini",
        )

        result = k8s_api["apps"].read_namespaced_deployment(
            name="test-dep-vol", namespace=k8s_namespace
        )
        container = result.spec.template.spec.containers[0]
        assert any(
            vm.mount_path == "/etc/config" for vm in (container.volume_mounts or [])
        )

        # Cleanup
        dep.delete()
        wait_for_deletion(
            lambda: k8s_api["apps"].read_namespaced_deployment(
                name="test-dep-vol", namespace=k8s_namespace
            )
        )
        cm.delete()

    def test_create_with_replica_count(self, k8s_api, k8s_namespace):
        dep = Deployment(
            app_name="test-dep-replicas", namespace=k8s_namespace, sa_enabled=False
        )
        dep.create(
            image="busybox:1.36",
            command=["sleep", "3600"],
            image_pull_policy="IfNotPresent",
            replicas=2,
        )

        result = k8s_api["apps"].read_namespaced_deployment(
            name="test-dep-replicas", namespace=k8s_namespace
        )
        assert result.spec.replicas == 2

        # Cleanup
        dep.delete()
        wait_for_deletion(
            lambda: k8s_api["apps"].read_namespaced_deployment(
                name="test-dep-replicas", namespace=k8s_namespace
            )
        )

    def test_delete_nonexistent_is_graceful(self, k8s_namespace):
        dep = Deployment(
            app_name="does-not-exist", namespace=k8s_namespace, sa_enabled=False
        )
        dep.delete()  # Should not raise
