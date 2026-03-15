import asyncio
import json
from dataclasses import dataclass
from typing import Any
from google import genai
from app.config import get_settings

settings = get_settings()


@dataclass
class GeminiGenerateResult:
    text: str
    prompt_tokens: int
    response_tokens: int


class GeminiClientError(Exception):
    pass


class GeminiClient:
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise GeminiClientError("GEMINI_API_KEY is not configured")
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = settings.GEMINI_MODEL
        self.max_retries = settings.GEMINI_MAX_RETRIES
        self.timeout_seconds = settings.GEMINI_REQUEST_TIMEOUT_SECONDS

    async def generate(self, prompt: str) -> GeminiGenerateResult:
        delay = 0.5
        last_error: Exception | None = None

        for _ in range(self.max_retries):
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.models.generate_content,
                        model=self.model,
                        contents=prompt,
                    ),
                    timeout=self.timeout_seconds,
                )
                text = getattr(response, "text", "") or ""
                usage = getattr(response, "usage_metadata", None)
                prompt_tokens = int(getattr(usage, "prompt_token_count", 0) or 0)
                response_tokens = int(
                    getattr(usage, "candidates_token_count", 0)
                    or getattr(usage, "response_token_count", 0)
                    or 0
                )
                return GeminiGenerateResult(
                    text=text,
                    prompt_tokens=prompt_tokens,
                    response_tokens=response_tokens,
                )
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(delay)
                delay = min(delay * 2, 4.0)

        raise GeminiClientError("Gemini request failed") from last_error

    async def generate_json(self, prompt: str) -> tuple[dict[str, Any], GeminiGenerateResult]:
        result = await self.generate(prompt)
        try:
            parsed = json.loads(result.text)
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a JSON object")
            return parsed, result
        except Exception as exc:
            raise GeminiClientError("Invalid JSON response from Gemini") from exc
