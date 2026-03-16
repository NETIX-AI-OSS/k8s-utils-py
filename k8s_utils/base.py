from kubernetes import client, config


class BaseConfig:
    def __init__(self, sa_enabled, config_file):
        if sa_enabled:
            config.load_incluster_config()
        else:
            config.load_kube_config(config_file=config_file)
        self.apps_api = client.AppsV1Api()
        self.api = client.CoreV1Api()
        self.networking_api = client.NetworkingV1Api()
