from rag.qdrant_service import add_document


KUBERNETES_DOCUMENTS = [
    {
        "id": 101,
        "text": """
Kubernetes pod troubleshooting should begin by inspecting
pod status, container readiness, restart counts, container
states, recent logs, previous container logs when available,
and Kubernetes events. If the current evidence does not
explain a restart or failure, collect additional evidence
instead of inventing a root cause.
""",
        "metadata": {
            "domain": "kubernetes",
            "topic": "pod_troubleshooting",
        },
    },
    {
        "id": 102,
        "text": """
A Kubernetes container restart count indicates that a
container has restarted during the lifetime of the pod.
The restart count alone does not identify the cause.
Inspect the current container state, last terminated state,
exit code, termination reason, previous logs, and pod events
to determine why the earlier instance stopped.
""",
        "metadata": {
            "domain": "kubernetes",
            "topic": "container_restarts",
        },
    },
    {
        "id": 103,
        "text": """
When the current Kubernetes container logs only show a
successful startup but the restart count is greater than
zero, retrieve logs from the previous container instance
when available and inspect Kubernetes pod events. Historical
evidence is required to determine the reason for the
previous termination.
""",
        "metadata": {
            "domain": "kubernetes",
            "topic": "previous_logs_and_events",
        },
    },
    {
        "id": 104,
        "text": """
Kubernetes readiness and liveness behavior should be
considered when troubleshooting workload health. A readiness
problem can prevent a pod from receiving traffic, while a
liveness failure can cause the kubelet to restart a
container. Probe configuration and related pod events should
be inspected before proposing remediation.
""",
        "metadata": {
            "domain": "kubernetes",
            "topic": "health_probes",
        },
    },
]


def ingest_kubernetes_documents() -> None:
    for document in KUBERNETES_DOCUMENTS:
        add_document(
            document_id=document["id"],
            text=document["text"],
            metadata=document["metadata"],
        )

    print(
        f"Ingested {len(KUBERNETES_DOCUMENTS)} "
        "Kubernetes knowledge documents."
    )


if __name__ == "__main__":
    ingest_kubernetes_documents()