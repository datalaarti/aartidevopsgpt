from typing import Any
import json

from llm.gemini_client import generate_json_response


SOLUTION_SCHEMA = {
    "type": "object",
    "properties": {
        "solution": {
            "type": "string",
        },
        "actions": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "execution_action": {
            "type": "string",
            "enum": [
                "restart_container",
                "none",
            ],
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "risk": {
            "type": "string",
            "enum": ["low", "medium", "high"],
        },
        "safe_to_execute": {
            "type": "boolean",
        },
        "reason": {
            "type": "string",
        },
    },
    "required": [
        "solution",
        "actions",
        "execution_action",
        "confidence",
        "risk",
        "safe_to_execute",
        "reason",
    ],
}


def generate_solution(
    root_cause: dict[str, Any],
    rag_result: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    investigation: dict[str, Any] | None = None,
) -> dict[str, Any]:

    evidence = evidence or {}
    investigation = investigation or {}

    requires_more_investigation = root_cause.get(
        "requires_more_investigation",
        True,
    )

    container_status = str(
        investigation.get(
            "status",
            "",
        )
    ).lower()

    prompt = f"""
You are the Solution Agent in DevOpsGPT.

Your job is to propose the safest evidence-based next step.

IMPORTANT SAFETY RULES:

1. Use only the supplied evidence and retrieved knowledge.
2. Never invent facts.
3. If requires_more_investigation is true, ONLY propose diagnostic
   or information-gathering actions.
4. If requires_more_investigation is true,
   safe_to_execute MUST be false.
5. Do not recommend destructive or irreversible actions.
6. Do not claim that any action has already been executed.
7. Human approval is required before any remediation.
8. Only choose execution_action = "restart_container"
   when restarting the existing Docker container is actually
   an appropriate remediation supported by the evidence.
9. If the problem requires changing application code,
   changing configuration, rebuilding an image, or changing
   the container command, choose execution_action = "none".
10. If execution_action = "none", safe_to_execute MUST be false.
11. If the container is already running normally and there is
    no active failure, execution_action MUST be "none".
12. Return only the requested structured fields.

ROOT CAUSE:
{json.dumps(root_cause, indent=2)}

INVESTIGATION:
{json.dumps(investigation, indent=2)}

INFRASTRUCTURE EVIDENCE:
{json.dumps(evidence, indent=2)}

RETRIEVED KNOWLEDGE:
{json.dumps(rag_result, indent=2)}

CURRENT CONTAINER STATUS:
{container_status}

CURRENT INVESTIGATION STATUS:
requires_more_investigation = {requires_more_investigation}
"""

    response = generate_json_response(
        prompt=prompt,
        response_schema=SOLUTION_SCHEMA,
    )

    result = json.loads(response)

    execution_action = result.get(
        "execution_action",
        "none",
    )

    safe_to_execute = bool(
        result.get(
            "safe_to_execute",
            False,
        )
    )

    # ---------------------------------------------------------
    # Server-side safety enforcement.
    #
    # The LLM does NOT get final authority over execution.
    # ---------------------------------------------------------

    if requires_more_investigation:
        safe_to_execute = False

    # Only currently supported executable action.
    if execution_action != "restart_container":
        safe_to_execute = False

    # Restart is meaningful only for a stopped/exited container.
    if container_status == "running":
        safe_to_execute = False
        execution_action = "none"

    # If the LLM proposes configuration/code/image changes,
    # we cannot execute those with the current Docker tools.
    if execution_action == "none":
        safe_to_execute = False

    return {
        "solution": result.get(
            "solution",
            "No solution generated.",
        ),
        "actions": result.get(
            "actions",
            [],
        ),
        "execution_action": execution_action,
        "confidence": result.get(
            "confidence",
            "low",
        ),
        "risk": result.get(
            "risk",
            "high",
        ),
        "safe_to_execute": safe_to_execute,
        "reason": result.get(
            "reason",
            "",
        ),
    }