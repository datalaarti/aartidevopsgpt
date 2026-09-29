from tools.docker_tools import (
    get_container_evidence,
    get_additional_container_evidence,
)

from agents.investigation_agent import investigate_docker_evidence
from agents.root_cause_agent import analyze_root_cause
from agents.rag_agent import retrieve_knowledge
from agents.solution_agent import generate_solution


CONTAINER_ID = (
    "16cbe07bcdc9a771751b2b4057059707b4256aae83b3fd93b8c0eb8af037a49f"
)


# ---------------------------------------------------------
# 1. Collect initial Docker evidence
# ---------------------------------------------------------

initial_evidence = get_container_evidence(
    CONTAINER_ID
)


# ---------------------------------------------------------
# 2. Collect additional Docker evidence
# ---------------------------------------------------------

additional_evidence = get_additional_container_evidence(
    CONTAINER_ID
)


evidence = {
    **initial_evidence,
    "additional_evidence": additional_evidence,
}


# ---------------------------------------------------------
# 3. Investigation
# ---------------------------------------------------------

investigation = investigate_docker_evidence(
    evidence
)


# ---------------------------------------------------------
# 4. Root Cause using Gemini
# ---------------------------------------------------------

root_cause = analyze_root_cause(
    investigation=investigation,
    evidence=evidence,
)


# ---------------------------------------------------------
# 5. RAG
# ---------------------------------------------------------

rag_result = retrieve_knowledge(
    domain="docker",
    root_cause=root_cause,
)


# ---------------------------------------------------------
# 6. Solution using Gemini
# ---------------------------------------------------------

solution = generate_solution(
    root_cause=root_cause,
    rag_result=rag_result,
    evidence=evidence,
    investigation=investigation,
)


# ---------------------------------------------------------
# 7. Print results
# ---------------------------------------------------------

print("\n=== INVESTIGATION ===")
print(investigation)

print("\n=== ROOT CAUSE ===")
print(root_cause)

print("\n=== RAG ===")
print(rag_result)

print("\n=== GEMINI SOLUTION ===")
print(solution)