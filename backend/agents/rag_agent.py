from typing import Any

from rag.qdrant_service import search_knowledge


def retrieve_knowledge(
    domain: str,
    root_cause: dict[str, Any],
    limit: int = 3,
) -> dict[str, Any]:
    """
    Retrieve relevant knowledge from Qdrant using
    the current root-cause analysis.
    """

    root_cause_text = root_cause.get(
        "root_cause",
        "",
    )

    reasoning = root_cause.get(
        "reasoning",
        [],
    )

    query_parts = [
        domain,
        root_cause_text,
        *reasoning,
    ]

    query = " ".join(
        str(part)
        for part in query_parts
        if part
    ).strip()

    if not query:
        return {
            "query": "",
            "retrieval_used": False,
            "documents": [],
            "message": "No meaningful query was generated.",
        }

    try:
        documents = search_knowledge(
            query=query,
            limit=limit,
        )

        return {
            "query": query,
            "retrieval_used": bool(documents),
            "documents": documents,
            "message": (
                f"Retrieved {len(documents)} relevant "
                "knowledge document(s)."
                if documents
                else "No relevant knowledge documents found."
            ),
        }

    except Exception as exc:
        return {
            "query": query,
            "retrieval_used": False,
            "documents": [],
            "message": f"Knowledge retrieval failed: {exc}",
        }