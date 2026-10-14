import pytest
from kubernetes.client import ApiClient, ApiException, V1ResourceRequirements

from tests.conftest import make_api_exception


class TestDeploymentInit:
    def test_init_sets_app_name_and_namespace(self, deployment):
        assert deployment.app_name == "test-app"
        assert deployment.namespace == "test-ns"

    def test_init_env_from_arr_is_empty(self, deployment):
        assert deployment.__env_from_arr__ == []


class TestAddEnvFrom:
    def test_add_env_from_appends_env_from_source(self, deployment):
        deployment.add_env_from("my-configmap")
        assert len(deployment.__env_from_arr__) == 1
        assert deployment.__env_from_arr__[0].config_map_ref.name == "my-configmap"

    def test_add_env_from_multiple_calls_accumulate(self, deployment):
        deployment.add_env_from("cm-1")
        deployment.add_env_from("cm-2")
        assert len(deployment.__env_from_arr__) == 2
        assert deployment.__env_from_arr__[0].config_map_ref.name == "cm-1"
        assert deployment.__env_from_arr__[1].config_map_ref.name == "cm-2"


class TestCreateEnv:
    def test_create_env_empty_dict_returns_empty_list(self, deployment):
        result = deployment.__create_env__({})
        assert result == []

    def test_create_env_dict_to_v1envvar_list(self, deployment):
        result = deployment.__create_env__({"FOO": "bar", "BAZ": "qux"})
        assert len(result) == 2
        names = {e.name for e in result}
        values = {e.value for e in result}
        assert names == {"FOO", "BAZ"}
        assert values == {"bar", "qux"}


class TestCreateBody:
    def _call_create_and_capture(self, deployment, **kwargs):
        defaults = {
            "image": "nginx:latest",
            "command": ["/bin/sh"],
            "image_pull_secrets": "my-secret",
            "image_pull_policy": None,
            "env_vars": None,
        }
        defaults.update(kwargs)
        deployment.create(**defaults)
        call_args = deployment.apps_api.create_namespaced_deployment.call_args
        return call_args.kwargs["body"]

    def test_create_body_metadata(self, deployment, mock_apps_api):
        body = self._call_create_and_capture(deployment)
        assert body.metadata.name == "test-app"
        assert body.metadata.namespace == "test-ns"
        assert body.metadata.labels == {"app": "test-app"}

    def test_create_body_replicas_defaults_to_1(self, deployment, mock_apps_api):
        body = self._call_create_and_capture(deployment)
        assert body.spec.replicas == 1

    def test_create_body_replicas_custom(self, deployment, mock_apps_api):
        body = self._call_create_and_capture(deployment, replicas=3)
        assert body.spec.replicas == 3

    def test_update_body_replicas_custom(self, deployment, mock_apps_api):
        deployment.update(
            image="nginx:latest",
            command=["/bin/sh"],
            image_pull_secrets="my-secret",
            replicas=5,
        )
        call_args = deployment.apps_api.replace_namespaced_deployment.call_args
        body = call_args.kwargs["body"]
        assert body.spec.replicas == 5

    def test_create_body_container_image_and_command(self, deployment, mock_apps_api):
        body = self._call_create_and_capture(
            deployment, image="myimg:v2", command=["/start"]
        )
        container = body.spec.template.spec.containers[0]
        assert container.image == "myimg:v2"
        assert container.command == ["/start"]

    def test_create_body_image_pull_policy_defaults_to_empty_string(
        self, deployment, mock_apps_api
    ):
        body = self._call_create_and_capture(deployment)
        container = body.spec.template.spec.containers[0]
        assert container.image_pull_policy == ""

    def test_create_body_image_pull_policy_set_when_provided(
        self, deployment, mock_apps_api
    ):
        body = self._call_create_and_capture(deployment, image_pull_policy="Always")
        container = body.spec.template.spec.containers[0]
        assert container.image_pull_policy == "Always"

    def test_create_body_image_pull_secrets(self, deployment, mock_apps_api):
        body = self._call_create_and_capture(
            deployment, image_pull_secrets="registry-creds"
        )
        assert body.spec.template.spec.image_pull_secrets[0].name == "registry-creds"

    def test_create_body_omits_image_pull_secrets_when_not_provided(
        self, deployment, mock_apps_api
    ):
        body = self._call_create_and_capture(deployment, image_pull_secrets=None)
        assert body.spec.template.spec.image_pull_secrets is None

    def test_create_body_no_volume_when_all_params_absent(
        self, deployment, mock_apps_api
    ):
        body = self._call_create_and_capture(deployment)
        container = body.spec.template.spec.containers[0]
        assert container.volume_mounts is None
        assert body.spec.template.spec.volumes is None

    def test_create_body_volume_mounted_when_all_5_params_provided(
        self, deployment, mock_apps_api
    ):
        body = self._call_create_and_capture(
            deployment,
            volume_name="data-vol",
            volume_mount_path="/etc/config",
            volume_configmap_name="my-cm",
            volume_configmap_key="app.conf",
            volume_configmap_path="app.conf",
        )
        container = body.spec.template.spec.containers[0]
        assert container.volume_mounts[0].name == "data-vol"
        assert container.volume_mounts[0].mount_path == "/etc/config"

        vol = body.spec.template.spec.volumes[0]
        assert vol.name == "data-vol"
        assert vol.config_map.name == "my-cm"
        assert vol.config_map.items[0].key == "app.conf"
        assert vol.config_map.items[0].path == "app.conf"

    @pytest.mark.parametrize(
        "missing_param",
        [
            "volume_name",
            "volume_mount_path",
            "volume_configmap_name",
            "volume_configmap_key",
            "volume_configmap_path",
        ],
    )
    def test_create_body_no_volume_when_any_one_param_missing(
        self, deployment, mock_apps_api, missing_param
    ):
        vol_kwargs = {
            "volume_name": "data-vol",
            "volume_mount_path": "/etc/config",
            "volume_configmap_name": "my-cm",
            "volume_configmap_key": "app.conf",
            "volume_configmap_path": "app.conf",
        }
        vol_kwargs[missing_param] = None
        body = self._call_create_and_capture(deployment, **vol_kwargs)
        container = body.spec.template.spec.containers[0]
        assert container.volume_mounts is None
        assert body.spec.template.spec.volumes is None


class TestCreateBodyWireFormat:
    def test_full_body_serializes_to_the_v1_0_manifest(self, deployment):
        deployment.add_env_from("my-cm")
        body = deployment.__create_body__(
            image="nginx:latest",
            command=["/bin/sh"],
            image_pull_secrets="regcred",
            image_pull_policy="Always",
            env_vars={"FOO": "bar"},
            replicas=2,
            volume_name="data-vol",
            volume_mount_path="/etc/config",
            volume_configmap_name="my-cm",
            volume_configmap_key="app.conf",
            volume_configmap_path="app.conf",
        )
        assert ApiClient().sanitize_for_serialization(body) == {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "labels": {"app": "test-app"},
                "name": "test-app",
                "namespace": "test-ns",
            },
            "spec": {
                "replicas": 2,
                "selector": {"matchLabels": {"app": "test-app"}},
                "template": {
                    "metadata": {"labels": {"app": "test-app"}},
                    "spec": {
                        "containers": [
                            {
                                "command": ["/bin/sh"],
                                "env": [{"name": "FOO", "value": "bar"}],
                                "envFrom": [{"configMapRef": {"name": "my-cm"}}],
                                "image": "nginx:latest",
                                "imagePullPolicy": "Always",
                                "name": "test-app",
                                "volumeMounts": [
                                    {"mountPath": "/etc/config", "name": "data-vol"}
                                ],
                            }
                        ],
                        "imagePullSecrets": [{"name": "regcred"}],
                        "volumes": [
                            {
                                "configMap": {
                                    "items": [{"key": "app.conf", "path": "app.conf"}],
                                    "name": "my-cm",
                                },
                                "name": "data-vol",
                            }
                        ],
                    },
                },
            },
        }

    def test_minimal_body_serializes_to_the_v1_0_manifest(self, deployment):
        body = deployment.__create_body__(
            image="nginx",
            command=["/bin/sh"],
            image_pull_secrets=None,
            image_pull_policy=None,
            env_vars=None,
        )
        assert ApiClient().sanitize_for_serialization(body) == {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "labels": {"app": "test-app"},
                "name": "test-app",
                "namespace": "test-ns",
            },
            "spec": {
                "replicas": 1,
                "selector": {"matchLabels": {"app": "test-app"}},
                "template": {
                    "metadata": {"labels": {"app": "test-app"}},
                    "spec": {
                        "containers": [
                            {
                                "command": ["/bin/sh"],
                                "env": [],
                                "envFrom": [],
                                "image": "nginx",
                                "imagePullPolicy": "",
                                "name": "test-app",
                            }
                        ]
                    },
                },
            },
        }

    def test_body_stays_mutable_for_callers_that_stamp_extra_fields(self, deployment):
        body = deployment.__create_body__(
            image="nginx",
            command=["/bin/sh"],
            image_pull_secrets=None,
            image_pull_policy=None,
            env_vars=None,
        )
        body.spec.template.metadata.annotations = {"rev": "2"}
        body.spec.template.spec.containers[0].resources = V1ResourceRequirements(
            requests={"cpu": "50m"}
        )
        wire = ApiClient().sanitize_for_serialization(body)
        assert wire["spec"]["template"]["metadata"]["annotations"] == {"rev": "2"}
        container = wire["spec"]["template"]["spec"]["containers"][0]
        assert container["resources"] == {"requests": {"cpu": "50m"}}


class TestDeploymentApiCalls:
    def test_create_calls_api_with_correct_namespace(self, deployment, mock_apps_api):
        deployment.create(
            image="nginx", command=["/bin/sh"], image_pull_secrets="secret"
        )
        mock_apps_api.create_namespaced_deployment.assert_called_once()
        call_kwargs = mock_apps_api.create_namespaced_deployment.call_args.kwargs
        assert call_kwargs["namespace"] == "test-ns"

    def test_create_propagates_api_exception(self, deployment, mock_apps_api):
        mock_apps_api.create_namespaced_deployment.side_effect = make_api_exception(409)
        with pytest.raises(ApiException):
            deployment.create(
                image="nginx",
                command=["/bin/sh"],
                image_pull_secrets="secret",
            )

    def test_update_calls_replace_namespaced_deployment(
        self, deployment, mock_apps_api
    ):
        deployment.update(
            image="nginx:v2", command=["/bin/sh"], image_pull_secrets="secret"
        )
        mock_apps_api.replace_namespaced_deployment.assert_called_once()
        call_kwargs = mock_apps_api.replace_namespaced_deployment.call_args.kwargs
        assert call_kwargs["name"] == "test-app"
        assert call_kwargs["namespace"] == "test-ns"

    def test_update_propagates_api_exception(self, deployment, mock_apps_api):
        mock_apps_api.replace_namespaced_deployment.side_effect = make_api_exception(
            500
        )
        with pytest.raises(ApiException):
            deployment.update(
                image="nginx",
                command=["/bin/sh"],
                image_pull_secrets="secret",
            )

    def test_delete_calls_api_with_foreground_propagation_and_grace_period(
        self, deployment, mock_apps_api
    ):
        deployment.delete()
        mock_apps_api.delete_namespaced_deployment.assert_called_once()
        call_kwargs = mock_apps_api.delete_namespaced_deployment.call_args.kwargs
        assert call_kwargs["name"] == "test-app"
        assert call_kwargs["namespace"] == "test-ns"
        body = call_kwargs["body"]
        assert body.propagation_policy == "Foreground"
        assert body.grace_period_seconds == 5

    def test_delete_404_does_not_raise(self, deployment, mock_apps_api):
        mock_apps_api.delete_namespaced_deployment.side_effect = make_api_exception(404)
        deployment.delete()  # should not raise

    def test_delete_404_logs_warning(self, deployment, mock_apps_api, caplog):
        mock_apps_api.delete_namespaced_deployment.side_effect = make_api_exception(404)
        import logging

        with caplog.at_level(logging.WARNING):
            deployment.delete()
        assert "not found" in caplog.text.lower()

    @pytest.mark.parametrize("status_code", [400, 403, 409, 500, 503])
    def test_delete_non_404_raises(self, deployment, mock_apps_api, status_code):
        mock_apps_api.delete_namespaced_deployment.side_effect = make_api_exception(
            status_code
        )
        with pytest.raises(ApiException) as exc_info:
            deployment.delete()
        assert exc_info.value.status == status_code
