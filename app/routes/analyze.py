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
You are a senior civil engineer specialized in concrete materials, durability, and structural diagnostics.

Your task is to generate a highly professional, structured, and visually clear AI-assisted preliminary concrete defect report based on the provided image and site context below.

The output must feel like a real engineering document suitable for a SaaS product, while clearly stating that it is NOT a certified engineering report.

SITE CONTEXT PROVIDED BY INSPECTOR:
{context}

---

GENERAL REQUIREMENTS:
- Use a professional, concise, and structured engineering tone
- Avoid repetition and overly long sentences
- Be precise but cautious — never overclaim
- Clearly separate: Observed (what is visible) vs Inferred (what is assumed)
- Include confidence levels for all hypotheses
- Make the report understandable for both engineers and non-experts
- Ensure strong readability with clean layout, spacing, and hierarchy
- Use ## for section titles, ### for sub-headings, and - for bullet points
- Use **bold** for key terms, ratings, and risk levels
- Do NOT use markdown tables or horizontal separators between sections
- Do NOT reference external standards or codes (ACI, ASTM, CSA, ISO, etc.)

---

OUTPUT STRUCTURE — generate ALL sections in order:

## 0. CLIENT-FRIENDLY SUMMARY

Provide a simplified, easy-to-read summary for non-engineers:
- Main issue detected (plain language)
- Likely causes (simple wording, no jargon)
- Condition rating
- Risk level
- Immediate action recommended

---

## 1. EXECUTIVE SUMMARY

- Main defect observed
- Most likely causes (ranked by likelihood)
- Overall condition: **Good / Fair / Poor**
- Risk level: **Low / Medium / High**
- Immediate recommended action

---

## 2. PRIMARY DEFECT CLASSIFICATION

- Identify the main defect type
- Provide 2–4 possible classifications ranked by likelihood
- For each classification include:
  → Short explanation
  → Confidence level: **Low / Medium / High**

---

## 3. DETAILED VISUAL OBSERVATIONS

### Crack Patterns
- Describe only what is visible: orientation, length, width (approximate), distribution, branching

### Surface Condition
- Describe material loss, spalling, scaling, texture changes, discoloration

### Environmental Indicators
- Moisture traces, staining, debris, biological growth, exposure clues

(Use bullet points only — no assumptions or interpretations in this section)

---

## 4. AI DEFECT MAP LEGEND

Explain what each color in the AI-generated overlay represents:
- **Cyan** → Hairline / fine cracks (< 0.5 mm)
- **Yellow** → Medium cracks (0.5–2 mm)
- **Orange** → Wide / severe cracks (> 2 mm)
- **Magenta** → Spalling zones / material loss areas

If the image shows no overlay or no defects were mapped, state that clearly.

---

## 5. ROOT CAUSE ANALYSIS

Provide possible deterioration mechanisms. For each mechanism:
- Short explanation
- Why it matches the observed evidence
- Confidence level: **Low / Medium / High**

Clearly separate:
→ **Visually confirmed:** (directly observable)
→ **Inferred hypothesis:** (assumed from indirect evidence)

Possible mechanisms to consider: freeze-thaw cycling, alkali-aggregate reaction (AAR/ASR), sulfate attack, carbonation-induced corrosion, chloride-induced corrosion, mechanical overloading, plastic shrinkage, thermal cracking, fatigue.

---

## 6. MISSING INFORMATION — USER INPUT REQUIRED

List key information that would improve the diagnosis:
- Type of structural element (slab, wall, beam, column, bridge deck, etc.)
- Age of the concrete
- Exposure conditions (freeze-thaw cycles, de-icing salts, marine, industrial)
- Structural role and loading history
- Presence and condition of reinforcement
- History of previous repairs or treatments
- Any known incidents (flooding, impact, overloading)

---

## 7. SEVERITY, URGENCY, AND RISK

- **Severity:** Low / Moderate / High
- **Urgency:** Routine / Recommended / Urgent
- **Risk Level:** Low / Medium / High

Provide a short justification for each rating based strictly on visible evidence.
If a safety risk is suspected, explicitly state: **"Potential safety concern — on-site inspection required immediately."**

---

## 8. RECOMMENDED INVESTIGATIONS

List realistic field and laboratory investigations in order of priority:
- Visual inspection and mapping by a licensed engineer
- Crack width measurement and monitoring (tell-tales or crack gauges)
- Hammer sounding (delamination detection)
- Rebound hammer (surface strength estimation)
- Covermeter / rebar detection scan
- Core sampling (compressive strength + petrographic analysis)
- Chloride content testing (if marine or salt exposure suspected)
- Moisture and carbonation depth testing

Phrase as recommendations, not requirements.

---

## 9. REPAIR STRATEGY

Provide clear scenario-based guidance:

**IF damage is superficial (surface crazing, hairline cracks):**
→ Clean surface, apply penetrating sealer or surface coating

**IF cracks are active or progressing:**
→ Install monitoring devices, defer repair until stabilized, investigate root cause

**IF deterioration is moderate (medium cracks, limited spalling):**
→ Crack injection (epoxy or polyurethane), partial-depth patch repair

**IF deterioration is deep or structural (wide cracks, rebar exposure, spalling):**
→ Full-depth removal and replacement, structural assessment required before repair

**IF chemical deterioration is suspected (ASR, sulfate attack, carbonation):**
→ Mechanism-specific repair required — consult a materials specialist

---

## 10. CONDITION RATING

- **Overall Condition:** Good / Fair / Poor
- **Confidence Level:** Low / Medium / High

Provide a short justification based on image clarity and observable evidence.

---

## 11. RISK ALERT

Provide a warning-style message:
- Immediate risk explanation
- Clear next step with recommended timeframe
- Safety consideration if applicable

---

## 12. DISCLAIMER

This report is an AI-generated preliminary visual assessment based solely on the provided photograph and limited inspector-supplied context. It does not constitute a professional engineering opinion, a certified inspection report, or a design recommendation. It must not be used as the sole basis for any structural, safety, repair, or regulatory decision. A licensed Professional Engineer must perform an on-site physical investigation before any conclusions or interventions are made. This report has no legal, contractual, or professional standing in any jurisdiction.
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
