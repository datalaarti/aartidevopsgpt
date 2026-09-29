from typing import Any


def investigate_docker_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze Docker evidence.

    This stage reports observations and does not
    invent a root cause or recommend remediation.
    """

    container = evidence.get("container", {})
    logs = evidence.get("logs", "")

    additional = evidence.get(
        "additional_evidence",
        {},
    )

    status = container.get("status")
    exit_code = container.get("exit_code")
    error = container.get("error")

    restart_count = container.get(
        "restart_count",
        0,
    )

    observations: list[str] = []

    # --------------------------------------------------
    # Container status
    # --------------------------------------------------

    if status != "running":
        observations.append(
            f"Container is not running. Current status: {status}."
        )
    else:
        observations.append(
            "Container is currently running."
        )

    # --------------------------------------------------
    # Exit code
    # --------------------------------------------------

    if exit_code is not None:
        observations.append(
            f"Container exit code: {exit_code}."
        )

    # --------------------------------------------------
    # Restart count
    # --------------------------------------------------

    if restart_count:
        observations.append(
            f"Container has restarted {restart_count} time(s)."
        )
    else:
        observations.append(
            "No container restart count was recorded."
        )

    # --------------------------------------------------
    # Docker error
    # --------------------------------------------------

    if error:
        observations.append(
            f"Docker reported an error: {error}."
        )

    # --------------------------------------------------
    # Logs
    # --------------------------------------------------

    if logs.strip():
        observations.append(
            "Container logs were successfully collected."
        )
    else:
        observations.append(
            "No container logs were available."
        )

    # --------------------------------------------------
    # Additional Docker state
    # --------------------------------------------------

    state = additional.get(
        "state",
        {},
    )

    config = additional.get(
        "config",
        {},
    )

    host_config = additional.get(
        "host_config",
        {},
    )

    # --------------------------------------------------
    # Container state
    # --------------------------------------------------

    if state:
        observations.append(
            f"OOM-killed status: {state.get('oom_killed')}."
        )

        observations.append(
            f"Restarting flag: {state.get('restarting')}."
        )

        observations.append(
            f"Container dead flag: {state.get('dead')}."
        )

        if state.get("error"):
            observations.append(
                f"Container state error: {state.get('error')}."
            )

    # --------------------------------------------------
    # Container configuration
    # --------------------------------------------------

    if config:
        command = config.get("command")
        entrypoint = config.get("entrypoint")
        working_dir = config.get(
            "working_dir"
        )

        if command:
            observations.append(
                f"Container command: {command}."
            )

        if entrypoint:
            observations.append(
                f"Container entrypoint: {entrypoint}."
            )

        if working_dir:
            observations.append(
                f"Container working directory: {working_dir}."
            )

    # --------------------------------------------------
    # Host configuration
    # --------------------------------------------------

    if host_config:
        restart_policy = host_config.get(
            "restart_policy"
        )

        network_mode = host_config.get(
            "network_mode"
        )

        if restart_policy:
            observations.append(
                f"Restart policy: {restart_policy}."
            )

        if network_mode:
            observations.append(
                f"Network mode: {network_mode}."
            )

    return {
        "container_name": container.get(
            "name"
        ),
        "status": status,
        "observations": observations,
        "logs_available": bool(
            logs.strip()
        ),
        "additional_evidence_available": bool(
            additional
        ),
        "evidence_complete": bool(
            container and logs.strip()
        ),
    }

def investigate_kubernetes_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Analyze Kubernetes pod evidence.

    This is the Kubernetes implementation of the
    shared Investigation stage.

    It reports facts from:
    - current pod state
    - container readiness
    - restart counts
    - current container state
    - previous container termination state
    - current logs
    - previous logs
    - Kubernetes events

    It does NOT invent a root cause and does NOT
    recommend remediation.
    """

    pod = evidence.get(
        "pod",
        {},
    )

    logs = evidence.get(
        "logs",
        "",
    )

    # Additional evidence is where the deeper Kubernetes
    # evidence is currently stored.
    additional = evidence.get(
        "additional_evidence",
        {},
    )

    if not isinstance(additional, dict):
        additional = {}

    # First check top-level fields.
    # If they are not present, use additional_evidence.
    previous_logs = evidence.get(
        "previous_logs",
        additional.get(
            "previous_logs",
            {},
        ),
    )

    events = evidence.get(
        "events",
        additional.get(
            "events",
            [],
        ),
    )

    pod_name = evidence.get(
        "pod_name",
        pod.get("name"),
    )

    namespace = evidence.get(
        "namespace",
        pod.get("namespace"),
    )

    status = pod.get(
        "status"
    )

    node = pod.get(
        "node"
    )

    container_statuses = pod.get(
        "container_statuses",
        [],
    )

    containers = pod.get(
        "containers",
        [],
    )

    observations: list[str] = []

    # ==================================================
    # POD STATUS
    # ==================================================

    if status == "Running":
        observations.append(
            "Pod is currently running."
        )
    else:
        observations.append(
            f"Pod is not in a running state. Current status: {status}."
        )

    # ==================================================
    # NODE
    # ==================================================

    if node:
        observations.append(
            f"Pod is scheduled on node: {node}."
        )
    else:
        observations.append(
            "Pod is not currently associated with a node."
        )

    # ==================================================
    # CONTAINERS
    # ==================================================

    if containers:
        observations.append(
            f"Pod contains {len(containers)} container(s)."
        )
    else:
        observations.append(
            "No container definitions were reported."
        )

    # ==================================================
    # CONTAINER STATE
    # ==================================================

    total_restarts = 0
    not_ready_containers = 0
    waiting_containers = 0
    terminated_containers = 0

    for container_status in container_statuses:

        restart_count = container_status.get(
            "restart_count",
            0,
        )

        total_restarts += int(
            restart_count or 0
        )

        # ----------------------------------------------
        # Readiness
        # ----------------------------------------------

        if not container_status.get(
            "ready",
            False,
        ):
            not_ready_containers += 1

        # ----------------------------------------------
        # Current state
        # ----------------------------------------------

        state = container_status.get(
            "state",
            {},
        ) or {}

        if state.get("waiting"):
            waiting_containers += 1

        if state.get("terminated"):
            terminated_containers += 1

        # ----------------------------------------------
        # Previous / last state
        # ----------------------------------------------

        last_state = container_status.get(
            "last_state",
            {},
        ) or {}

        previous_termination = last_state.get(
            "terminated"
        )

        if previous_termination:

            exit_code = previous_termination.get(
                "exit_code"
            )

            reason = previous_termination.get(
                "reason"
            )

            finished_at = previous_termination.get(
                "finished_at"
            )

            observations.append(
                "A previous container termination was recorded."
            )

            if exit_code is not None:
                observations.append(
                    f"Previous container exit code: {exit_code}."
                )

            if reason:
                observations.append(
                    f"Previous container termination reason: {reason}."
                )

            if finished_at:
                observations.append(
                    f"Previous container termination time: {finished_at}."
                )

    # ==================================================
    # RESTART COUNT
    # ==================================================

    if total_restarts:
        observations.append(
            f"Containers have restarted {total_restarts} time(s)."
        )
    else:
        observations.append(
            "No container restarts were recorded."
        )

    # ==================================================
    # READINESS
    # ==================================================

    if not_ready_containers:
        observations.append(
            f"{not_ready_containers} container(s) are not ready."
        )
    else:
        observations.append(
            "All reported containers are ready."
        )

    # ==================================================
    # WAITING STATE
    # ==================================================

    if waiting_containers:
        observations.append(
            f"{waiting_containers} container(s) have a waiting state."
        )

    # ==================================================
    # TERMINATED STATE
    # ==================================================

    if terminated_containers:
        observations.append(
            f"{terminated_containers} container(s) have a terminated state."
        )

    # ==================================================
    # CURRENT LOGS
    # ==================================================

    if logs.strip():
        observations.append(
            "Current pod logs were successfully collected."
        )
    else:
        observations.append(
            "No current pod logs were available."
        )

    # ==================================================
    # PREVIOUS LOGS
    # ==================================================

    previous_logs_available = False

    if isinstance(previous_logs, dict):

        for container_name, previous_log in previous_logs.items():

            if previous_log:

                previous_log_text = str(
                    previous_log
                ).strip()

                if previous_log_text:
                    previous_logs_available = True

                    observations.append(
                        f"Previous logs were collected for container "
                        f"'{container_name}'."
                    )

    elif previous_logs:

        previous_logs_available = True

        observations.append(
            "Previous container logs were collected."
        )

    if not previous_logs_available:
        observations.append(
            "No previous container logs were available."
        )

    # ==================================================
    # KUBERNETES EVENTS
    # ==================================================

    if events:

        observations.append(
            f"{len(events)} Kubernetes event(s) were collected."
        )

        for event in events:

            reason = event.get(
                "reason"
            )

            message = event.get(
                "message"
            )

            event_time = (
                event.get("last_timestamp")
                or event.get("first_timestamp")
            )

            if reason and message:

                if event_time:

                    observations.append(
                        f"Kubernetes event: {reason} - {message} "
                        f"(time: {event_time})."
                    )

                else:

                    observations.append(
                        f"Kubernetes event: {reason} - {message}."
                    )

            elif reason:

                observations.append(
                    f"Kubernetes event reason: {reason}."
                )

    else:

        observations.append(
            "No Kubernetes events were available."
        )

    # ==================================================
    # RETURN RESULT
    # ==================================================

    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "status": status,
        "observations": observations,

        "logs_available": bool(
            logs.strip()
        ),

        "previous_logs_available": previous_logs_available,

        "events_available": bool(
            events
        ),

        "additional_evidence_available": bool(
            additional
        ),

        "evidence_complete": bool(
            pod and logs.strip()
        ),
    }    # CONTAINER STATE
    # ==================================================

    total_restarts = 0
    not_ready_containers = 0
    waiting_containers = 0
    terminated_containers = 0

    for container_status in container_statuses:

        restart_count = container_status.get(
            "restart_count",
            0,
        )

        total_restarts += int(
            restart_count or 0
        )

        # ----------------------------------------------
        # Readiness
        # ----------------------------------------------

        if not container_status.get(
            "ready",
            False,
        ):
            not_ready_containers += 1

        # ----------------------------------------------
        # Current state
        # ----------------------------------------------

        state = container_status.get(
            "state",
            {},
        ) or {}

        if state.get("waiting"):
            waiting_containers += 1

        if state.get("terminated"):
            terminated_containers += 1

        # ----------------------------------------------
        # Previous / last state
        # ----------------------------------------------

        last_state = container_status.get(
            "last_state",
            {},
        ) or {}

        previous_termination = last_state.get(
            "terminated"
        )

        if previous_termination:
            exit_code = previous_termination.get(
                "exit_code"
            )

            reason = previous_termination.get(
                "reason"
            )

            finished_at = previous_termination.get(
                "finished_at"
            )

            observations.append(
                "A previous container termination was recorded."
            )

            if exit_code is not None:
                observations.append(
                    f"Previous container exit code: {exit_code}."
                )

            if reason:
                observations.append(
                    f"Previous container termination reason: {reason}."
                )

            if finished_at:
                observations.append(
                    f"Previous container termination time: {finished_at}."
                )

    # ==================================================
    # RESTART COUNT
    # ==================================================

    if total_restarts:
        observations.append(
            f"Containers have restarted {total_restarts} time(s)."
        )
    else:
        observations.append(
            "No container restarts were recorded."
        )

    # ==================================================
    # READINESS
    # ==================================================

    if not_ready_containers:
        observations.append(
            f"{not_ready_containers} container(s) are not ready."
        )
    else:
        observations.append(
            "All reported containers are ready."
        )

    # ==================================================
    # WAITING STATE
    # ==================================================

    if waiting_containers:
        observations.append(
            f"{waiting_containers} container(s) have a waiting state."
        )

    # ==================================================
    # TERMINATED STATE
    # ==================================================

    if terminated_containers:
        observations.append(
            f"{terminated_containers} container(s) have a terminated state."
        )

    # ==================================================
    # CURRENT LOGS
    # ==================================================

    if logs.strip():
        observations.append(
            "Current pod logs were successfully collected."
        )
    else:
        observations.append(
            "No current pod logs were available."
        )

    # ==================================================
    # PREVIOUS LOGS
    # ==================================================

    previous_logs_available = False

    if isinstance(previous_logs, dict):

        for container_name, previous_log in previous_logs.items():

            if previous_log:

                previous_log_text = str(
                    previous_log
                ).strip()

                if previous_log_text:
                    previous_logs_available = True

                    observations.append(
                        f"Previous logs were collected for container '{container_name}'."
                    )

    elif previous_logs:

        previous_logs_available = True

        observations.append(
            "Previous container logs were collected."
        )

    if not previous_logs_available:
        observations.append(
            "No previous container logs were available."
        )

    # ==================================================
    # KUBERNETES EVENTS
    # ==================================================

    if events:

        observations.append(
            f"{len(events)} Kubernetes event(s) were collected."
        )

        for event in events:

            reason = event.get(
                "reason"
            )

            message = event.get(
                "message"
            )

            event_time = (
                event.get("last_timestamp")
                or event.get("first_timestamp")
            )

            if reason and message:

                if event_time:

                    observations.append(
                        f"Kubernetes event: {reason} - {message} "
                        f"(time: {event_time})."
                    )

                else:

                    observations.append(
                        f"Kubernetes event: {reason} - {message}."
                    )

            elif reason:

                observations.append(
                    f"Kubernetes event reason: {reason}."
                )

    else:

        observations.append(
            "No Kubernetes events were available."
        )

    # ==================================================
    # RETURN INVESTIGATION RESULT
    # ==================================================

    return {
        "pod_name": pod_name,
        "namespace": namespace,
        "status": status,
        "observations": observations,

        "logs_available": bool(
            logs.strip()
        ),

        "previous_logs_available": previous_logs_available,

        "events_available": bool(
            events
        ),

        "additional_evidence_available": bool(
            evidence.get(
                "additional_evidence",
                False,
            )
        ),

        "evidence_complete": bool(
            pod and logs.strip()
        ),
    }