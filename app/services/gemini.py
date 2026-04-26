"""Gemini service — image generation for defect overlay + text for analysis."""

import re

from google import genai
from google.genai import types

from app.config import settings

OVERLAY_PROMPT = (
    "You are an expert concrete pathology segmentation system used by licensed structural engineers. "
    "Your task: paint a PRECISE, SCIENTIFICALLY ACCURATE color-coded defect overlay directly on this concrete image.\n\n"

    "━━━ GOLDEN RULE ━━━\n"
    "When in doubt — leave it out. A false positive (marking a non-defect) is worse than a "
    "false negative. Only mark what you are CERTAIN is a genuine structural defect.\n\n"

    "━━━ SECTION 1 — WHAT IS A TRUE CRACK ━━━\n"
    "A genuine crack has ALL of these properties:\n"
    "✓ Physical separation: an actual gap, fissure, or split in the material\n"
    "✓ Visible depth: a shadow inside the crack or darker interior\n"
    "✓ Sharp, defined edges (not fuzzy, gradient, or blurry)\n"
    "✓ Linear or branching path following structural stress directions\n"
    "✓ Consistent path — it starts somewhere and ends somewhere\n\n"

    "━━━ SECTION 2 — NEVER ANNOTATE THESE (False Positive List) ━━━\n"
    "✗ Water streaks, moisture runs, wet patches, damp spots, rain marks\n"
    "✗ Efflorescence: white or gray calcium deposits, salt bloom, mineral leaching\n"
    "✗ Rust stains or iron oxide discoloration (only mark if actual crack is visible)\n"
    "✗ Shadows from lighting angles, adjacent objects, formwork edges\n"
    "✗ Construction joints, control joints, expansion joints (designed separations)\n"
    "✗ Formwork tie-rod holes, weep holes, drainage holes, bolt holes\n"
    "✗ Paint marks, chalk lines, survey markings, pre-existing manual annotations\n"
    "✗ Texture variations, aggregate patterns, color gradients in the concrete\n"
    "✗ Biological growth: moss, mold, lichen, algae (green/black patches)\n"
    "✗ Background: sky, vegetation, vehicles, people, road surface, soil\n"
    "✗ Mortar joints between bricks or blocks (unless cracked through the masonry unit)\n"
    "✗ Bug holes, honeycombing surface texture from casting (unless structural crack present)\n\n"

    "━━━ SECTION 3 — COLOR CODE BY CRACK WIDTH ━━━\n"
    "Measure each crack segment's ACTUAL visual width and apply the correct color:\n\n"
    "① HAIRLINE / FINE — width < 0.5 mm\n"
    "   → Bright CYAN #00FFFF | Stroke: 1.5–2 px | Opacity: 85%\n"
    "   Typical: barely visible thin lines, early shrinkage, surface crazing\n\n"
    "② MEDIUM — width 0.5 mm to 2 mm\n"
    "   → Bright YELLOW #FFE000 | Stroke: 2.5–3.5 px | Opacity: 90%\n"
    "   Typical: clearly visible crack, structural loading, carbonation-induced\n\n"
    "③ WIDE / SEVERE — width > 2 mm\n"
    "   → Bright ORANGE #FF6200 | Stroke: 4–6 px | Opacity: 95%\n"
    "   Typical: open gap showing interior depth, rebar corrosion pressure, overloading\n\n"
    "CRITICAL WIDTH RULES:\n"
    "• A single crack NETWORK must use MULTIPLE colors — trunk is wider (ORANGE/YELLOW), "
    "branches taper (YELLOW/CYAN). Transition smoothly as width narrows.\n"
    "• NEVER paint the entire crack system in one single color.\n"
    "• At each crack endpoint, taper the stroke to a fine point — do not end bluntly.\n"
    "• Minimum crack length to annotate: 5 mm visual equivalent — ignore micro-specks.\n\n"

    "━━━ SECTION 4 — SPALLING & MATERIAL LOSS ZONES ━━━\n"
    "Color: MAGENTA #FF00CC | Fill opacity: 65–75%\n\n"
    "ONLY fill where concrete has PHYSICALLY BROKEN AWAY:\n"
    "✓ Visible cavity, depression, or hollow in the surface\n"
    "✓ Exposed aggregate, rebar, or underlying layer visible\n"
    "✓ Missing chunk of concrete leaving an irregular void\n\n"
    "Fill quality rules:\n"
    "• Trace the EXACT organic, irregular boundary of the actual damage — never rectangular or circular\n"
    "• Fill must be semi-transparent so the underlying texture remains visible through it\n"
    "• Keep the fill TIGHT — zero padding beyond the damaged area\n"
    "• Multiple separate spalls = multiple separate fills (never connect unrelated spalls)\n"
    "• DO NOT fill areas that are merely discolored, stained, shadowed, or wet\n"
    "• A single spall zone should never exceed 15% of the total image area\n\n"

    "━━━ SECTION 5 — SPECIAL DEFECT PATTERNS ━━━\n"
    "ASR MAP CRACKING (Alkali-Silica Reaction):\n"
    "• Random interconnected fine cracks in all directions — spider-web or crazing pattern\n"
    "• Use CYAN #00FFFF at 1.5 px for each individual strand of the network\n"
    "• Trace every branch of the pattern — do not simplify into a few lines\n\n"
    "REBAR CORROSION CRACKING:\n"
    "• Longitudinal cracks running parallel and directly above rebar lines\n"
    "• Use ORANGE #FF6200 — these are typically WIDE and urgent\n"
    "• If rust staining is visible alongside the crack, annotate only the crack itself\n\n"

    "━━━ SECTION 6 — RENDERING QUALITY ━━━\n"
    "• All strokes must be ANTI-ALIASED and SMOOTH — no pixelated, jagged, or blocky lines\n"
    "• Follow the actual curved path of each crack precisely using smooth curves\n"
    "• The ORIGINAL photo must remain fully visible everywhere — the overlay only adds "
    "color on top, it never blurs, erases, or darkens the underlying image\n"
    "• Output must be EXACTLY the same pixel dimensions as the input image\n"
    "• Absolutely NO text, labels, legends, arrows, numbers, scale bars, watermarks, "
    "borders, frames, or vignettes of any kind\n\n"

    "━━━ SECTION 7 — IF NO DEFECTS FOUND ━━━\n"
    "If the image contains NO genuine cracks or defects, return the ORIGINAL image "
    "completely unmodified. Do not add any overlay, color, or marking.\n\n"

    "Final output style: clean, precise, publication-quality structural inspection map — "
    "as would be produced by a certified concrete inspection laboratory."
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
