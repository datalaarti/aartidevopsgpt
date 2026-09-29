import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Add it to backend/.env"
    )

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAMES = [
    "gemini-2.5-flash",
    "gemini-3.5-flash-lite",
]


def _run_with_retry(call):
    """
    Execute a Gemini request with retries for temporary 503 errors.
    """
    last_error = None

    for attempt in range(3):
        try:
            response = call()
            return response

        except errors.ServerError as exc:
            last_error = exc

            if getattr(exc, "status_code", None) == 503:
                time.sleep(2 ** attempt)
                continue

            raise

    raise RuntimeError(
        f"Gemini unavailable after retries: {last_error}"
    )


def generate_response(prompt: str) -> str:
    """
    Generate normal text from Gemini.
    """
    last_error = None

    for model_name in MODEL_NAMES:
        try:
            response = _run_with_retry(
                lambda: client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"All Gemini models failed: {last_error}"
    )


def generate_json_response(
    prompt: str,
    response_schema: dict,
) -> str:
    """
    Generate schema-constrained JSON from Gemini.
    """

    last_error = None

    for model_name in MODEL_NAMES:
        try:
            response = _run_with_retry(
                lambda: client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=response_schema,
                    ),
                )
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            return response.text

        except Exception as exc:
            last_error = exc

    raise RuntimeError(
        f"All Gemini models failed: {last_error}"
    )