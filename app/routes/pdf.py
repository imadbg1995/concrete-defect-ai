import base64

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.config import settings
from app.services.pdf_gen import generate_pdf

router = APIRouter()


class PdfRequest(BaseModel):
    report: str
    original_b64: str = ""
    annotated_b64: str = ""


def _b64_to_bytes(data_uri: str) -> bytes | None:
    if not data_uri:
        return None
    try:
        if "," in data_uri:
            data_uri = data_uri.split(",", 1)[1]
        return base64.b64decode(data_uri)
    except Exception:
        return None


@router.post("/export-pdf")
async def export_pdf(body: PdfRequest):
    if not body.report.strip():
        raise HTTPException(400, "Report text is required.")

    original_bytes = _b64_to_bytes(body.original_b64)
    annotated_bytes = _b64_to_bytes(body.annotated_b64)

    try:
        pdf_bytes = generate_pdf(
            report_text=body.report,
            original_bytes=original_bytes,
            annotated_bytes=annotated_bytes,
            brand_name=settings.app_name,
        )
    except Exception as exc:
        raise HTTPException(500, f"PDF generation failed: {exc}") from exc

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="concrete-defect-report.pdf"'},
    )
