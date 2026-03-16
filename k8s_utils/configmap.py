import base64
import logging

from kubernetes.client import ApiException

from k8s_utils.base import BaseConfig

logger = logging.getLogger(__name__)


class ConfigMap(BaseConfig):
    def __init__(self, name, namespace="default", sa_enabled=True, config_file=None):
        self.name = name
        self.data = {}
        self.namespace = namespace
        super().__init__(sa_enabled, config_file)

    def _build_body_data(self, filename=None, content=None):
        if filename is None and content is None:
            return dict(self.data)
        if filename is None or content is None:
            raise ValueError("filename and content must be provided together")
        return {filename: content}

    def _build_body(self, data):
        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "namespace": self.namespace,
            "metadata": {"name": self.name},
            "data": data,
        }

    def upsert_key_binary(self, name, content):
        encoded_data = base64.b64encode(content).decode("utf-8")
        self.data[name] = encoded_data

    def upsert_key(self, name, content):
        self.data[name] = content

    def delete_key(self, name):
        del self.data[name]

    def create(self, filename=None, content=None):
        body = self._build_body(
            self._build_body_data(filename=filename, content=content)
        )
        logger.info("Created configmap.")
        return self.api.create_namespaced_config_map(
            namespace=self.namespace, body=body
        )

    def update(self, filename=None, content=None):
        body = self._build_body(
            self._build_body_data(filename=filename, content=content)
        )
        logger.info("Updated configmap.")
        return self.api.patch_namespaced_config_map(
            name=self.name, namespace=self.namespace, body=body
        )

    def delete(self):
        try:
            self.api.delete_namespaced_config_map(
                name=self.name, namespace=self.namespace
            )
            logger.info(
                "Deleted configmap %s in namespace %s.", self.name, self.namespace
            )
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "Configmap %s in namespace %s not found. Skipping delete.",
                    self.name,
                    self.namespace,
                )
            else:
                raise
