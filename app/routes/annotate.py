import base64
import io
import json
import math

from fastapi import APIRouter, File, HTTPException, UploadFile
from PIL import Image as PILImage

from app.config import settings
from app.services.claude import call_claude, strip_json_fences
from app.services.gemini import generate_annotated_image
from app.services.imaging import resize_for_api

router = APIRouter()


def validate_image(data: bytes) -> None:
    try:
        img = PILImage.open(io.BytesIO(data))
        img.verify()
    except Exception:
        raise HTTPException(400, "Invalid or unreadable image file.")


CLAUDE_PROMPT = """\
You are a concrete and pavement inspection expert.

Analyze this photo and return ONLY this JSON format.
Be EXTREMELY PRECISE with coordinates (0-100%).

IMPORTANT: Only annotate the CONCRETE SURFACE itself. Ignore background, sky, people, vehicles, and surroundings.

{
  "fissures": [
    {
      "id": 1,
      "type": "fine|medium|wide",
      "epaisseur_mm": 0.3,
      "points_xy": [[x1,y1],[x2,y2],[x3,y3]],
      "description": "short description"
    }
  ],
  "zones_deteriorees": [
    {
      "id": 1,
      "type": "eclat|desquamation|effritement|void|joint",
      "points_xy": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]],
      "description": "short description"
    }
  ],
  "niveau_gravite": "faible|moyen|critique",
  "recommendation": "short text"
}

CRACK RULES:
1. Only trace cracks ON the concrete surface — never extend into background/sky/road
2. Crack crossing full concrete area → MINIMUM 30 points
3. Medium crack → MINIMUM 15 points
4. Short crack → MINIMUM 8 points
5. FORBIDDEN: crack with only 2-4 points
6. FORBIDDEN: straight diagonal line approximation
7. Trace the EXACT curved path of each crack
8. fine: <0.5mm | medium: 0.5-2mm | wide: >2mm

ZONE RULES — VERY IMPORTANT:
- Zones must be SMALL and TIGHT around the actual deteriorated spot
- Maximum zone size: 8% radius of image dimension (e.g. if image is 100 units wide, max radius = 8)
- Typical zone radius: 3-6% of image dimension
- Trace the TIGHT boundary around the deteriorated area only
- Use 10-14 polygon points to define the boundary
- Do NOT create large zones covering multiple defects — one zone per defect spot
- Do NOT place zones outside the concrete surface
"""

SEVERITY_MAP  = {"faible": "low", "moyen": "medium", "critique": "high"}
CRACK_SEV_MAP = {"fine": "low", "medium": "medium", "wide": "high"}
ZONE_TYPE_MAP = {
    "eclat": "spalling", "desquamation": "delamination",
    "effritement": "raveling", "void": "pothole", "joint": "joint_deterioration",
}


def _infer_crack_type(pts: list) -> str:
    if len(pts) < 2:
        return "diagonal_crack"
    dx = abs(pts[-1][0] - pts[0][0])
    dy = abs(pts[-1][1] - pts[0][1])
    if dx > dy * 1.8:
        return "transverse_crack"
    if dy > dx * 1.8:
        return "longitudinal_crack"
    return "diagonal_crack"


def _parse_pts_raw(raw_pts: list) -> list[dict]:
    pts = []
    for p in raw_pts:
        if isinstance(p, (list, tuple)) and len(p) >= 2:
            pts.append({"x": max(0.0, min(100.0, float(p[0]))),
                        "y": max(0.0, min(100.0, float(p[1])))})
        elif isinstance(p, dict) and "x" in p and "y" in p:
            pts.append({"x": max(0.0, min(100.0, float(p["x"]))),
                        "y": max(0.0, min(100.0, float(p["y"])))})
    return pts


def _circle_fallback(cx: float, cy: float, r: float, n: int = 20) -> list[dict]:
    return [
        {"x": max(0.0, min(100.0, cx + r * math.cos(2 * math.pi * i / n))),
         "y": max(0.0, min(100.0, cy + r * math.sin(2 * math.pi * i / n)))}
        for i in range(n)
    ]


@router.post("/annotate")
async def annotate(image: UploadFile = File(...)):
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(400, "No image data received.")
    if len(image_bytes) > settings.max_image_size_mb * 1024 * 1024:
        raise HTTPException(400, f"Image exceeds {settings.max_image_size_mb}MB limit.")
    validate_image(image_bytes)

    api_bytes, mime = resize_for_api(image_bytes)

    # ── Claude analyzes the image ─────────────────────────────────────────────
    try:
        raw = await call_claude(api_bytes, mime, CLAUDE_PROMPT,
                                max_tokens=16384, model="claude-sonnet-4-6")
    except Exception as exc:
        raise HTTPException(502, f"Claude error: {exc}") from exc

    raw = strip_json_fences(raw)
    try:
        analysis = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, f"Could not parse Claude JSON: {exc}") from exc

    defects: list[dict] = []

    # ── Cracks → polylines ────────────────────────────────────────────────────
    for f in analysis.get("fissures", []):
        pts = _parse_pts_raw(f.get("points_xy", []))
        if len(pts) < 2:
            continue
        crack_w = str(f.get("type", "medium")).lower().strip()
        defects.append({
            "id":          int(f.get("id", len(defects) + 1)),
            "defect_type": _infer_crack_type([(p["x"], p["y"]) for p in pts]),
            "geometry":    "polyline",
            "severity":    CRACK_SEV_MAP.get(crack_w, "medium"),
            "points":      pts,
            "notes":       f.get("description", ""),
        })

    # ── Deteriorated zones → polygons ─────────────────────────────────────────
    for z in analysis.get("zones_deteriorees", []):
        pts = _parse_pts_raw(z.get("points_xy", []))
        if len(pts) < 3:
            cx = float(z.get("centre_x", z.get("center_x", 50)))
            cy = float(z.get("centre_y", z.get("center_y", 50)))
            r  = float(z.get("rayon", z.get("radius", 5)))
            # Cap radius to max 10% of image dimension
            r = min(r, 10.0)
            pts = _circle_fallback(cx, cy, r)
        else:
            # Validate zone is not too large (bounding box check)
            xs = [p["x"] for p in pts]
            ys = [p["y"] for p in pts]
            w  = max(xs) - min(xs)
            h  = max(ys) - min(ys)
            if w > 35 or h > 35:
                # Zone is too large — skip it
                continue

        zone_fr = str(z.get("type", "eclat")).lower().strip()
        defects.append({
            "id":          int(z.get("id", len(defects) + 1)),
            "defect_type": ZONE_TYPE_MAP.get(zone_fr, "spalling"),
            "geometry":    "polygon",
            "severity":    SEVERITY_MAP.get(
                               analysis.get("niveau_gravite", "moyen").lower(), "medium"),
            "points":      pts,
            "notes":       z.get("description", ""),
        })

    if not defects:
        raise HTTPException(422, "No defects detected.")

    gravity_fr = analysis.get("niveau_gravite", "moyen").lower()
    inventory = {
        "overall_severity":   SEVERITY_MAP.get(gravity_fr, "medium"),
        "pci_estimate":       "",
        "primary_distress":   analysis.get("recommendation", ""),
        "secondary_distress": "",
        "total_defects":      len(defects),
        "notes":              analysis.get("recommendation", ""),
    }

    # ── Gemini paints the overlay on the image ───────────────────────────────
    try:
        annotated_png = await generate_annotated_image(api_bytes, mime)
        annotated_b64 = "data:image/png;base64," + base64.standard_b64encode(annotated_png).decode()
    except Exception as exc:
        raise HTTPException(502, f"Gemini image error: {exc}") from exc

    return {
        "annotations":      defects,
        "distress_summary": inventory,
        "annotated_b64":    annotated_b64,
        "count":            len(defects),
    }
