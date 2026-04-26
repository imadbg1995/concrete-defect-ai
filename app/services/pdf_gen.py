"""PDF report generation using ReportLab — v3."""

import io
import re
from datetime import datetime

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
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

# ── Palette ──────────────────────────────────────────────────
ACCENT        = colors.HexColor("#E05F1A")
ACCENT_LIGHT  = colors.HexColor("#FFF5EE")
ACCENT_BORDER = colors.HexColor("#E8A878")
DANGER        = colors.HexColor("#B03020")
DANGER_LIGHT  = colors.HexColor("#FEF3F2")
DANGER_BORDER = colors.HexColor("#CC8880")
TEXT_DARK     = colors.HexColor("#1A1A1A")
TEXT_MUTED    = colors.HexColor("#444444")
TEXT_LIGHT    = colors.HexColor("#999999")
BORDER        = colors.HexColor("#DDDDDD")
BORDER_DARK   = colors.HexColor("#BBBBBB")


def _styles() -> dict:
    return {
        "title": ParagraphStyle("title",
            fontName="Helvetica-Bold", fontSize=20, textColor=TEXT_DARK,
            spaceAfter=3, leading=26),
        "meta": ParagraphStyle("meta",
            fontName="Helvetica", fontSize=9, textColor=TEXT_LIGHT, spaceAfter=0),
        "img_label": ParagraphStyle("img_label",
            fontName="Helvetica-Bold", fontSize=7, textColor=ACCENT,
            spaceAfter=5, leading=10, letterSpacing=1.2),
        "legend_title": ParagraphStyle("legend_title",
            fontName="Helvetica-Bold", fontSize=7, textColor=TEXT_LIGHT,
            spaceAfter=4, leading=10, letterSpacing=1.0),
        "legend_text": ParagraphStyle("legend_text",
            fontName="Helvetica", fontSize=8, textColor=TEXT_MUTED,
            leading=12, spaceAfter=0, alignment=TA_CENTER),
        # Main section heading  (## )
        "h2": ParagraphStyle("h2",
            fontName="Helvetica-Bold", fontSize=11.5, textColor=TEXT_DARK,
            spaceBefore=18, spaceAfter=6, leading=15),
        # Sub-section heading  (### )
        "h3": ParagraphStyle("h3",
            fontName="Helvetica-Bold", fontSize=7.5, textColor=ACCENT,
            spaceBefore=10, spaceAfter=4, leading=11, letterSpacing=1.0),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=10, textColor=TEXT_MUTED,
            leading=16, spaceAfter=7),
        "bullet": ParagraphStyle("bullet",
            fontName="Helvetica", fontSize=10, textColor=TEXT_MUTED,
            leading=16, spaceAfter=4, leftIndent=12),
        # Quick Action Box
        "qa_body": ParagraphStyle("qa_body",
            fontName="Helvetica", fontSize=10.5, textColor=TEXT_DARK,
            leading=17, spaceAfter=5),
        "qa_bullet": ParagraphStyle("qa_bullet",
            fontName="Helvetica", fontSize=10.5, textColor=TEXT_DARK,
            leading=17, spaceAfter=5, leftIndent=0),
        # Risk Alert Box
        "alert_body": ParagraphStyle("alert_body",
            fontName="Helvetica-Bold", fontSize=10.5,
            textColor=colors.HexColor("#8B1A10"),
            leading=17, spaceAfter=5),
        "alert_bullet": ParagraphStyle("alert_bullet",
            fontName="Helvetica", fontSize=10.5,
            textColor=colors.HexColor("#8B1A10"),
            leading=17, spaceAfter=5, leftIndent=0),
        # Disclaimer (section 15)
        "disclaimer": ParagraphStyle("disclaimer",
            fontName="Helvetica", fontSize=9, textColor=TEXT_MUTED,
            leading=14, spaceAfter=5),
    }


def _b(text: str) -> str:
    """Convert **bold** markers to ReportLab HTML."""
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)


def _get_rl_image(img_bytes: bytes, max_w: float, max_h: float):
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


def _render_lines(lines: list[str], st: dict,
                  bullet_key: str = "bullet",
                  body_key: str = "body") -> list:
    """Convert text lines to ReportLab flowables."""
    out = []
    buf: list[str] = []

    def flush():
        if buf:
            out.append(Paragraph(_b(" ".join(buf)), st[body_key]))
            buf.clear()

    for line in lines:
        s = line.strip()
        if not s:
            flush()
        elif s.startswith("### "):
            flush()
            out.append(Paragraph(s[4:].strip().upper(), st["h3"]))
            out.append(HRFlowable(width="100%", thickness=0.5,
                                  color=ACCENT, spaceAfter=5))
        elif s.startswith(("- ", "* ")):
            flush()
            out.append(Paragraph(f"\u2192 {_b(s[2:].strip())}", st[bullet_key]))
        elif s.startswith("\u2192 ") or s.startswith("→ "):
            flush()
            text = s[2:].strip() if s.startswith("→ ") else s[2:].strip()
            out.append(Paragraph(f"\u2192 {_b(text)}", st[bullet_key]))
        elif s.startswith("## "):
            flush()  # nested ## — skip silently
        else:
            buf.append(s)

    flush()
    return out


def _box(content: list, bg: colors.Color,
         border_color: colors.Color, usable_w: float) -> Table:
    """Wrap a list of flowables in a colored background box."""
    t = Table([[content]], colWidths=[usable_w])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("BOX",           (0, 0), (-1, -1), 1.2, border_color),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _parse_report(text: str, st: dict, usable_w: float) -> list:
    """Parse the Claude report text into ReportLab flowables."""
    out = []
    chunks = re.split(r'\n(?=## )', text.strip())

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        lines = chunk.split('\n')
        first = lines[0].strip()
        content_lines = lines[1:]

        # Not a section heading — render as plain body
        if not first.startswith("## "):
            out.extend(_render_lines(lines, st))
            continue

        header = first[3:].strip()
        m = re.match(r'^(\d+)\.\s+(.+)$', header)
        num   = m.group(1) if m else None
        title = m.group(2) if m else header

        # ── Section 15: Disclaimer ───────────────────────
        if num == "15":
            out.append(Spacer(1, 0.12 * inch))
            out.append(HRFlowable(width="100%", thickness=1,
                                  color=BORDER, spaceAfter=8))
            out.extend(_render_lines(content_lines, st,
                                     bullet_key="disclaimer",
                                     body_key="disclaimer"))
            continue

        # ── Section heading ──────────────────────────────
        num_tag = (f'<font color="#E05F1A"><b>{num}.</b></font>\u2002'
                   if num else "")
        out.append(Spacer(1, 0.04 * inch))
        out.append(Paragraph(f'{num_tag}<b>{title.upper()}</b>', st["h2"]))
        out.append(HRFlowable(width="100%", thickness=0.8,
                              color=BORDER_DARK, spaceAfter=8, spaceBefore=1))

        # ── Section 0: Quick Action Box ──────────────────
        if num == "0":
            content = _render_lines(content_lines, st,
                                    bullet_key="qa_bullet", body_key="qa_body")
            out.append(_box(content, ACCENT_LIGHT, ACCENT_BORDER, usable_w))

        # ── Section 13: Risk Alert Box ───────────────────
        elif num == "13":
            content = _render_lines(content_lines, st,
                                    bullet_key="alert_bullet", body_key="alert_body")
            out.append(_box(content, DANGER_LIGHT, DANGER_BORDER, usable_w))

        else:
            out.extend(_render_lines(content_lines, st))

    return out


def generate_pdf(
    report_text: str,
    original_bytes: bytes | None,
    annotated_bytes: bytes | None,
    brand_name: str = "Concrete Defect AI",
) -> bytes:
    buf = io.BytesIO()
    PAGE_W, PAGE_H = A4
    MARGIN   = 2.0 * cm
    usable_w = PAGE_W - 2 * MARGIN

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=2.2 * cm, bottomMargin=2.2 * cm,
        title=f"{brand_name} – Concrete Defect Report",
        author=brand_name,
    )

    st    = _styles()
    story = []

    # ── Document header ──────────────────────────────────
    date_str = datetime.now().strftime("%B %d, %Y")
    story.append(Paragraph(brand_name, st["title"]))
    story.append(Paragraph(
        f"Concrete Defect Analysis Report &nbsp;·&nbsp; {date_str}"
        " &nbsp;·&nbsp; AI-assisted preliminary visual assessment",
        st["meta"],
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT,
                            spaceBefore=10, spaceAfter=18))

    # ── Side-by-side images ──────────────────────────────
    col_w    = usable_w / 2 - 0.4 * cm
    max_h    = 6.5 * cm
    lbl_row, img_row = [], []

    for label, img_bytes in [("UPLOADED PHOTO", original_bytes),
                              ("AI DEFECT MAP",  annotated_bytes)]:
        if img_bytes:
            rl = _get_rl_image(img_bytes, col_w, max_h)
            lbl_row.append(Paragraph(label, st["img_label"]))
            img_row.append(rl or Paragraph("Image unavailable.", st["body"]))

    if lbl_row:
        n   = len(lbl_row)
        cws = [col_w + 0.8 * cm] * n
        img_table = Table([lbl_row, img_row], colWidths=cws, hAlign="LEFT")
        img_table.setStyle(TableStyle([
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",  (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
        ]))
        story.append(img_table)

    # ── AI Defect Map color legend ───────────────────────
    LEGEND = [
        ("#00FFFF", "Cyan",    "Hairline  <0.5 mm"),
        ("#FFE000", "Yellow",  "Medium  0.5–2 mm"),
        ("#FF6200", "Orange",  "Wide  >2 mm"),
        ("#FF00CC", "Magenta", "Spalling zone"),
    ]
    lcw = usable_w / 4

    story.append(Spacer(1, 0.18 * inch))
    story.append(Paragraph("AI DEFECT MAP LEGEND", st["legend_title"]))

    color_row = [""] * 4
    text_row  = [Paragraph(desc, st["legend_text"]) for _, _, desc in LEGEND]
    leg = Table([color_row, text_row], colWidths=[lcw] * 4)
    leg_cmds = [
        ("ROWHEIGHT",    (0, 0), (-1, 0), 9),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 1), (-1, 1), 3),
        ("BOTTOMPADDING",(0, 1), (-1, 1), 3),
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",   (0, 0), (-1, 0), 0),
        ("BOTTOMPADDING",(0, 0), (-1, 0), 0),
        ("LINEBELOW",    (0, 0), (-1, 0), 0, colors.white),
    ]
    for i, (hex_c, _, _) in enumerate(LEGEND):
        leg_cmds.append(("BACKGROUND", (i, 0), (i, 0), colors.HexColor(hex_c)))
    leg.setStyle(TableStyle(leg_cmds))
    story.append(leg)
    story.append(Spacer(1, 0.28 * inch))

    # ── Report sections ──────────────────────────────────
    story.extend(_parse_report(report_text, st, usable_w))

    doc.build(story)
    return buf.getvalue()
