import base64
import re

import anthropic

from app.config import settings

_client: anthropic.AsyncAnthropic | None = None


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


def strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    brace = text.find("{")
    if brace > 0:
        text = text[brace:]
    return text.strip()
