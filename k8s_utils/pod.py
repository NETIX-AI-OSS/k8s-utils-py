import logging

from kubernetes.client import ApiException

from k8s_utils.base import BaseConfig

logger = logging.getLogger(__name__)


class Pod(BaseConfig):
    def __init__(self, name, namespace="default", sa_enabled=True, config_file=None):
        self.name = name
        self.namespace = namespace
        super().__init__(sa_enabled, config_file)

    def delete(self):
        try:
            self.api.delete_namespaced_pod(self.name, self.namespace)
            logger.info("Pod %s deleted in namespace %s", self.name, self.namespace)
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "Pod %s in namespace %s not found. Skipping delete.",
                    self.name,
                    self.namespace,
                )
            else:
                raise

    def get_pods(self):
        try:
            pods = self.api.list_namespaced_pod(namespace=self.namespace)
            return pods.items
        except ApiException as e:
            logger.error("Error getting pods in namespace %s: %s", self.namespace, e)
            return None
