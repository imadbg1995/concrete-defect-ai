import asyncio
import base64
import re

import anthropic

from app.config import settings

_client: anthropic.AsyncAnthropic | None = None

# 529 = overloaded; 529/500/503 are all transient — retry up to 4 times
_RETRYABLE_STATUS = {429, 500, 503, 529}
_MAX_RETRIES = 4
_BASE_DELAY = 5  # seconds


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def call_claude(
    image_bytes: bytes,
    image_mime: str,
    prompt: str,
    max_tokens: int = 8192,
    model: str | None = None,
) -> str:
    client = get_client()
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            message = await client.messages.create(
                model=model or settings.claude_model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": image_mime,
                                    "data": b64,
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )
            return message.content[0].text

        except anthropic.APIStatusError as exc:
            last_exc = exc
            if exc.status_code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                delay = _BASE_DELAY * (2 ** attempt)  # 5s, 10s, 20s
                await asyncio.sleep(delay)
                continue
            raise

        except anthropic.APIConnectionError as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(_BASE_DELAY * (2 ** attempt))
                continue
            raise

    raise last_exc


def strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    brace = text.find("{")
    if brace > 0:
        text = text[brace:]
    return text.strip()
