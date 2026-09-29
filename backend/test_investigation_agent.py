from tools.docker_tools import get_container_evidence
from agents.investigation_agent import investigate_docker_evidence


CONTAINER_ID = "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"

evidence = get_container_evidence(CONTAINER_ID)

investigation = investigate_docker_evidence(evidence)

print("=== INVESTIGATION RESULT ===")

for key, value in investigation.items():
    print(f"{key}: {value}")