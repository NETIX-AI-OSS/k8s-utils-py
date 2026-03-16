import pytest
from kubernetes import client

from k8s_utils.pod import Pod
from tests.integration.conftest import wait_for_deletion

pytestmark = pytest.mark.k8s


class TestPodIntegration:
    def test_get_pods_empty_namespace(self, k8s_namespace):
        pod = Pod(name="unused", namespace=k8s_namespace, sa_enabled=False)
        pods = pod.get_pods()
        assert isinstance(pods, list)

    def test_get_pods_and_delete_roundtrip(self, k8s_api, k8s_namespace):
        # Create pod via direct K8s API (library has no create)
        body = client.V1Pod(
            metadata=client.V1ObjectMeta(name="test-pod"),
            spec=client.V1PodSpec(
                containers=[
                    client.V1Container(
                        name="busybox",
                        image="busybox:1.36",
                        command=["sleep", "3600"],
                    )
                ],
                restart_policy="Never",
            ),
        )
        k8s_api["core"].create_namespaced_pod(namespace=k8s_namespace, body=body)

        # Verify get_pods finds it
        pod = Pod(name="test-pod", namespace=k8s_namespace, sa_enabled=False)
        pods = pod.get_pods()
        pod_names = [p.metadata.name for p in pods]
        assert "test-pod" in pod_names

        # Delete via library
        pod.delete()

        wait_for_deletion(
            lambda: k8s_api["core"].read_namespaced_pod(
                name="test-pod", namespace=k8s_namespace
            )
        )

    def test_delete_nonexistent_is_graceful(self, k8s_namespace):
        pod = Pod(name="does-not-exist", namespace=k8s_namespace, sa_enabled=False)
        pod.delete()  # Should not raise
