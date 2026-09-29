from tools.docker_tools import get_container_evidence
from agents.investigation_agent import investigate_docker_evidence
from agents.root_cause_agent import analyze_root_cause


CONTAINER_ID = (
    "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"
)

evidence = get_container_evidence(CONTAINER_ID)

investigation = investigate_docker_evidence(
    {
        **evidence,
        "additional_evidence": {},
    }
)

result = analyze_root_cause(
    investigation=investigation,
    evidence=evidence,
)

print("=== GEMINI ROOT CAUSE ===")
print(result)