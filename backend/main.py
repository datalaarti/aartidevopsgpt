from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import docker

from agents.graph import build_graph

from tools.kubernetes_tools import (
    get_kubernetes_status,
    get_nodes,
    get_pods,
    get_pod_details,
    get_pod_logs,
    get_deployments,
    get_services,
)


app = FastAPI(
    title="DevOpsGPT Backend",
    version="0.1.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Docker Connection
# --------------------------------------------------

try:
    docker_client = docker.from_env()
    docker_client.ping()
    docker_connected = True
except Exception:
    docker_client = None
    docker_connected = False


# --------------------------------------------------
# Root
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "DevOpsGPT Backend is running",
        "docker_connected": docker_connected,
    }


# ==================================================
# DOCKER APIs
# ==================================================


@app.get("/api/docker/status")
def docker_status():
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    return {
        "connected": True,
        "message": "Connected to Docker Engine",
    }


@app.get("/api/docker/containers")
def get_containers():
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    containers = docker_client.containers.list(
        all=True
    )

    result = []

    for container in containers:
        result.append(
            {
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "image": container.image.tags,
                "created": container.attrs.get(
                    "Created"
                ),
                "ports": container.attrs.get(
                    "NetworkSettings",
                    {},
                ).get(
                    "Ports"
                ),
            }
        )

    return {
        "count": len(result),
        "containers": result,
    }


@app.get("/api/docker/containers/{container_id}")
def get_container(container_id: str):
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    try:
        container = docker_client.containers.get(
            container_id
        )

        return {
            "id": container.id,
            "name": container.name,
            "status": container.status,
            "image": container.image.tags,
            "created": container.attrs.get(
                "Created"
            ),
            "ports": container.attrs.get(
                "NetworkSettings",
                {},
            ).get(
                "Ports"
            ),
            "networks": list(
                container.attrs.get(
                    "NetworkSettings",
                    {},
                )
                .get(
                    "Networks",
                    {}
                )
                .keys()
            ),
        }

    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail="Container not found",
        )


@app.get(
    "/api/docker/containers/{container_id}/logs"
)
def get_container_logs(container_id: str):
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    try:
        container = docker_client.containers.get(
            container_id
        )

        logs = container.logs(
            tail=500
        ).decode(
            "utf-8",
            errors="replace",
        )

        return {
            "container_id": container.id,
            "container_name": container.name,
            "logs": logs,
        }

    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail="Container not found",
        )


@app.get("/api/docker/images")
def get_images():
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    images = docker_client.images.list()

    result = []

    for image in images:
        result.append(
            {
                "id": image.id,
                "tags": image.tags,
                "created": image.attrs.get(
                    "Created"
                ),
                "size": image.attrs.get(
                    "Size"
                ),
            }
        )

    return {
        "count": len(result),
        "images": result,
    }


@app.get("/api/docker/volumes")
def get_volumes():
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    volumes = docker_client.volumes.list()

    return {
        "count": len(volumes),
        "volumes": [
            {
                "name": volume.name,
                "driver": volume.attrs.get(
                    "Driver"
                ),
            }
            for volume in volumes
        ],
    }


@app.get("/api/docker/networks")
def get_networks():
    if not docker_connected:
        raise HTTPException(
            status_code=503,
            detail="Docker Desktop is not available",
        )

    networks = docker_client.networks.list()

    return {
        "count": len(networks),
        "networks": [
            {
                "id": network.id,
                "name": network.name,
                "driver": network.attrs.get(
                    "Driver"
                ),
            }
            for network in networks
        ],
    }


# ==================================================
# COMMON AGENT PIPELINE
# ==================================================


class AgentAnalyzeRequest(BaseModel):
    domain: str
    resource_id: str


@app.post("/api/agent/analyze")
def analyze_with_agent(
    request: AgentAnalyzeRequest,
):
    """
    Run the common DevOpsGPT LangGraph pipeline
    against a selected infrastructure resource.
    """

    try:
        graph = build_graph()

        result = graph.invoke(
            {
                "domain": request.domain,
                "resource_id": request.resource_id,
            }
        )

        return {
            "domain": request.domain,
            "resource_id": request.resource_id,
            "investigation": result.get(
                "investigation"
            ),
            "root_cause": result.get(
                "root_cause"
            ),
            "rag_result": result.get(
                "rag_result"
            ),
            "solution": result.get(
                "solution"
            ),
            "verification": result.get(
                "verification"
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Agent analysis failed: {exc}"
            ),
        ) from exc


# ==================================================
# HUMAN APPROVAL + DOCKER REMEDIATION
# ==================================================


class ApprovalRequest(BaseModel):
    domain: str
    resource_id: str
    action: str
    approved: bool
    verification: dict[str, Any]


@app.post("/api/agent/approve")
def approve_action(
    request: ApprovalRequest,
):
    """
    Execute an approved remediation action.

    The action is executed only when:
    1. The user explicitly approved it.
    2. Verification marked it safe to execute.
    3. The requested domain and action are supported.
    """

    if not request.approved:
        return {
            "approved": False,
            "executed": False,
            "message": (
                "Action rejected by human approval."
            ),
        }

    if not request.verification.get(
        "safe_to_execute",
        False,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Action cannot be executed because "
                "verification did not mark it safe."
            ),
        )

    if request.domain != "docker":
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported remediation domain: "
                f"{request.domain}"
            ),
        )

    if request.action != "restart_container":
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported Docker action: "
                f"{request.action}"
            ),
        )

    from tools.docker_action_tools import (
        restart_container,
        verify_container_state,
    )

    try:
        # Execute approved remediation
        result = restart_container(
            request.resource_id
        )

        # Verify actual Docker state
        post_verification = (
            verify_container_state(
                request.resource_id
            )
        )

        resolved = post_verification.get(
            "healthy",
            False,
        )

        return {
            "approved": True,
            "executed": True,
            "action": request.action,
            "result": result,
            "post_verification": post_verification,
            "resolved": resolved,
            "message": (
                "Approved remediation executed "
                "successfully and post-remediation "
                "verification completed."
            ),
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Remediation failed: {exc}"
            ),
        ) from exc


# ==================================================
# KUBERNETES APIs
# ==================================================


@app.get("/api/kubernetes/status")
def kubernetes_status():
    """
    Return Kubernetes cluster connection status.
    """

    try:
        return get_kubernetes_status()

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Kubernetes cluster is unavailable: "
                f"{exc}"
            ),
        ) from exc


@app.get("/api/kubernetes/nodes")
def kubernetes_nodes():
    """
    Return Kubernetes nodes.
    """

    try:
        nodes = get_nodes()

        return {
            "count": len(nodes),
            "nodes": nodes,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unable to retrieve Kubernetes "
                f"nodes: {exc}"
            ),
        ) from exc


@app.get("/api/kubernetes/pods")
def kubernetes_pods(
    namespace: str = "default",
):
    """
    Return pods from a Kubernetes namespace.
    """

    try:
        pods = get_pods(
            namespace=namespace
        )

        return {
            "namespace": namespace,
            "count": len(pods),
            "pods": pods,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unable to retrieve Kubernetes "
                f"pods: {exc}"
            ),
        ) from exc


@app.get(
    "/api/kubernetes/pods/{pod_name}"
)
def kubernetes_pod_details(
    pod_name: str,
    namespace: str = "default",
):
    """
    Return details for a Kubernetes pod.
    """

    try:
        return get_pod_details(
            pod_name=pod_name,
            namespace=namespace,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unable to retrieve pod details: "
                f"{exc}"
            ),
        ) from exc


@app.get(
    "/api/kubernetes/pods/{pod_name}/logs"
)
def kubernetes_pod_logs(
    pod_name: str,
    namespace: str = "default",
    tail_lines: int = 500,
):
    """
    Return recent logs from a Kubernetes pod.
    """

    try:
        logs = get_pod_logs(
            pod_name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
        )

        return {
            "pod_name": pod_name,
            "namespace": namespace,
            "logs": logs,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Unable to retrieve pod logs: "
                f"{exc}"
            ),
        ) from exc


@app.get("/api/kubernetes/deployments")
def kubernetes_deployments(
    namespace: str = "default",
):
    """
    Return Kubernetes deployments.
    """

    try:
        deployments = get_deployments(
            namespace=namespace
        )

        return {
            "namespace": namespace,
            "count": len(deployments),
            "deployments": deployments,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to retrieve Kubernetes "
                f"deployments: {exc}"
            ),
        ) from exc


@app.get("/api/kubernetes/services")
def kubernetes_services(
    namespace: str = "default",
):
    """
    Return Kubernetes services.
    """

    try:
        services = get_services(
            namespace=namespace
        )

        return {
            "namespace": namespace,
            "count": len(services),
            "services": services,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to retrieve Kubernetes "
                f"services: {exc}"
            ),
        ) from exc