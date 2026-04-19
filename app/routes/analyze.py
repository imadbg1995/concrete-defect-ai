import io

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image as PILImage

from app.config import settings
from app.services.claude import call_claude
from app.services.imaging import resize_for_api

router = APIRouter()


def validate_image(data: bytes) -> None:
    """Raise HTTPException if bytes are not a valid image."""
    try:
        img = PILImage.open(io.BytesIO(data))
        img.verify()
    except Exception:
        raise HTTPException(400, "Invalid or unreadable image file. Please upload a JPEG, PNG, or WebP.")

REPORT_PROMPT = """\
You are a Senior Civil Engineer with 25+ years of field experience in concrete and pavement pathology.
You write structured field assessment reports used by contractors, inspectors, and asset owners.

SITE CONTEXT:
{context}

Analyze the attached image and produce a structured pathology report covering ALL 8 sections below.
Use precise engineering terminology. Be specific to what you actually observe — never generic.

FORMATTING RULES — follow exactly:
- Use ## for main section headings (e.g. ## 1. PRIMARY DEFECT CLASSIFICATION)
- Use ### for sub-headings within a section
- Use - for bullet points
- Use **bold** for key terms and ratings
- Do NOT use markdown tables — use bullet lists instead
- Do NOT reference any external standards, codes, or norms (no ACI, ASTM, EN, CSA, ISO, etc.)
- Separate each section with ---

---

## 1. PRIMARY DEFECT CLASSIFICATION

Identify the main defect type using precise engineering terminology.
State whether it is a **structural**, **durability**, or **functional/surface** defect.
Name the defect pattern (e.g. map cracking, longitudinal crack, transverse crack, spalling, delamination, efflorescence).

---

## 2. DETAILED VISUAL OBSERVATIONS

Describe precisely what you observe:
- **Crack geometry:** pattern, estimated width (hairline <0.1mm / fine 0.1–0.3mm / medium 0.3–1mm / wide >1mm), orientation
- **Surface condition:** spalling, delamination, scaling, honeycombing, raveling
- **Staining and deposits:** efflorescence, rust stains, biological growth, watermarks
- **Active vs dormant:** signs of water seepage, fresh edges, debris in cracks
- **Affected area:** localized (<1 m²) / moderate (1–10 m²) / extensive (>10 m²)

---

## 3. ROOT CAUSE ANALYSIS

Explain the mechanism that produced these defects. Consider and rank causes from most to least likely:
- **Structural causes:** overloading, differential settlement, inadequate reinforcement cover
- **Physico-chemical causes:** alkali-aggregate reaction, carbonation, chloride-induced corrosion, freeze-thaw
- **Execution causes:** poor curing, premature formwork removal, inadequate compaction
- **Environmental causes:** de-icing salts, marine exposure, acid attack, heavy traffic

---

## 4. SEVERITY AND URGENCY ASSESSMENT

Rate each item and justify with specific observations:
- **Overall severity:** Low / Medium / High / Critical
- **Structural risk:** None / Possible / Probable / Imminent
- **Progression risk:** Stable / Slowly evolving / Rapidly evolving / Unknown
- **Intervention urgency:** Routine maintenance / Planned repair within 1–2 years / Priority repair within 6 months / Immediate intervention required

---

## 5. RECOMMENDED INVESTIGATIONS

List the most critical tests for this specific case before finalizing repair:

### Non-destructive tests
- List relevant tests (half-cell potential, cover meter, GPR, Schmidt hammer, IR thermography, chain drag)

### Destructive / laboratory tests
- List relevant tests (core extraction, chloride profile, carbonation depth, petrographic analysis, pH testing)

### Monitoring
- List relevant monitoring methods (crack width gauges, photographic documentation, deformation survey)

---

## 6. REPAIR STRATEGY

Propose a concrete repair strategy:
- **Surface preparation:** (sandblasting, hydro-demolition, saw-cutting, mechanical cleaning)
- **Repair approach:** (crack injection, partial demolition, full-depth repair, overlay)
- **Recommended materials:** (epoxy injection, polyurethane grout, cementitious repair mortar, silane/siloxane impregnation)
- **Execution sequence:** describe the key steps in order
- **Quality control points:** critical checks during execution
- **Long-term protection:** measures to prevent recurrence

---

## 7. CONDITION RATING

- **Overall condition:** Poor / Fair / Good / Very Good / Excellent
- **Estimated remaining service life without repair:** give a range in years
- **Executive summary:** 2–3 sentences suitable for a non-technical owner or project manager

---

## 8. DISCLAIMER

This is an AI-assisted preliminary visual assessment based solely on photographic evidence. It does not replace a comprehensive on-site inspection by a licensed Professional Engineer. A qualified engineer must conduct a full physical investigation before any structural conclusions or repair decisions are made. This report has no legal or contractual standing.
"""


@router.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    element_type: str = Form(""),
    structure_age: str = Form(""),
    exposure: str = Form(""),
    water_infiltration: str = Form(""),
    crack_evolution: str = Form(""),
    previous_repair: str = Form(""),
    customer_notes: str = Form(""),
):
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(400, "No image data received.")
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(400, f"Image exceeds {settings.max_image_size_mb}MB limit.")
    validate_image(image_bytes)
    image_bytes, mime = resize_for_api(image_bytes)

    def val(v: str) -> str:
        return v.strip() if v.strip() else "Not provided"

    context = (
        f"- Element type: {val(element_type)}\n"
        f"- Approximate age: {val(structure_age)}\n"
        f"- Exposure conditions: {val(exposure)}\n"
        f"- Water infiltration visible: {val(water_infiltration)}\n"
        f"- Defect evolving: {val(crack_evolution)}\n"
        f"- Previous repair: {val(previous_repair)}\n"
        f"- Inspector notes: {val(customer_notes)}"
    )
    prompt = REPORT_PROMPT.format(context=context)

    try:
        report = await call_claude(image_bytes, mime, prompt, max_tokens=8192)
    except Exception as exc:
        raise HTTPException(502, f"AI service error: {exc}") from exc

    return {"report": report}
