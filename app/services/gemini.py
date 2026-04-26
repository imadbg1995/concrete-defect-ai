"""Gemini service — image generation for defect overlay + text for analysis."""

import re

from google import genai
from google.genai import types

from app.config import settings

OVERLAY_PROMPT = (
    "You are a computer vision system specialized in concrete crack detection and structural surface analysis. "
    "Your task is to generate a highly accurate crack detection overlay image from this real concrete photo.\n\n"

    "OBJECTIVE: Produce an overlay that accurately follows real cracks with pixel-level precision, "
    "avoids false detections, and clearly distinguishes crack severity.\n\n"

    "━━━ DETECTION RULES (CRITICAL) ━━━\n"
    "• Detect ONLY real cracks visible in the image — no hallucination\n"
    "• Do NOT generate cracks where none exist\n"
    "• Follow crack paths precisely — no approximation blobs or rough shapes\n"
    "• Avoid over-smoothing or exaggerated line thickness\n"
    "• Respect actual crack geometry including branching, forking, and tapering\n"
    "• Minimum detectable crack: must be clearly visible as a linear separation\n"
    "• When in doubt — do NOT mark it\n\n"

    "━━━ WHAT IS A REAL CRACK ━━━\n"
    "✓ Linear discontinuity with visible depth (shadow or darker interior)\n"
    "✓ Sharp defined edges, not fuzzy or gradient\n"
    "✓ Follows structural stress directions (branching, forking, map networks)\n\n"

    "━━━ NEVER ANNOTATE THESE ━━━\n"
    "✗ Water streaks, moisture runs, damp patches\n"
    "✗ Efflorescence, salt bloom, calcium deposits\n"
    "✗ Rust stains or discoloration (only mark if actual crack is present)\n"
    "✗ Shadows from lighting, objects, or edges\n"
    "✗ Construction joints, expansion joints, control joints\n"
    "✗ Tie-rod holes, weep holes, bolt holes\n"
    "✗ Paint marks, chalk lines, existing annotations\n"
    "✗ Texture variations, aggregate patterns, color gradients\n"
    "✗ Biological growth: moss, mold, lichen, algae\n"
    "✗ Background: sky, vegetation, vehicles, people, soil\n\n"

    "━━━ COLOR CODING — MANDATORY ━━━\n"
    "Classify each crack segment by actual visible width:\n\n"
    "① HAIRLINE (< 0.5 mm) → CYAN #00FFFF | Stroke: 1.5–2 px | Opacity: 85%\n"
    "② MEDIUM (0.5–2 mm)   → YELLOW #FFE000 | Stroke: 2.5–3.5 px | Opacity: 90%\n"
    "③ WIDE (> 2 mm)       → ORANGE #FF6200 | Stroke: 4–6 px | Opacity: 95%\n\n"
    "CRACK NETWORK RULE: A single network MUST use multiple colors — "
    "trunk cracks are wider (ORANGE/YELLOW), branches taper (YELLOW/CYAN). "
    "NEVER use one color for the entire crack system. "
    "Taper stroke to a fine point at each crack endpoint.\n\n"

    "━━━ SPALLING DETECTION ━━━\n"
    "Color: MAGENTA #FF00CC | Fill opacity: 30–50%\n"
    "Detect ONLY real material loss:\n"
    "✓ Visible cavity, depression, or missing chunk\n"
    "✓ Exposed aggregate or rebar\n"
    "Fill rules:\n"
    "• Trace exact organic, irregular boundary — never rectangular or circular\n"
    "• Semi-transparent fill — original texture must remain visible underneath\n"
    "• Tight boundary — zero padding beyond damaged area\n"
    "• Each separate spall = separate fill (never connect unrelated zones)\n"
    "• Single spall zone must not exceed 15% of total image area\n"
    "• DO NOT fill stained, shadowed, or discolored areas\n\n"

    "━━━ VISUAL QUALITY REQUIREMENTS ━━━\n"
    "• Overlay must align perfectly with the original image (pixel-accurate)\n"
    "• Maintain transparency 30–50% so original texture is always visible\n"
    "• All strokes must be anti-aliased and smooth — no pixelated or jagged lines\n"
    "• No large unrealistic colored patches or color bleeding outside defect zones\n"
    "• Output must be EXACTLY the same pixel dimensions as the input image\n"
    "• NO text, labels, legends, arrows, scale bars, watermarks, or borders\n\n"

    "━━━ IF NO DEFECTS FOUND ━━━\n"
    "If the image contains no genuine cracks or defects, return the ORIGINAL image "
    "completely unmodified. Do not add any marking.\n\n"

    "Goal: produce a professional, engineering-grade defect visualization — "
    "not an artistic interpretation. Accuracy over coverage."
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
