from tools.docker_tools import (
    get_container_evidence,
    get_additional_container_evidence,
)

from agents.investigation_agent import investigate_docker_evidence
from agents.root_cause_agent import analyze_root_cause
from agents.rag_agent import retrieve_knowledge
from agents.solution_agent import generate_solution
from agents.verification_agent import verify_solution


CONTAINER_ID = (
    "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"
)


# 1. Docker evidence
initial = get_container_evidence(
    CONTAINER_ID
)

additional = get_additional_container_evidence(
    CONTAINER_ID
)

evidence = {
    **initial,
    "additional_evidence": additional,
}


# 2. Investigation
investigation = investigate_docker_evidence(
    evidence
)


# 3. Root cause
root_cause = analyze_root_cause(
    investigation=investigation,
    evidence=evidence,
)


# 4. RAG
rag_result = retrieve_knowledge(
    domain="docker",
    root_cause=root_cause,
)


# 5. Solution
solution = generate_solution(
    root_cause=root_cause,
    rag_result=rag_result,
    evidence=evidence,
    investigation=investigation,
)


# 6. Verification
verification = verify_solution(
    root_cause=root_cause,
    solution=solution,
    rag_result=rag_result,
    evidence=evidence,
    investigation=investigation,
)


print("\n=== ROOT CAUSE ===")
print(root_cause)

print("\n=== RAG ===")
print(rag_result)

print("\n=== SOLUTION ===")
print(solution)

print("\n=== VERIFICATION ===")
print(verification)