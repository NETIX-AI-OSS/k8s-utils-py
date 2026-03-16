import base64

import pytest
from kubernetes.client import ApiException

from tests.conftest import make_api_exception


class TestConfigMapInit:
    def test_init_data_is_empty_dict(self, configmap):
        assert configmap.data == {}


class TestConfigMapLocalState:
    def test_upsert_key_adds_to_data(self, configmap):
        configmap.upsert_key("key1", "value1")
        assert configmap.data == {"key1": "value1"}

    def test_upsert_key_overwrites_existing(self, configmap):
        configmap.upsert_key("key1", "old")
        configmap.upsert_key("key1", "new")
        assert configmap.data["key1"] == "new"

    def test_upsert_key_binary_base64_encodes(self, configmap):
        raw = b"hello world"
        configmap.upsert_key_binary("binkey", raw)
        expected = base64.b64encode(raw).decode("utf-8")
        assert configmap.data["binkey"] == expected

    def test_upsert_key_binary_stores_as_str_not_bytes(self, configmap):
        configmap.upsert_key_binary("binkey", b"\x00\x01\x02")
        assert isinstance(configmap.data["binkey"], str)

    def test_upsert_key_binary_empty_bytes(self, configmap):
        configmap.upsert_key_binary("empty", b"")
        expected = base64.b64encode(b"").decode("utf-8")
        assert configmap.data["empty"] == expected

    def test_delete_key_removes_entry(self, configmap):
        configmap.upsert_key("key1", "value1")
        configmap.delete_key("key1")
        assert "key1" not in configmap.data

    def test_delete_key_raises_key_error_for_missing_key(self, configmap):
        with pytest.raises(KeyError):
            configmap.delete_key("nonexistent")


class TestConfigMapCreate:
    def test_create_calls_create_namespaced_config_map(self, configmap, mock_core_api):
        configmap.create(filename="app.conf", content="data=1")
        mock_core_api.create_namespaced_config_map.assert_called_once()

    def test_create_body_structure(self, configmap, mock_core_api):
        configmap.create(filename="app.conf", content="data=1")
        call_kwargs = mock_core_api.create_namespaced_config_map.call_args.kwargs
        body = call_kwargs["body"]
        assert body["apiVersion"] == "v1"
        assert body["kind"] == "ConfigMap"
        assert body["metadata"]["name"] == "test-cm"
        assert body["namespace"] == "test-ns"
        assert body["data"] == {"app.conf": "data=1"}

    def test_create_keeps_old_inline_behavior_by_default(
        self, configmap, mock_core_api
    ):
        configmap.upsert_key("local-key", "local-val")
        configmap.create(filename="app.conf", content="inline-content")
        call_kwargs = mock_core_api.create_namespaced_config_map.call_args.kwargs
        body = call_kwargs["body"]
        assert body["data"] == {"app.conf": "inline-content"}
        assert configmap.data == {"local-key": "local-val"}

    def test_create_uses_accumulated_data_without_inline_args(
        self, configmap, mock_core_api
    ):
        configmap.upsert_key("app.conf", "data=1")
        configmap.upsert_key("extra.conf", "data=2")
        configmap.create()
        body = mock_core_api.create_namespaced_config_map.call_args.kwargs["body"]
        assert body["data"] == {"app.conf": "data=1", "extra.conf": "data=2"}

    def test_create_rejects_partial_inline_content(self, configmap):
        with pytest.raises(ValueError):
            configmap.create(filename="app.conf")

    def test_create_propagates_api_exception(self, configmap, mock_core_api):
        mock_core_api.create_namespaced_config_map.side_effect = make_api_exception(409)
        with pytest.raises(ApiException):
            configmap.create(filename="app.conf", content="data=1")


class TestConfigMapUpdate:
    def test_update_calls_patch_namespaced_config_map(self, configmap, mock_core_api):
        configmap.update(filename="app.conf", content="data=2")
        mock_core_api.patch_namespaced_config_map.assert_called_once()

    def test_update_body_structure(self, configmap, mock_core_api):
        configmap.update(filename="app.conf", content="data=2")
        call_kwargs = mock_core_api.patch_namespaced_config_map.call_args.kwargs
        assert call_kwargs["name"] == "test-cm"
        assert call_kwargs["namespace"] == "test-ns"
        body = call_kwargs["body"]
        assert body["apiVersion"] == "v1"
        assert body["kind"] == "ConfigMap"
        assert body["data"] == {"app.conf": "data=2"}

    def test_update_keeps_old_inline_behavior_by_default(
        self, configmap, mock_core_api
    ):
        configmap.upsert_key("local-key", "local-val")
        configmap.update(filename="file.txt", content="inline")
        call_kwargs = mock_core_api.patch_namespaced_config_map.call_args.kwargs
        body = call_kwargs["body"]
        assert body["data"] == {"file.txt": "inline"}
        assert configmap.data == {"local-key": "local-val"}

    def test_update_uses_accumulated_data_without_inline_args(
        self, configmap, mock_core_api
    ):
        configmap.upsert_key("app.conf", "data=2")
        configmap.update()
        body = mock_core_api.patch_namespaced_config_map.call_args.kwargs["body"]
        assert body["data"] == {"app.conf": "data=2"}

    def test_update_rejects_partial_inline_content(self, configmap):
        with pytest.raises(ValueError):
            configmap.update(content="data=2")

    def test_update_propagates_api_exception(self, configmap, mock_core_api):
        mock_core_api.patch_namespaced_config_map.side_effect = make_api_exception(500)
        with pytest.raises(ApiException):
            configmap.update(filename="app.conf", content="data=2")


class TestConfigMapDelete:
    def test_delete_calls_api(self, configmap, mock_core_api):
        configmap.delete()
        mock_core_api.delete_namespaced_config_map.assert_called_once()
        call_kwargs = mock_core_api.delete_namespaced_config_map.call_args.kwargs
        assert call_kwargs["name"] == "test-cm"
        assert call_kwargs["namespace"] == "test-ns"

    def test_delete_404_does_not_raise(self, configmap, mock_core_api):
        mock_core_api.delete_namespaced_config_map.side_effect = make_api_exception(404)
        configmap.delete()  # should not raise

    @pytest.mark.parametrize("status_code", [400, 403, 500, 503])
    def test_delete_non_404_raises(self, configmap, mock_core_api, status_code):
        mock_core_api.delete_namespaced_config_map.side_effect = make_api_exception(
            status_code
        )
        with pytest.raises(ApiException) as exc_info:
            configmap.delete()
        assert exc_info.value.status == status_code
