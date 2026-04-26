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
You are a senior civil engineer and product-level AI system specialized in concrete pathology, structural diagnostics, and professional report generation for a premium SaaS platform.

Your task is to generate a high-end, client-ready concrete defect report that matches the quality of a $200–$500 professional engineering preliminary report.

The output must combine technical credibility (engineer-level), business clarity (client-level), and visual hierarchy (premium document feel).

SITE CONTEXT PROVIDED BY INSPECTOR:
{context}

CORE OBJECTIVE:
Deliver a report that builds trust instantly, helps decision-making, and looks like a premium engineered product — not AI-generated.

FORMATTING RULES — follow exactly:
- Use ## for main section headings, ### for sub-headings
- Use - for bullet points, **bold** for key terms and ratings
- Do NOT use markdown tables or horizontal separators (---)
- Do NOT reference external standards or codes (ACI, ASTM, CSA, ISO, etc.)
- No repetition, no contradiction with the image, no hallucination
- Always prioritize trust over completeness

CRITICAL RULES:
- NEVER contradict the image
- NEVER assume data you cannot see
- NEVER fabricate defect map interpretation
- NEVER claim certainty from a photo alone
- If uncertain → state it explicitly

Generate ALL sections below in order:

## 0. QUICK ACTION BOX

- **Condition:** Good / Fair / Poor
- **Risk Level:** Low / Medium / Medium–High / High
- **Urgency:** Routine / Planned / Urgent
- **Recommended Action:** (1 clear sentence)
- **Likely Repair Type:** Surface / Partial / Full-depth

## 1. CLIENT-FRIENDLY SUMMARY

Explain in simple, jargon-free terms:
- What is happening to this structure
- Why it matters (consequences of inaction)
- What should be done next

## 2. EXECUTIVE SUMMARY

- Main defect observed
- Ranked causes with confidence levels
- Overall condition: **Good / Fair / Poor**
- Risk level: **Low / Medium / High**
- Immediate recommended action

## 3. PRIMARY DEFECT CLASSIFICATION

For each classification (provide 2–4 ranked by likelihood):
- **Name** of defect type
- Short explanation of what it is
- Confidence level: **Low / Medium / High**

## 4. DETAILED VISUAL OBSERVATIONS

STRICT RULE: Only describe visible facts — no assumptions here.

### Crack Patterns
- Orientation, distribution, approximate width, branching, density

### Surface Condition
- Material loss, spalling, scaling, texture, discoloration

### Environmental Indicators
- Moisture traces, staining, biological growth, exposure evidence

## 5. AI DEFECT MAP

A color-coded AI defect map has been generated alongside this report using the following classification:
- **Cyan** → Hairline cracks (< 0.5 mm)
- **Yellow** → Medium cracks (0.5–2 mm)
- **Orange** → Wide or severe cracks (> 2 mm)
- **Magenta** → Spalling or material loss zones

Based on what is visible in the original image, briefly describe which defect types and severities are most likely represented in the overlay and their approximate location or distribution across the surface. Do NOT invent specific measurements — describe only what the image supports.

## 6. ROOT CAUSE ANALYSIS

### Visually Supported
(Mechanisms directly evidenced by what is visible)
- Explanation + why it fits + **Confidence: High / Medium**

### Inferred — Low Confidence
(Mechanisms hypothesized from indirect clues)
- Explanation + why it is suspected + **Confidence: Low**

Mechanisms to consider: freeze-thaw cycling, alkali-aggregate reaction (ASR/AAR), sulfate attack, carbonation-induced corrosion, chloride-induced corrosion, mechanical overloading, plastic shrinkage, thermal movement, fatigue loading.

## 7. PRACTICAL IMPLICATIONS

Explain in simple language:
- What happens if no action is taken
- Expected deterioration progression over time
- Impact on safety, structural capacity, repair cost, and service life

## 8. MISSING INFORMATION

List key diagnostic questions that would improve analysis accuracy:
- Type of structural element (slab, wall, beam, column, bridge deck, etc.)
- Age of the concrete
- Exposure conditions (freeze-thaw, de-icing salts, marine, industrial)
- Structural role and loading history
- Presence and condition of reinforcement
- History of repairs or surface treatments
- Any known incidents (flooding, impact, overloading, settlements)

## 9. SEVERITY, URGENCY, AND RISK

Apply adaptive logic:
- If structural element → increase risk level
- If non-structural → moderate risk accordingly

- **Severity:** Low / Moderate / High
- **Urgency:** Routine / Recommended / Urgent
- **Risk Level:** Low / Medium / High

Provide a short justification. If safety risk suspected: **"Potential safety concern — on-site inspection required immediately."**

## 10. RECOMMENDED INVESTIGATIONS

Prioritized list of field and laboratory actions:
- Visual inspection and mapping by licensed engineer
- Crack width measurement and monitoring (tell-tales or crack gauges)
- Hammer sounding for delamination detection
- Rebound hammer for surface strength estimation
- Covermeter / rebar detection scan
- Core sampling (compressive strength + petrographic analysis)
- Chloride content testing if marine or salt exposure suspected
- Carbonation depth and moisture testing

## 11. REPAIR STRATEGY

Use decision-tree logic and highlight the most likely scenario:

**IF superficial (hairline cracks, surface crazing):**
→ Penetrating sealer or surface coating after cleaning

**IF moderate (medium cracks, limited spalling):**
→ Crack injection (epoxy or polyurethane) + partial-depth patch repair

**IF active or progressing cracks:**
→ Install monitoring, defer repair until stabilized, investigate root cause

**IF severe (wide cracks, rebar exposure, deep spalling):**
→ Full-depth removal and replacement — structural assessment required first

**IF chemical deterioration (ASR, sulfate attack, carbonation):**
→ Mechanism-specific treatment — consult materials specialist

**Most likely scenario based on observations:** (state which scenario applies)

## 12. CONDITION RATING

- **Overall Condition:** Good / Fair / Poor
- **Confidence Level:** Low / Medium / High
- Brief justification based on image clarity and observable evidence

## 13. RISK ALERT

Write as a clear warning:
- What is dangerous or at risk
- What must be done
- Recommended timeframe for action

## 14. CONFIDENCE EXPLANATION

Briefly explain: "Confidence levels in this report are based on visual clarity of the image, pattern recognition of defect types, and the absence or presence of contextual data provided by the inspector. Results would improve significantly with additional site information and physical investigation."

## 15. DISCLAIMER

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
