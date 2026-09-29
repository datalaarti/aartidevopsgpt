from rag.qdrant_service import ensure_collection, add_document


DOCUMENTS = [
    {
        "id": 1,
        "text": """
Docker container exit codes indicate how the main process
terminated. A non-zero exit code generally indicates failure,
but the exit code alone is not sufficient to determine the
root cause. Logs and container configuration should also be
inspected.
""",
        "metadata": {
            "domain": "docker",
            "topic": "exit_codes",
        },
    },
    {
        "id": 2,
        "text": """
When a Docker container exits unexpectedly, inspect container
status, logs, exit code, OOM status, restart policy, command,
entrypoint, environment variables, mounts, and networks.
If the evidence is insufficient, collect additional evidence
instead of inventing a root cause.
""",
        "metadata": {
            "domain": "docker",
            "topic": "troubleshooting",
        },
    },
]


def ingest() -> None:
    ensure_collection()

    for document in DOCUMENTS:
        add_document(
            document_id=document["id"],
            text=document["text"],
            metadata=document["metadata"],
        )

    print(
        f"Inserted {len(DOCUMENTS)} documents "
        "into Qdrant."
    )


if __name__ == "__main__":
    ingest()