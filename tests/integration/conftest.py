import time
import uuid

import pytest
from kubernetes import client, config
from kubernetes.client import ApiException


@pytest.fixture(scope="session")
def k8s_api():
    config.load_kube_config()
    return {
        "core": client.CoreV1Api(),
        "apps": client.AppsV1Api(),
        "networking": client.NetworkingV1Api(),
    }


@pytest.fixture(scope="session")
def k8s_namespace(k8s_api):
    name = f"k8s-utils-test-{uuid.uuid4().hex[:8]}"
    body = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=name,
            labels={
                "purpose": "integration-test",
                "managed-by": "k8s-utils-py",
            },
        )
    )
    k8s_api["core"].create_namespace(body=body)
    yield name
    try:
        k8s_api["core"].delete_namespace(
            name=name,
            body=client.V1DeleteOptions(propagation_policy="Foreground"),
        )
    except ApiException as exc:
        if exc.status != 404:
            raise


def wait_for_deletion(api_call, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            api_call()
        except ApiException as exc:
            if exc.status == 404:
                return
            raise
        time.sleep(1)
    raise TimeoutError(f"Resource still exists after {timeout}s")
