from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from rag.embeddings import (
    embed_text,
    embedding_dimension,
)


QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "devopsgpt_knowledge"

client = QdrantClient(
    url=QDRANT_URL
)


def ensure_collection() -> None:
    collections = (
        client.get_collections()
        .collections
    )

    exists = any(
        collection.name == COLLECTION_NAME
        for collection in collections
    )

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=embedding_dimension(),
                distance=Distance.COSINE,
            ),
        )


def add_document(
    document_id: int,
    text: str,
    metadata: dict,
) -> None:
    ensure_collection()

    vector = embed_text(text)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=document_id,
                vector=vector,
                payload={
                    "text": text,
                    **metadata,
                },
            )
        ],
    )


def search_knowledge(
    query: str,
    limit: int = 5,
    domain: str | None = None,
) -> list[dict]:
    """
    Search the knowledge base.

    When domain is supplied, only knowledge documents
    belonging to that domain are returned.
    """

    ensure_collection()

    query_vector = embed_text(query)

    query_filter = None

    if domain:
        query_filter = Filter(
            must=[
                FieldCondition(
                    key="domain",
                    match=MatchValue(
                        value=domain
                    ),
                )
            ]
        )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    ).points

    return [
        {
            "score": result.score,
            "text": result.payload.get(
                "text",
                "",
            ),
            "metadata": {
                key: value
                for key, value in result.payload.items()
                if key != "text"
            },
        }
        for result in results
    ]