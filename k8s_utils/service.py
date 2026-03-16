import logging

from kubernetes import client
from kubernetes.client import ApiException

from k8s_utils.base import BaseConfig

logger = logging.getLogger(__name__)


class Service(BaseConfig):
    def __init__(self, app_name, namespace, sa_enabled=True, config_file=None):
        self.app_name = app_name
        self.namespace = namespace
        super().__init__(sa_enabled, config_file)

    def __create_body__(self, port):
        service = client.V1Service()

        # service fields
        service.api_version = "v1"
        service.kind = "Service"
        service.metadata = client.V1ObjectMeta(
            name=self.app_name, namespace=self.namespace
        )

        # spec fields
        spec = client.V1ServiceSpec()
        spec.selector = {"app": self.app_name}
        spec.ports = [client.V1ServicePort(protocol="TCP", port=80, target_port=port)]
        service.spec = spec
        logger.info("Service body created.")
        return service

    def create(self, port):
        service = self.__create_body__(port=port)
        self.api.create_namespaced_service(namespace=self.namespace, body=service)
        logger.info("Service Creation Done for %s", self.app_name)

    def delete(self):
        try:
            self.api.delete_namespaced_service(
                name=self.app_name, namespace=self.namespace
            )
            logger.info("Service Deletion Done for %s", self.app_name)
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "Service %s in namespace %s not found. Skipping delete.",
                    self.app_name,
                    self.namespace,
                )
            else:
                raise
