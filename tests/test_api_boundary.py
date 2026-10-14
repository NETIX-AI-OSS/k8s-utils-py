import json
from unittest.mock import patch

import pytest
import urllib3
from kubernetes.client import ApiException

from k8s_utils import ConfigMap, Deployment, Ingress, Pod, Service


def _stub_http(monkeypatch, status=200):
    sent = []

    def fake_request(_pool, method, url, *_args, **kwargs):
        body = json.loads(kwargs["body"]) if kwargs.get("body") else None
        sent.append((method, urllib3.util.parse_url(url).path, body))
        reply = body if method in ("POST", "PUT", "PATCH") else {}
        if method == "GET":
            reply = {"items": []}
        if status >= 400:
            reply = {"kind": "Status", "code": status}
        return urllib3.HTTPResponse(
            body=json.dumps(reply).encode(),
            status=status,
            headers={"Content-Type": "application/json"},
        )

    monkeypatch.setattr(urllib3.PoolManager, "request", fake_request)
    return sent


@pytest.fixture
def wire(monkeypatch):
    return _stub_http(monkeypatch)


def _real_api(cls, *args):
    with patch("k8s_utils.base.config.load_kube_config"):
        return cls(*args, sa_enabled=False)


CORE = "/api/v1/namespaces/ns"
APPS = "/apis/apps/v1/namespaces/ns"
NETWORKING = "/apis/networking.k8s.io/v1/namespaces/ns"


@pytest.mark.parametrize(
    ("call", "method", "path", "kind"),
    [
        (
            lambda: _real_api(ConfigMap, "cm", "ns").create("config.json", "{}"),
            "POST",
            f"{CORE}/configmaps",
            "ConfigMap",
        ),
        (
            lambda: _real_api(ConfigMap, "cm", "ns").update("config.json", "{}"),
            "PATCH",
            f"{CORE}/configmaps/cm",
            "ConfigMap",
        ),
        (
            lambda: _real_api(ConfigMap, "cm", "ns").delete(),
            "DELETE",
            f"{CORE}/configmaps/cm",
            None,
        ),
        (
            lambda: _real_api(Deployment, "w", "ns").create(
                image="img",
                command=["run"],
                image_pull_secrets="regcred",
                env_vars={"A": "1"},
                volume_name="v",
                volume_mount_path="/m",
                volume_configmap_name="cm",
                volume_configmap_key="k",
                volume_configmap_path="p",
            ),
            "POST",
            f"{APPS}/deployments",
            "Deployment",
        ),
        (
            lambda: _real_api(Deployment, "w", "ns").update("img", ["run"]),
            "PUT",
            f"{APPS}/deployments/w",
            "Deployment",
        ),
        (
            lambda: _real_api(Deployment, "w", "ns").delete(),
            "DELETE",
            f"{APPS}/deployments/w",
            None,
        ),
        (
            lambda: _real_api(Service, "svc", "ns").create(8080),
            "POST",
            f"{CORE}/services",
            "Service",
        ),
        (
            lambda: _real_api(Service, "svc", "ns").delete(),
            "DELETE",
            f"{CORE}/services/svc",
            None,
        ),
        (
            lambda: _real_api(Ingress, "ing", "ns", "ex.com").create(80, "svc", "u"),
            "POST",
            f"{NETWORKING}/ingresses",
            "Ingress",
        ),
        (
            lambda: _real_api(Ingress, "ing", "ns", "ex.com").delete(),
            "DELETE",
            f"{NETWORKING}/ingresses/ing-ingress",
            None,
        ),
        (
            lambda: _real_api(Pod, "p", "ns").delete(),
            "DELETE",
            f"{CORE}/pods/p",
            None,
        ),
        (
            lambda: _real_api(Pod, "p", "ns").get_pods(),
            "GET",
            f"{CORE}/pods",
            None,
        ),
    ],
    ids=[
        "configmap-create",
        "configmap-update",
        "configmap-delete",
        "deployment-create",
        "deployment-update",
        "deployment-delete",
        "service-create",
        "service-delete",
        "ingress-create",
        "ingress-delete",
        "pod-delete",
        "pod-get-pods",
    ],
)
def test_helper_passes_the_real_client_request_validation(
    wire, call, method, path, kind
):
    call()
    sent_method, sent_path, body = wire[-1]
    assert (sent_method, sent_path) == (method, path)
    assert (body or {}).get("kind") == kind


def test_configmap_body_keeps_namespace_in_metadata(wire):
    _real_api(ConfigMap, "cm", "ns").create("config.json", "{}")
    assert wire[-1][2] == {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {"name": "cm", "namespace": "ns"},
        "data": {"config.json": "{}"},
    }


def test_deployment_delete_sends_foreground_options(wire):
    _real_api(Deployment, "w", "ns").delete()
    assert wire[-1][2] == {"gracePeriodSeconds": 5, "propagationPolicy": "Foreground"}


@pytest.mark.parametrize("status", [404, 409, 500])
def test_api_errors_keep_their_status_for_callers_fallbacks(monkeypatch, status):
    _stub_http(monkeypatch, status)
    with pytest.raises(ApiException) as exc_info:
        _real_api(Deployment, "w", "ns").create("img", ["run"])
    assert exc_info.value.status == status


def test_deleting_a_missing_resource_is_a_no_op(monkeypatch):
    _stub_http(monkeypatch, 404)
    _real_api(ConfigMap, "cm", "ns").delete()
