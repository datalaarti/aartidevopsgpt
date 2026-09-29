from agents.graph import build_graph


CONTAINER_ID = (
    "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"
)

graph = build_graph()

result = graph.invoke(
    {
        "domain": "docker",
        "resource_id": CONTAINER_ID,
    }
)

print("\n=== FINAL DEVOPSGPT RESULT ===\n")

print("Initial Evidence:")
print(result["evidence"])

print("\nAdditional Evidence:")
print(result.get("additional_evidence"))

print("\nInvestigation:")
print(result["investigation"])

print("\nRoot Cause:")
print(result["root_cause"])

print("\nRAG:")
print(result["rag_result"])

print("\nSolution:")
print(result["solution"])

print("\nVerification:")
print(result["verification"])