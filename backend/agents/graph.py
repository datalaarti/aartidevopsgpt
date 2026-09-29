from typing import Any, TypedDict

from langgraph.graph import StateGraph, START, END

from tools.docker_tools import (
    get_container_evidence,
    get_additional_container_evidence,
)

from tools.kubernetes_tools import (
    get_pod_evidence,
    get_additional_pod_evidence,
)

from agents.investigation_agent import (
    investigate_docker_evidence,
    investigate_kubernetes_evidence,
)

from agents.root_cause_agent import analyze_root_cause
from agents.rag_agent import retrieve_knowledge
from agents.solution_agent import generate_solution
from agents.verification_agent import verify_solution


class DevOpsState(TypedDict, total=False):
    domain: str
    resource_id: str

    evidence: dict[str, Any]
    additional_evidence: dict[str, Any]

    investigation: dict[str, Any]
    root_cause: dict[str, Any]
    rag_result: dict[str, Any]
    solution: dict[str, Any]
    verification: dict[str, Any]


# --------------------------------------------------
# Initial Evidence Collection
# --------------------------------------------------

def collect_evidence(
    state: DevOpsState,
) -> DevOpsState:
    """
    Collect initial read-only evidence from the
    selected DevOps domain.
    """

    domain = state["domain"]
    resource_id = state["resource_id"]

    if domain == "docker":
        evidence = get_container_evidence(
            resource_id
        )

    elif domain == "kubernetes":
        evidence = get_pod_evidence(
            resource_id
        )

    else:
        raise ValueError(
            f"Unsupported domain: {domain}"
        )

    return {
        **state,
        "evidence": evidence,
    }


# --------------------------------------------------
# Additional Evidence Collection
# --------------------------------------------------

def collect_additional_evidence(
    state: DevOpsState,
) -> DevOpsState:
    """
    Collect deeper read-only evidence when the
    initial investigation is insufficient.
    """

    domain = state["domain"]
    resource_id = state["resource_id"]

    if domain == "docker":
        additional = get_additional_container_evidence(
            resource_id
        )

    elif domain == "kubernetes":
        additional = get_additional_pod_evidence(
            resource_id
        )

    else:
        raise ValueError(
            "Additional evidence is not implemented "
            f"for domain: {domain}"
        )

    return {
        **state,
        "additional_evidence": additional,
    }


# --------------------------------------------------
# Investigation
# --------------------------------------------------

def investigation_node(
    state: DevOpsState,
) -> DevOpsState:
    """
    Use the common Investigation stage with the
    correct domain-specific evidence adapter.
    """

    combined_evidence = {
        **state["evidence"],
        "additional_evidence": state.get(
            "additional_evidence",
            {},
        ),
    }

    domain = state["domain"]

    if domain == "docker":
        result = investigate_docker_evidence(
            combined_evidence
        )

    elif domain == "kubernetes":
        result = investigate_kubernetes_evidence(
            combined_evidence
        )

    else:
        raise ValueError(
            f"Unsupported domain: {domain}"
        )

    return {
        **state,
        "investigation": result,
    }


# --------------------------------------------------
# Root Cause
# --------------------------------------------------

def root_cause_node(
    state: DevOpsState,
) -> DevOpsState:
    """
    Determine the likely root cause using all
    available evidence.
    """

    combined_evidence = {
        **state["evidence"],
        "additional_evidence": state.get(
            "additional_evidence",
            {},
        ),
    }

    result = analyze_root_cause(
        state["investigation"],
        combined_evidence,
    )

    return {
        **state,
        "root_cause": result,
    }


# --------------------------------------------------
# Agentic Decision
# --------------------------------------------------

def route_after_root_cause(
    state: DevOpsState,
) -> str:
    """
    Decide whether deeper evidence is needed.
    """

    root_cause = state.get(
        "root_cause",
        {},
    )

    requires_more = root_cause.get(
        "requires_more_investigation",
        False,
    )

    already_collected = bool(
        state.get("additional_evidence")
    )

    if requires_more and not already_collected:
        return "additional_evidence"

    return "rag"


# --------------------------------------------------
# RAG
# --------------------------------------------------

def rag_node(
    state: DevOpsState,
) -> DevOpsState:

    result = retrieve_knowledge(
        domain=state["domain"],
        root_cause=state["root_cause"],
    )

    return {
        **state,
        "rag_result": result,
    }


# --------------------------------------------------
# Solution
# --------------------------------------------------

def solution_node(
    state: DevOpsState,
) -> DevOpsState:

    result = generate_solution(
        root_cause=state["root_cause"],
        rag_result=state["rag_result"],
        evidence={
            **state["evidence"],
            "additional_evidence": state.get(
                "additional_evidence",
                {},
            ),
        },
        investigation=state["investigation"],
    )

    return {
        **state,
        "solution": result,
    }


# --------------------------------------------------
# Verification
# --------------------------------------------------

def verification_node(
    state: DevOpsState,
) -> DevOpsState:

    combined_evidence = {
        **state["evidence"],
        "additional_evidence": state.get(
            "additional_evidence",
            {},
        ),
    }

    result = verify_solution(
        root_cause=state["root_cause"],
        solution=state["solution"],
        rag_result=state["rag_result"],
        evidence=combined_evidence,
        investigation=state["investigation"],
    )

    return {
        **state,
        "verification": result,
    }


# --------------------------------------------------
# Build Graph
# --------------------------------------------------

def build_graph():

    graph = StateGraph(
        DevOpsState
    )

    # Nodes
    graph.add_node(
        "collect_evidence",
        collect_evidence,
    )

    graph.add_node(
        "investigation",
        investigation_node,
    )

    graph.add_node(
        "root_cause",
        root_cause_node,
    )

    graph.add_node(
        "additional_evidence",
        collect_additional_evidence,
    )

    graph.add_node(
        "rag",
        rag_node,
    )

    graph.add_node(
        "solution",
        solution_node,
    )

    graph.add_node(
        "verification",
        verification_node,
    )

    # --------------------------------------------------
    # Initial Flow
    # --------------------------------------------------

    graph.add_edge(
        START,
        "collect_evidence",
    )

    graph.add_edge(
        "collect_evidence",
        "investigation",
    )

    graph.add_edge(
        "investigation",
        "root_cause",
    )

    # --------------------------------------------------
    # Agentic Decision
    # --------------------------------------------------

    graph.add_conditional_edges(
        "root_cause",
        route_after_root_cause,
        {
            "additional_evidence": "additional_evidence",
            "rag": "rag",
        },
    )

    # After deeper evidence,
    # return to common Investigation.
    graph.add_edge(
        "additional_evidence",
        "investigation",
    )

    # --------------------------------------------------
    # Common AI Pipeline
    # --------------------------------------------------

    graph.add_edge(
        "rag",
        "solution",
    )

    graph.add_edge(
        "solution",
        "verification",
    )

    graph.add_edge(
        "verification",
        END,
    )

    return graph.compile()