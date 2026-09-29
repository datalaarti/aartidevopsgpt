from tools.docker_tools import get_container_evidence
from agents.investigation_agent import investigate_docker_evidence
from agents.root_cause_agent import analyze_root_cause
from agents.rag_agent import retrieve_knowledge
from agents.solution_agent import generate_solution
from agents.verification_agent import verify_solution


CONTAINER_ID = (
    "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"
)

evidence = get_container_evidence(CONTAINER_ID)

investigation = investigate_docker_evidence(evidence)

root_cause = analyze_root_cause(
    investigation,
    evidence,
)

rag_result = retrieve_knowledge(
    domain="docker",
    root_cause=root_cause,
)

solution = generate_solution(
    root_cause=root_cause,
    rag_result=rag_result,
)

verification = verify_solution(
    root_cause=root_cause,
    solution=solution,
    rag_result=rag_result,
)

print("=== VERIFICATION RESULT ===")

for key, value in verification.items():
    print(f"{key}: {value}")