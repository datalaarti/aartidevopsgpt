from llm.gemini_client import generate_response


response = generate_response(
    """
You are a DevOps troubleshooting assistant.

Explain in one short paragraph:
Why should a Docker troubleshooting system inspect
container logs instead of relying only on the exit code?
"""
)

print("=== GEMINI RESPONSE ===")
print(response)