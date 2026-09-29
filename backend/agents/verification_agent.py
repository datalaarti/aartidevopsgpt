from typing import Any
import json

from llm.gemini_client import generate_json_response


VERIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "verified": {
            "type": "boolean",
        },
        "safe_to_execute": {
            "type": "boolean",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "reasons": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "requires_human_approval": {
            "type": "boolean",
        },
    },
    "required": [
        "verified",
        "safe_to_execute",
        "confidence",
        "reasons",
        "requires_human_approval",
    ],
}


def verify_solution(
    root_cause: dict[str, Any],
    solution: dict[str, Any],
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

    prompt = f"""
You are the Verification Agent in DevOpsGPT.

Your job is to evaluate whether the proposed solution is:
1. Supported by the available evidence.
2. Appropriate for the identified root cause.
3. Safe enough to proceed to human approval.
4. Not claiming that an action has already happened.

IMPORTANT SAFETY RULES:

- Never invent evidence.
- If the root cause still requires more investigation,
  the solution cannot be verified.
- If the solution is not supported by the evidence,
  verification must fail.
- A diagnostic recommendation is not the same as a remediation.
- Do not execute anything.
- Human approval is required before any real remediation.
- Return only structured JSON.

ROOT CAUSE:
{json.dumps(root_cause, indent=2)}

INVESTIGATION:
{json.dumps(investigation, indent=2)}

INFRASTRUCTURE EVIDENCE:
{json.dumps(evidence, indent=2)}

RETRIEVED KNOWLEDGE:
{json.dumps(rag_result, indent=2)}

PROPOSED SOLUTION:
{json.dumps(solution, indent=2)}

CURRENT STATUS:
requires_more_investigation = {requires_more_investigation}
"""

    response = generate_json_response(
        prompt=prompt,
        response_schema=VERIFICATION_SCHEMA,
    )

    result = json.loads(response)

    verified = bool(
        result.get("verified", False)
    )

    safe_to_execute = bool(
        result.get("safe_to_execute", False)
    )

    reasons = result.get(
        "reasons",
        [],
    )

    confidence = result.get(
        "confidence",
        "low",
    )

    # ---------------------------------------------------------
    # Backend safety enforcement.
    # The LLM never gets final authority to permit execution.
    # ---------------------------------------------------------

    if requires_more_investigation:
        verified = False
        safe_to_execute = False

        reasons.append(
            "Root cause still requires additional investigation."
        )

    if not solution.get(
        "safe_to_execute",
        False,
    ):
        safe_to_execute = False

        reasons.append(
            "The Solution Agent did not mark the proposal "
            "as safe to execute."
        )

    # Human approval is mandatory for any remediation.
    requires_human_approval = True

    return {
        "verified": verified,
        "safe_to_execute": safe_to_execute,
        "confidence": confidence,
        "reasons": reasons,
        "requires_human_approval": requires_human_approval,
    }