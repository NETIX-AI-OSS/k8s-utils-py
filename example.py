import json

from k8s_utils import ConfigMap, Deployment

data = {
    "global_config": {
        "kafka": {"address": "dfads", "topic": "dfads", "client_id": "dfads"}
    },
    "devices_config": [
        {
            "device": {
                "connection_properties": {
                    "url": "opc.tcp://10.190.0.44:53530/",
                    "user": "",
                    "password": "",
                },
                "type": 2,
                "id": 3,
            },
            "tags": [
                {
                    "id": 5,
                    "address": "ns=2;s=Simulation Examples.Functions.Ramp1",
                    "scaling": 10,
                    "scaling_enabled": True,
                }
            ],
        }
    ],
}

config = ConfigMap(name="example-config", sa_enabled=False)

config.create(filename="config.json", content=json.dumps(data))

deployment = Deployment(app_name="ubuntu", sa_enabled=False)
deployment.create(
    image="ubuntu",
    command=["/bin/bash", "-c", "sleep infinity"],
    volume_name="data",
    volume_mount_path="/etc/config",
    volume_configmap_name="example-config",
    volume_configmap_key="config.json",
    volume_configmap_path="config.json",
)
