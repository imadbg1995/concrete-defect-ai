"""PDF report generation using ReportLab."""

import io
import re
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ACCENT = colors.HexColor("#E05F1A")
TEXT_DARK = colors.HexColor("#1a1a1a")
TEXT_MUTED = colors.HexColor("#555555")
TEXT_LIGHT = colors.HexColor("#888888")
BORDER = colors.HexColor("#DDDDDD")
BG_LIGHT = colors.HexColor("#FFF8F0")


def _make_styles() -> dict:
    return {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=19,
            textColor=TEXT_DARK,
            spaceAfter=3,
            leading=24,
        ),
        "meta": ParagraphStyle(
            "meta",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT_LIGHT,
            spaceAfter=0,
        ),
        "img_label": ParagraphStyle(
            "img_label",
            fontName="Helvetica-Bold",
            fontSize=7,
            textColor=ACCENT,
            spaceAfter=5,
            leading=10,
            letterSpacing=1.2,
        ),
        "section": ParagraphStyle(
            "section",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=4,
            leading=11,
            letterSpacing=1.0,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=TEXT_MUTED,
            leading=16,
            spaceAfter=7,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            textColor=TEXT_MUTED,
            leading=16,
            spaceAfter=4,
            leftIndent=14,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=8.5,
            textColor=TEXT_MUTED,
            leading=13,
            spaceAfter=0,
        ),
    }


def _get_rl_image(img_bytes: bytes, max_w: float, max_h: float) -> RLImage | None:
    try:
        pil = PILImage.open(io.BytesIO(img_bytes))
        pw, ph = pil.size
        ratio = ph / pw
        w = min(max_w, max_h / ratio if ratio > 0 else max_w)
        h = w * ratio
        if h > max_h:
            h = max_h
            w = h / ratio
        return RLImage(io.BytesIO(img_bytes), width=w, height=h)
    except Exception:
        return None


def _parse_report(text: str, styles: dict) -> list:
    flowables = []
    sections = re.split(r"\n(?=### )", text)

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split("\n")
        first = lines[0].strip()

        if first.startswith("### "):
            header = re.sub(r"^\d+\.\s+", "", first[4:].strip())
            flowables.append(Paragraph(header.upper(), styles["section"]))
            flowables.append(
                HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=5, spaceBefore=0)
            )
            content_lines = lines[1:]
        else:
            content_lines = lines

        buf: list[str] = []

        def flush_buf():
            if not buf:
                return
            text_out = " ".join(buf)
            text_out = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text_out)
            flowables.append(Paragraph(text_out, styles["body"]))
            buf.clear()

        for line in content_lines:
            stripped = line.strip()
            if not stripped:
                flush_buf()
                continue
            if stripped.startswith(("- ", "* ")):
                flush_buf()
                item = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped[2:].strip())
                flowables.append(Paragraph(f"\u2192 {item}", styles["bullet"]))
            else:
                buf.append(stripped)

        flush_buf()

    return flowables


def generate_pdf(
    report_text: str,
    original_bytes: bytes | None,
    annotated_bytes: bytes | None,
    brand_name: str = "Concrete Defect AI",
) -> bytes:
    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        title=f"{brand_name} – Concrete Defect Report",
        author=brand_name,
    )

    styles = _make_styles()
    story = []

    # Header
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(brand_name, styles["title"]))
    story.append(
        Paragraph(
            f"Concrete Defect Analysis Report &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp; AI-assisted preliminary visual assessment",
            styles["meta"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=10, spaceAfter=16))

    # Images section
    avail_w = (PAGE_W - 4 * cm) / 2 - 0.4 * cm
    max_img_h = 6.5 * cm
    cells_top: list[Paragraph] = []
    cells_img: list[RLImage | Paragraph] = []

    for label, img_bytes in [("UPLOADED PHOTO", original_bytes), ("AI DEFECT MAP", annotated_bytes)]:
        if img_bytes:
            rl_img = _get_rl_image(img_bytes, avail_w, max_img_h)
            cells_top.append(Paragraph(label, styles["img_label"]))
            cells_img.append(rl_img if rl_img else Paragraph("Image unavailable.", styles["body"]))

    if cells_top:
        col_ws = [avail_w + 0.4 * cm] * len(cells_top)
        t = Table([cells_top, cells_img], colWidths=col_ws, hAlign="LEFT")
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 0.35 * inch))

    # Report body
    story.extend(_parse_report(report_text, styles))

    # Disclaimer
    story.append(Spacer(1, 0.15 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceAfter=8))
    story.append(
        Paragraph(
            (
                "<b>DISCLAIMER:</b> This report is based solely on photographic analysis by an AI system. "
                "It constitutes a preliminary visual assessment only and does not replace a comprehensive "
                "on-site inspection by a licensed Professional Engineer. A qualified P.Eng must conduct a "
                "full investigation, including physical testing and sampling, before any structural conclusions "
                "or repair decisions are made. This report has no legal or contractual standing."
            ),
            styles["disclaimer"],
        )
    )

    doc.build(story)
    return buf.getvalue()
