from typing import Any
import json

from llm.gemini_client import generate_json_response


ROOT_CAUSE_SCHEMA = {
    "type": "object",
    "properties": {
        "root_cause": {
            "type": "string",
        },
        "confidence": {
            "type": "string",
            "enum": ["high", "medium", "low"],
        },
        "reasoning": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "requires_more_investigation": {
            "type": "boolean",
        },
    },
    "required": [
        "root_cause",
        "confidence",
        "reasoning",
        "requires_more_investigation",
    ],
}


def analyze_root_cause(
    investigation: dict[str, Any],
    evidence: dict[str, Any],
    rag_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Determine the root cause using:
    - real infrastructure evidence
    - investigation observations
    - retrieved RAG knowledge
    """

    rag_result = rag_result or {}

    prompt = f"""
You are the Root Cause Agent in DevOpsGPT.

Determine the most likely root cause using ONLY the supplied evidence.

Rules:
- Never invent facts.
- Do not confuse correlation with proof.
- If evidence is insufficient, explicitly say so.
- Do not propose remediation.
- Do not claim a specific root cause unless the evidence supports it.
- Return the requested structured fields.

INVESTIGATION:
{json.dumps(investigation, indent=2)}

INFRASTRUCTURE EVIDENCE:
{json.dumps(evidence, indent=2)}

RETRIEVED KNOWLEDGE:
{json.dumps(rag_result, indent=2)}
"""

    response = generate_json_response(
        prompt=prompt,
        response_schema=ROOT_CAUSE_SCHEMA,
    )

    result = json.loads(response)

    return {
        "root_cause": result["root_cause"],
        "confidence": result["confidence"],
        "reasoning": result["reasoning"],
        "requires_more_investigation": result[
            "requires_more_investigation"
        ],
    }