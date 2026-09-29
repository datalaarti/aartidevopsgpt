import docker
from docker.errors import DockerException, NotFound


def get_docker_client():
    """
    Create and verify a connection to the Docker Engine
    running on the user's machine.
    """
    try:
        client = docker.from_env()
        client.ping()
        return client

    except DockerException as exc:
        raise RuntimeError(
            f"Unable to connect to Docker Engine: {exc}"
        ) from exc


def get_container(container_id: str) -> dict:
    """
    Collect basic information about a Docker container.
    This is read-only.
    """
    client = get_docker_client()

    try:
        container = client.containers.get(container_id)

    except NotFound as exc:
        raise ValueError(
            "Docker container not found."
        ) from exc

    attrs = container.attrs

    network_settings = attrs.get(
        "NetworkSettings",
        {}
    )

    state = attrs.get(
        "State",
        {}
    )

    return {
        "id": container.id,
        "short_id": container.short_id,
        "name": container.name,
        "status": container.status,
        "image": container.image.tags,
        "created": attrs.get("Created"),
        "started_at": state.get("StartedAt"),
        "finished_at": state.get("FinishedAt"),
        "exit_code": state.get("ExitCode"),
        "error": state.get("Error"),
        "restart_count": attrs.get(
            "RestartCount",
            0
        ),
        "ports": network_settings.get(
            "Ports"
        ),
        "networks": list(
            network_settings
            .get("Networks", {})
            .keys()
        ),
    }


def get_container_logs(
    container_id: str,
    tail: int = 500,
) -> str:
    """
    Retrieve the latest logs from a Docker container.
    This is read-only.
    """
    client = get_docker_client()

    try:
        container = client.containers.get(
            container_id
        )

    except NotFound as exc:
        raise ValueError(
            "Docker container not found."
        ) from exc

    logs = container.logs(
        stdout=True,
        stderr=True,
        tail=tail,
    )

    return logs.decode(
        "utf-8",
        errors="replace"
    )


def get_container_evidence(
    container_id: str,
) -> dict:
    """
    Collect the initial evidence required by
    the common Investigation Agent.
    """
    return {
        "container": get_container(
            container_id
        ),
        "logs": get_container_logs(
            container_id
        ),
    }


def get_additional_container_evidence(
    container_id: str,
) -> dict:
    """
    Collect deeper read-only Docker information when
    the initial evidence is not sufficient to determine
    the root cause.
    """
    client = get_docker_client()

    try:
        container = client.containers.get(
            container_id
        )

    except NotFound as exc:
        raise ValueError(
            "Docker container not found."
        ) from exc

    attrs = container.attrs

    state = attrs.get(
        "State",
        {}
    )

    config = attrs.get(
        "Config",
        {}
    )

    host_config = attrs.get(
        "HostConfig",
        {}
    )

    network_settings = attrs.get(
        "NetworkSettings",
        {}
    )

    return {
        "state": {
            "status": state.get("Status"),
            "running": state.get("Running"),
            "paused": state.get("Paused"),
            "restarting": state.get("Restarting"),
            "oom_killed": state.get("OOMKilled"),
            "dead": state.get("Dead"),
            "pid": state.get("Pid"),
            "exit_code": state.get("ExitCode"),
            "error": state.get("Error"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
        },

        "config": {
            "command": config.get("Cmd"),
            "entrypoint": config.get("Entrypoint"),
            "working_dir": config.get("WorkingDir"),
            "environment": config.get("Env", []),
            "exposed_ports": config.get(
                "ExposedPorts",
                {}
            ),
        },

        "host_config": {
            "restart_policy": host_config.get(
                "RestartPolicy"
            ),
            "network_mode": host_config.get(
                "NetworkMode"
            ),
            "binds": host_config.get(
                "Binds"
            ),
        },

        "mounts": attrs.get(
            "Mounts",
            []
        ),

        "networks": network_settings.get(
            "Networks",
            {}),
    }