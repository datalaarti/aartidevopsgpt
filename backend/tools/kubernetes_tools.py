from datetime import date, datetime
import ast

from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
def _make_json_safe(value):
    """
    Convert Kubernetes/Python objects into JSON-safe values.
    """

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: _make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            _make_json_safe(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            _make_json_safe(item)
            for item in value
        ]

    return value


def get_kubernetes_clients():
    """
    Load the user's current Kubernetes kubeconfig
    and return CoreV1Api and AppsV1Api clients.
    """

    try:
        config.load_kube_config()
    except ConfigException as exc:
        raise RuntimeError(
            f"Unable to load Kubernetes configuration: {exc}"
        ) from exc

    return (
        client.CoreV1Api(),
        client.AppsV1Api(),
    )


def get_kubernetes_status() -> dict:
    """
    Return basic Kubernetes cluster status.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        nodes = core_api.list_node().items

        return {
            "connected": True,
            "node_count": len(nodes),
            "nodes": [
                {
                    "name": node.metadata.name,
                    "status": (
                        node.status.conditions[-1].type
                        if node.status.conditions
                        else "Unknown"
                    ),
                }
                for node in nodes
            ],
        }

    except Exception as exc:
        raise RuntimeError(
            f"Unable to query Kubernetes cluster: {exc}"
        ) from exc


def get_nodes() -> list[dict]:
    """
    Return Kubernetes nodes and their readiness status.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        nodes = core_api.list_node().items

        result = []

        for node in nodes:
            ready = False

            for condition in node.status.conditions or []:
                if condition.type == "Ready":
                    ready = condition.status == "True"
                    break

            result.append(
                {
                    "name": node.metadata.name,
                    "ready": ready,
                    "status": (
                        "Ready" if ready else "NotReady"
                    ),
                    "roles": [
                        key.replace(
                            "node-role.kubernetes.io/",
                            "",
                        )
                        for key in (
                            node.metadata.labels or {}
                        )
                        if key.startswith(
                            "node-role.kubernetes.io/"
                        )
                    ],
                    "version": (
                        node.status.node_info.kubelet_version
                        if node.status.node_info
                        else None
                    ),
                }
            )

        return result

    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve Kubernetes nodes: {exc}"
        ) from exc


def get_pods(
    namespace: str = "default",
) -> list[dict]:
    """
    Return pods from the requested namespace.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        pods = core_api.list_namespaced_pod(
            namespace=namespace
        ).items

        return [
            {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": (
                    pod.status.phase
                    if pod.status
                    else "Unknown"
                ),
                "node": pod.spec.node_name
                if pod.spec
                else None,
                "restarts": sum(
                    container.restart_count or 0
                    for container in (
                        pod.status.container_statuses
                        or []
                    )
                ),
            }
            for pod in pods
        ]

    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve Kubernetes pods: {exc}"
        ) from exc


def get_pod_details(
    pod_name: str,
    namespace: str = "default",
) -> dict:
    """
    Return detailed information for a Kubernetes pod.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        pod = core_api.read_namespaced_pod(
            name=pod_name,
            namespace=namespace,
        )

        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "status": (
                pod.status.phase
                if pod.status
                else "Unknown"
            ),
            "node": (
                pod.spec.node_name
                if pod.spec
                else None
            ),
            "containers": [
                {
                    "name": container.name,
                    "image": container.image,
                    "command": container.command,
                }
                for container in (
                    pod.spec.containers or []
                )
            ],
            "container_statuses": [
                {
                    "name": status.name,
                    "ready": status.ready,
                    "restart_count": status.restart_count,
                    "state": _make_json_safe(
                        status.state.to_dict()
                        if status.state
                        else None
                    ),
                    "last_state": _make_json_safe(
                        status.last_state.to_dict()
                        if status.last_state
                        else None
                    ),
                }
                for status in (
                    pod.status.container_statuses
                    or []
                )
            ],
        }

    except client.exceptions.ApiException as exc:
        if exc.status == 404:
            raise ValueError(
                "Kubernetes pod not found."
            ) from exc

        raise RuntimeError(
            f"Unable to retrieve pod details: {exc}"
        ) from exc

def get_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 500,
) -> str:
    """
    Return recent logs from a Kubernetes pod.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        logs = core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
        )

        if isinstance(logs, bytes):
            return logs.decode(
                "utf-8",
                errors="replace",
            )

        logs = str(logs)

        # Some Kubernetes client/runtime combinations can
        # return a string containing a bytes literal such as:
        # b'/docker-entrypoint.sh: ...'
        if logs.startswith("b'") and logs.endswith("'"):
            try:
                parsed = ast.literal_eval(logs)

                if isinstance(parsed, bytes):
                    return parsed.decode(
                        "utf-8",
                        errors="replace",
                    )
            except (ValueError, SyntaxError):
                pass

        return logs

    except client.exceptions.ApiException as exc:
        if exc.status == 404:
            raise ValueError(
                "Kubernetes pod not found."
            ) from exc

        raise RuntimeError(
            f"Unable to retrieve pod logs: {exc}"
        ) from exc
def get_pod_events(
    pod_name: str,
    namespace: str = "default",
) -> list[dict]:
    """
    Return Kubernetes events associated with a pod.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        events = core_api.list_namespaced_event(
            namespace=namespace,
            field_selector=(
                f"involvedObject.name={pod_name}"
            ),
        ).items

        return [
            {
                "name": event.metadata.name
                if event.metadata
                else None,
                "type": event.type,
                "reason": event.reason,
                "message": event.message,
                "count": event.count,
                "first_timestamp": (
                    event.first_timestamp
                ),
                "last_timestamp": (
                    event.last_timestamp
                ),
                "involved_object": (
                    event.involved_object.name
                    if event.involved_object
                    else None
                ),
            }
            for event in events
        ]

    except client.exceptions.ApiException as exc:
        raise RuntimeError(
            f"Unable to retrieve Kubernetes pod events: {exc}"
        ) from exc
def get_deployments(
    namespace: str = "default",
) -> list[dict]:
    """
    Return Kubernetes deployments.
    """

    _, apps_api = get_kubernetes_clients()

    try:
        deployments = apps_api.list_namespaced_deployment(
            namespace=namespace
        ).items

        return [
            {
                "name": deployment.metadata.name,
                "namespace": deployment.metadata.namespace,
                "replicas": (
                    deployment.spec.replicas
                    if deployment.spec
                    else 0
                ),
                "available_replicas": (
                    deployment.status.available_replicas or 0
                    if deployment.status
                    else 0
                ),
                "ready_replicas": (
                    deployment.status.ready_replicas or 0
                    if deployment.status
                    else 0
                ),
            }
            for deployment in deployments
        ]

    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve Kubernetes deployments: {exc}"
        ) from exc


def get_services(
    namespace: str = "default",
) -> list[dict]:
    """
    Return Kubernetes services.
    """

    core_api, _ = get_kubernetes_clients()

    try:
        services = core_api.list_namespaced_service(
            namespace=namespace
        ).items

        return [
            {
                "name": service.metadata.name,
                "namespace": service.metadata.namespace,
                "type": (
                    service.spec.type
                    if service.spec
                    else "Unknown"
                ),
                "cluster_ip": (
                    service.spec.cluster_ip
                    if service.spec
                    else None
                ),
                "ports": [
                    {
                        "port": port.port,
                        "target_port": str(
                            port.target_port
                        ),
                        "protocol": port.protocol,
                    }
                    for port in (
                        service.spec.ports or []
                    )
                ],
            }
            for service in services
        ]

    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve Kubernetes services: {exc}"
        ) from exc
# --------------------------------------------------
# DevOpsGPT Agent Evidence
# --------------------------------------------------

def _parse_pod_resource_id(resource_id: str) -> tuple[str, str]:
    """
    Accept either:
        pod-name
    or:
        namespace/pod-name
    """

    if "/" in resource_id:
        namespace, pod_name = resource_id.split(
            "/",
            1,
        )

        namespace = namespace.strip()
        pod_name = pod_name.strip()

        if namespace and pod_name:
            return namespace, pod_name

    return "default", resource_id.strip()


def get_pod_evidence(resource_id: str) -> dict:
    """
    Collect initial read-only evidence for a Kubernetes pod.
    """

    namespace, pod_name = _parse_pod_resource_id(
        resource_id
    )

    details = get_pod_details(
        pod_name=pod_name,
        namespace=namespace,
    )

    logs = get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        tail_lines=500,
    )

    return {
        "resource_type": "pod",
        "namespace": namespace,
        "pod_name": pod_name,
        "pod": details,
        "logs": logs,
    }


def get_additional_pod_evidence(
    resource_id: str,
) -> dict:
    """
    Collect deeper read-only Kubernetes evidence
    when initial evidence is insufficient.
    """

    namespace, pod_name = _parse_pod_resource_id(
        resource_id
    )

    details = get_pod_details(
        pod_name=pod_name,
        namespace=namespace,
    )

    current_logs = get_pod_logs(
        pod_name=pod_name,
        namespace=namespace,
        tail_lines=1000,
    )

    # --------------------------------------------------
    # Previous container logs
    # --------------------------------------------------

    core_api, _ = get_kubernetes_clients()

    previous_logs: dict[str, str] = {}

    for container in details.get(
        "containers",
        [],
    ):
        container_name = container.get(
            "name"
        )

        if not container_name:
            continue

        try:
            logs = core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=namespace,
                container=container_name,
                previous=True,
                tail_lines=1000,
            )

            if isinstance(logs, bytes):
                logs = logs.decode(
                    "utf-8",
                    errors="replace",
                )
            else:
                logs = str(logs)

            previous_logs[container_name] = logs

        except client.exceptions.ApiException:
            # No previous container instance/logs
            # may be available.
            previous_logs[container_name] = ""

    # --------------------------------------------------
    # Kubernetes events
    # --------------------------------------------------

    events = get_pod_events(
        pod_name=pod_name,
        namespace=namespace,
    )

    return _make_json_safe(
        {
            "resource_type": "pod",
            "namespace": namespace,
            "pod_name": pod_name,
            "pod": details,
            "logs": current_logs,
            "previous_logs": previous_logs,
            "events": events,
            "additional_evidence": True,
        }
    )