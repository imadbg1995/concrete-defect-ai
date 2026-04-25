import io

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from PIL import Image as PILImage

from app.auth import decode_token
from app.config import settings
from app.database import get_db
from app.services.claude import call_claude
from app.services.imaging import resize_for_api

router = APIRouter()


def _require_auth(authorization: str = None) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in to generate a report.")
    user_id = decode_token(authorization.split(" ", 1)[1])
    if not user_id:
        raise HTTPException(401, "Session expired. Please log in again.")
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if not user:
        raise HTTPException(401, "Account not found.")
    if user["tries_remaining"] <= 0:
        raise HTTPException(403, "You have used all 3 of your free analyses. Contact us for more.")
    return dict(user)


def validate_image(data: bytes) -> None:
    """Raise HTTPException if bytes are not a valid image."""
    try:
        img = PILImage.open(io.BytesIO(data))
        img.verify()
    except Exception:
        raise HTTPException(400, "Invalid or unreadable image file. Please upload a JPEG, PNG, or WebP.")

REPORT_PROMPT = """\
You are a Senior Civil Engineer with 25+ years of experience in concrete, structural, and pavement pathology.

You produce structured, professional field-style assessment reports based STRICTLY on visual observations from images.

IMPORTANT BEHAVIOR RULES:
- This is a PRELIMINARY VISUAL ASSESSMENT ONLY — not a certified engineering diagnosis
- Base your analysis ONLY on what is clearly visible in the image
- If something cannot be confirmed visually, explicitly state: "Not observable from image"
- Do NOT assume hidden conditions (reinforcement, internal damage, subgrade, etc.)
- Avoid overconfidence — express uncertainty when appropriate
- Do NOT provide definitive conclusions requiring laboratory testing or site inspection
- Use cautious, professional engineering language

SITE CONTEXT:
{context}

TASK:
Analyze the provided image and produce a structured pathology report covering ALL 8 sections below.

FORMATTING RULES — follow exactly:
- Use ## for main section headings
- Use ### for sub-headings within a section
- Use - for bullet points
- Use **bold** for key terms and ratings
- Do NOT use markdown tables
- Do NOT reference any external standards, codes, or norms (ACI, ASTM, CSA, etc.)
- Separate each section with ---
- Keep writing concise, technical, and field-oriented

---

## 1. PRIMARY DEFECT CLASSIFICATION
- Identify the most probable defect type(s)
- If uncertain, provide 2–3 plausible classifications

---

## 2. DETAILED VISUAL OBSERVATIONS
- Describe ONLY visible features:
  - Crack patterns, width (approximate if possible), orientation
  - Surface condition (spalling, scaling, discoloration, etc.)
  - Environmental indicators (moisture, staining, vegetation, etc.)
- Do not interpret yet — only observe

---

## 3. ROOT CAUSE ANALYSIS
- Provide likely causes based on observed evidence
- Use conditional language:
  - "This may indicate…"
  - "This is commonly associated with…"
- If multiple causes possible → list them
- Clearly separate confirmed vs inferred elements

---

## 4. SEVERITY AND URGENCY ASSESSMENT
- Rate severity: **Low / Moderate / High / Critical**
- Rate urgency: **Monitor / Plan repair / Urgent inspection required**
- Justify based ONLY on visible damage
- If safety risk suspected → explicitly flag:
  - **"Potential safety concern – in-person inspection recommended"**

---

## 5. RECOMMENDED INVESTIGATIONS
- Suggest typical follow-up actions:
  - Visual inspection by engineer
  - Non-destructive testing (hammer sounding, rebound, etc.)
  - Core sampling or lab testing (if relevant)
- Phrase as possibilities, not requirements

---

## 6. REPAIR STRATEGY
- Suggest general intervention approaches:
  - Surface repair, crack sealing, patching, etc.
- Use non-prescriptive wording:
  - "Typical repair options may include…"
- Do NOT provide design-level solutions or specifications

---

## 7. CONDITION RATING
- Provide overall condition:
  - **Good / Fair / Poor / Critical**
- Add a **Confidence Level**:
  - **Low / Medium / High**
- Justify briefly based on image clarity and visible indicators

---

## 8. DISCLAIMER
This report is an AI-generated preliminary visual assessment based solely on the provided image and limited contextual information.
It does not constitute a professional engineering opinion, certified inspection, or design recommendation.
A qualified licensed engineer should perform an in-person evaluation before any decisions or interventions are undertaken.
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
    authorization: str = Header(None),
):
    user = _require_auth(authorization)

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

    # Deduct one try after successful analysis
    db = get_db()
    db.execute("UPDATE users SET tries_remaining = tries_remaining - 1 WHERE id = ?", (user["id"],))
    db.commit()
    tries_left = user["tries_remaining"] - 1
    db.close()

    return {"report": report, "tries_remaining": tries_left}
