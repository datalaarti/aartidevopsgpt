import docker
from docker.errors import DockerException, NotFound


def get_docker_client():
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as exc:
        raise RuntimeError(
            f"Unable to connect to Docker Engine: {exc}"
        ) from exc


def restart_container(container_id: str) -> dict:
    """
    Restart a Docker container.

    This is an action tool and must only be called
    after explicit human approval.
    """

    client = get_docker_client()

    try:
        container = client.containers.get(container_id)
    except NotFound as exc:
        raise ValueError("Docker container not found.") from exc

    container.restart()

    container.reload()

    return {
        "action": "restart_container",
        "container_id": container.id,
        "container_name": container.name,
        "status": container.status,
        "message": (
            f"Container '{container.name}' was restarted successfully."
        ),
    }
def verify_container_state(container_id: str) -> dict:
    """
    Verify the actual Docker container state after remediation.
    """

    client = get_docker_client()

    try:
        container = client.containers.get(container_id)
    except NotFound as exc:
        raise ValueError("Docker container not found.") from exc

    container.reload()

    attrs = container.attrs
    state = attrs.get("State", {})

    logs = container.logs(
        stdout=True,
        stderr=True,
        tail=100,
    ).decode("utf-8", errors="replace")

    return {
        "container_id": container.id,
        "container_name": container.name,
        "status": container.status,
        "running": state.get("Running"),
        "exit_code": state.get("ExitCode"),
        "error": state.get("Error"),
        "restart_count": attrs.get("RestartCount", 0),
        "logs": logs,
        "healthy": container.status == "running"
        and not state.get("Error"),
    }