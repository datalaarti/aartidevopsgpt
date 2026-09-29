from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """
    Convert text into a dense vector.
    all-MiniLM-L6-v2 produces 384-dimensional embeddings.
    """
    vector = _model.encode(
        text,
        normalize_embeddings=True,
    )

    return vector.tolist()


def embedding_dimension() -> int:
    return _model.get_sentence_embedding_dimension()