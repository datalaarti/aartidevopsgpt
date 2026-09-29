from tools.docker_tools import get_container_evidence

CONTAINER_ID = "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"

evidence = get_container_evidence(CONTAINER_ID)

print("=== CONTAINER EVIDENCE ===")
for key, value in evidence["container"].items():
    print(f"{key}: {value}")

print("\n=== CONTAINER LOGS ===")
print(evidence["logs"])