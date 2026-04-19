"""Gemini service — image generation for defect overlay + text for analysis."""

import re

from google import genai
from google.genai import types

from app.config import settings

OVERLAY_PROMPT = (
    "You are a professional computer-vision crack segmentation system for concrete inspection. "
    "Paint a color-coded defect overlay on this concrete image following these strict rules.\n\n"

    "═══ WHAT IS A CRACK (annotate these) ═══\n"
    "A crack is a LINEAR DISCONTINUITY in the concrete surface — a physical gap, fissure, "
    "or split. It must show actual separation (shadow, dark thin line, depth) — NOT just "
    "a darker color or stain. Cracks usually have sharp edges and follow stress patterns "
    "(branching, forking, map-like networks).\n\n"

    "═══ WHAT IS NOT A CRACK (DO NOT annotate these) ═══\n"
    "✗ Water streaks, moisture runs, rain marks\n"
    "✗ White/gray EFFLORESCENCE (mineral deposits, salt leaching, calcium bloom)\n"
    "✗ Dirt, rust stains, biological growth (moss, mold)\n"
    "✗ Shadows cast by objects, people, edges of the structure\n"
    "✗ Joints between different materials (wall-to-roof, wall-to-ground)\n"
    "✗ Color variations, paint marks, chalk lines, existing annotations/labels\n"
    "✗ Formwork marks, tie-rod holes, weep holes (unless cracked around them)\n"
    "✗ Background: sky, road, vehicles, people, vegetation\n\n"

    "═══ COLOR CODE BY CRACK WIDTH ═══\n"
    "1) HAIRLINE / FINE (< 0.5 mm, barely visible thin line):\n"
    "   → Bright CYAN (#00E5FF), stroke 1-2 px\n"
    "2) MEDIUM (0.5 – 2 mm, clearly visible):\n"
    "   → Bright YELLOW (#FFE000), stroke 2-3 px\n"
    "3) WIDE (> 2 mm, clearly open gap):\n"
    "   → Bright ORANGE (#FF6200), stroke 3-5 px\n\n"

    "IMPORTANT: In a real crack network, widths VARY along the path. "
    "Use all three colors where appropriate — do not default everything to one color. "
    "Thicker trunk cracks are often ORANGE while their branches taper to YELLOW then CYAN.\n\n"

    "═══ SPALLED / DETERIORATED ZONES ═══\n"
    "Fill with MAGENTA (#FF00AA) at 80-90% opacity ONLY where concrete has physically "
    "BROKEN AWAY, leaving a visible depression, missing material, or exposed aggregate/rebar. "
    "Requirements for magenta fills:\n"
    "• Must follow the ORGANIC, IRREGULAR boundary of the actual damaged area\n"
    "• Must NOT be rectangular, boxy, or geometric\n"
    "• Must be TIGHT around real damage — no padding or over-expansion\n"
    "• Do NOT fill areas that are merely discolored, wet, stained, or shadowed\n"
    "• Do NOT fill an entire quadrant of the image — real spalls are localized patches\n\n"

    "═══ TRACING RULES ═══\n"
    "• Follow every real crack along its exact curved path, including all branches and forks\n"
    "• Preserve the fine network — do not simplify a spider-web pattern into a few lines\n"
    "• Keep the original concrete surface fully visible between overlays\n"
    "• No text, labels, legends, arrows, or numbers — overlay only\n"
    "• Style: clean, precise, scientific segmentation map"
)


def _make_client() -> genai.Client:
    return genai.Client(api_key=settings.gemini_api_key)


async def generate_annotated_image(image_bytes: bytes, mime: str, prompt: str | None = None) -> bytes:
    """Ask Gemini to paint defect overlay onto the image."""
    client = _make_client()

    response = await client.aio.models.generate_content(
        model=settings.gemini_image_model,
        contents=[
            types.Content(parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime),
                types.Part.from_text(text=prompt or OVERLAY_PROMPT),
            ])
        ],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            return part.inline_data.data

    raise ValueError("Gemini returned no image in the response.")


async def call_gemini_text(image_bytes: bytes, mime: str, prompt: str, max_tokens: int = 4096) -> str:
    """Vision-only call — returns text."""
    client = _make_client()

    response = await client.aio.models.generate_content(
        model=settings.gemini_model,
        contents=[
            types.Content(parts=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime),
                types.Part.from_text(text=prompt),
            ])
        ],
        config=types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.1,
        ),
    )
    return response.text


def strip_json_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    brace = text.find("{")
    if brace > 0:
        text = text[brace:]
    return text.strip()
