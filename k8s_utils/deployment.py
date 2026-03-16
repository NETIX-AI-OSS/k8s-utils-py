import logging

from kubernetes import client
from kubernetes.client import ApiException

from k8s_utils.base import BaseConfig

logger = logging.getLogger(__name__)


class Deployment(BaseConfig):
    def __init__(
        self, app_name, namespace="default", sa_enabled=True, config_file=None
    ):
        self.app_name = app_name
        self.namespace = namespace
        self.__env_from_arr__ = []
        super().__init__(sa_enabled, config_file)

    def __create_env__(self, env_vars):
        logger.debug(type(env_vars))
        env_list = []
        for key, value in env_vars.items():
            env_list.append(client.V1EnvVar(name=key, value=value))
        return env_list

    def __create_body__(
        self,
        image,
        command,
        image_pull_secrets,
        image_pull_policy,
        env_vars,
        replicas=1,
        volume_name=None,
        volume_mount_path=None,
        volume_configmap_name=None,
        volume_configmap_key=None,
        volume_configmap_path=None,
    ):
        # create deployment object
        deployment = client.V1Deployment()

        # deployment fields
        deployment.api_version = "apps/v1"
        deployment.kind = "Deployment"
        deployment.metadata = client.V1ObjectMeta(
            name=self.app_name, namespace=self.namespace, labels={"app": self.app_name}
        )

        # deployment spec
        spec = client.V1DeploymentSpec(
            selector=client.V1LabelSelector(match_labels={"app": self.app_name}),
            template=client.V1PodTemplateSpec(),
            replicas=replicas,
        )
        spec.template.metadata = client.V1ObjectMeta(labels={"app": self.app_name})

        # container
        container = client.V1Container(
            name=self.app_name,
            image=image,
            image_pull_policy=(
                image_pull_policy if image_pull_policy is not None else ""
            ),
            command=command,
            env=self.__create_env__(env_vars if env_vars is not None else {}),
            env_from=self.__env_from_arr__,
            # ports=[client.V1ContainerPort(container_port=port)]
        )

        spec.template.spec = client.V1PodSpec(
            containers=[container],
        )
        if image_pull_secrets:
            spec.template.spec.image_pull_secrets = [
                client.V1LocalObjectReference(name=image_pull_secrets)
            ]

        # mount configmap data to volume
        self.__apply_volume_mount__(
            container,
            spec,
            volume_name,
            volume_mount_path,
            volume_configmap_name,
            volume_configmap_key,
            volume_configmap_path,
        )

        deployment.spec = spec
        return deployment

    def __apply_volume_mount__(
        self,
        container,
        spec,
        volume_name,
        volume_mount_path,
        volume_configmap_name,
        volume_configmap_key,
        volume_configmap_path,
    ):
        if not (
            volume_name
            and volume_mount_path
            and volume_configmap_name
            and volume_configmap_key
            and volume_configmap_path
        ):
            return
        container.volume_mounts = [
            {"mountPath": volume_mount_path, "name": volume_name}
        ]
        spec.template.spec.volumes = [
            client.V1Volume(
                name=volume_name,
                config_map=client.V1ConfigMapVolumeSource(
                    name=volume_configmap_name,
                    items=[
                        {"key": volume_configmap_key, "path": volume_configmap_path}
                    ],
                ),
            )
        ]

    def add_env_from(self, configmap_name):
        self.__env_from_arr__.append(
            client.V1EnvFromSource(
                config_map_ref=client.V1ConfigMapEnvSource(name=configmap_name)
            )
        )

    def create(
        self,
        image,
        command,
        image_pull_secrets=None,
        image_pull_policy=None,
        env_vars=None,
        replicas=1,
        volume_name=None,
        volume_mount_path=None,
        volume_configmap_name=None,
        volume_configmap_key=None,
        volume_configmap_path=None,
    ):

        body = self.__create_body__(
            image,
            command,
            image_pull_secrets,
            image_pull_policy,
            env_vars,
            replicas,
            volume_name,
            volume_mount_path,
            volume_configmap_name,
            volume_configmap_key,
            volume_configmap_path,
        )
        self.apps_api.create_namespaced_deployment(namespace=self.namespace, body=body)
        logger.info("Deployment Creation Done for %s", self.app_name)

    def update(
        self,
        image,
        command,
        image_pull_secrets=None,
        image_pull_policy=None,
        env_vars=None,
        replicas=1,
        volume_name=None,
        volume_mount_path=None,
        volume_configmap_name=None,
        volume_configmap_key=None,
        volume_configmap_path=None,
    ):
        body = self.__create_body__(
            image,
            command,
            image_pull_secrets,
            image_pull_policy,
            env_vars,
            replicas,
            volume_name,
            volume_mount_path,
            volume_configmap_name,
            volume_configmap_key,
            volume_configmap_path,
        )
        self.apps_api.replace_namespaced_deployment(
            name=self.app_name, namespace=self.namespace, body=body
        )
        logger.info("Deployment Updation Done for %s", self.app_name)

    def delete(self):
        try:
            self.apps_api.delete_namespaced_deployment(
                name=self.app_name,
                namespace=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )
            logger.info("Deployment Deletion Done for %s", self.app_name)
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "Deployment %s in namespace %s not found. Skipping delete.",
                    self.app_name,
                    self.namespace,
                )
            else:
                raise
