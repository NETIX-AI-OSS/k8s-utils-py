import logging

from kubernetes import client
from kubernetes.client import ApiException

from k8s_utils.base import BaseConfig

logger = logging.getLogger(__name__)


class Ingress(BaseConfig):
    def __init__(
        self, app_name, namespace, domain_name, sa_enabled=True, config_file=None
    ):
        self.app_name = app_name
        self.namespace = namespace
        self.domain_name = domain_name
        super().__init__(sa_enabled, config_file)

        self.annotations = {
            "kubernetes.io/ingress.class": "nginx",
            "nginx.ingress.kubernetes.io/add-headers": "X-Frame-Options: SAMEORIGIN",
            "nginx.ingress.kubernetes.io/use-gzip": "true",
            "nginx.ingress.kubernetes.io/enable-brotli": "true",
            "nginx.ingress.kubernetes.io/enable-modsecurity": "true",
            "nginx.ingress.kubernetes.io/enable-owasp-modsecurity-crs": "true",
            "nginx.ingress.kubernetes.io/modsecurity-transaction-id": "$request_id",
            # "nginx.ingress.kubernetes.io/modsecurity-snippet": |
            #   SecRuleEngine On
            #   SecRequestBodyAccess On
            #   SecAuditLogParts ABIJDEFHZ
            #   SecAuditEngine RelevantOnly
            #   SecAuditLogType Serial
            #   SecAuditLog /dev/stdout
            #   SecRule REQUEST_HEADERS:User-Agent \"fern-scanner\"
            #   \"log,deny,id:107,status:403,msg:'Fern Scanner Identified'\"
            # Include /etc/nginx/owasp-modsecurity-crs/nginx-modsecurity.conf
            "nginx.ingress.kubernetes.io/limit-connection": "60",
            "nginx.ingress.kubernetes.io/limit-rpm": "600",
            # Redirects HTTP to HTTPS for all requests.
            "nginx.ingress.kubernetes.io/ssl-redirect": "true",
            # Indicates which certificate issuer is used.
            "cert-manager.io/cluster-issuer": "letsencrypt-prod",
            "nginx.ingress.kubernetes.io/proxy-body-size": "0",
            "nginx.ingress.kubernetes.io/proxy-read-timeout": "600",
            "nginx.ingress.kubernetes.io/proxy-send-timeout": "600",
            "kubernetes.io/tls-acme": "true",
        }

    def create(self, port, service_name, username):
        body = client.V1Ingress(
            api_version="networking.k8s.io/v1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=f"{self.app_name}-ingress", annotations=self.annotations
            ),
            spec=client.V1IngressSpec(
                tls=[
                    client.V1IngressTLS(
                        hosts=[f"{username}.cdr.{self.domain_name}"],
                        secret_name=f"{username}-code-tls",
                    )
                ],
                rules=[
                    client.V1IngressRule(
                        host=f"{username}.cdr.{self.domain_name}",
                        http=client.V1HTTPIngressRuleValue(
                            paths=[
                                client.V1HTTPIngressPath(
                                    path="/",
                                    path_type="Prefix",
                                    backend=client.V1IngressBackend(
                                        service=client.V1IngressServiceBackend(
                                            port=client.V1ServiceBackendPort(
                                                number=port,
                                            ),
                                            name=service_name,
                                        )
                                    ),
                                )
                            ]
                        ),
                    )
                ],
            ),
        )

        self.networking_api.create_namespaced_ingress(
            namespace=self.namespace, body=body
        )
        logger.info("Ingress Creation Done for %s", self.app_name)

    def delete(self):
        try:
            self.networking_api.delete_namespaced_ingress(
                name=f"{self.app_name}-ingress", namespace=self.namespace
            )
            logger.info("Ingress Deletion Done for %s", self.app_name)
        except ApiException as exc:
            if exc.status == 404:
                logger.warning(
                    "Ingress %s in namespace %s not found. Skipping delete.",
                    self.app_name,
                    self.namespace,
                )
            else:
                raise
