from rag.qdrant_service import search_knowledge


query = """
My Docker container exited unexpectedly with a non-zero
exit code and the logs do not clearly show the cause.
What should I investigate?
"""

results = search_knowledge(query, limit=3)

print("=== QDRANT RESULTS ===")

for result in results:
    print("\nScore:", result["score"])
    print("Metadata:", result["metadata"])
    print("Text:", result["text"])