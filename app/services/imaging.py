"""
Pillow-based defect overlay renderer.
Style: bright cyan (#00E5FF) for fine/medium cracks,
       bright magenta (#FF00AA) for wide cracks and deteriorated zones.
Matches the computer-vision segmentation map aesthetic.
"""

import io
import platform

from PIL import Image, ImageDraw, ImageFilter, ImageFont

# ── Color palette ─────────────────────────────────────────────────────────────
CYAN    = (0,   229, 255)   # fine / medium cracks
MAGENTA = (255,   0, 170)   # wide cracks + deteriorated zones
BLACK   = (0,   0,   0)


def _get_font(size: int, bold: bool = False):
    candidates = []
    if platform.system() == "Windows":
        candidates = [
            f"C:/Windows/Fonts/{'arialbd' if bold else 'arial'}.ttf",
            f"C:/Windows/Fonts/{'calibrib' if bold else 'calibri'}.ttf",
        ]
    elif platform.system() == "Darwin":
        candidates = ["/System/Library/Fonts/Helvetica.ttc"]
    else:
        candidates = [f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf"]
    for p in candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _catmull_rom(pts: list[tuple], steps: int = 16) -> list[tuple]:
    """Smooth curve through control points using Catmull-Rom spline."""
    if len(pts) < 2:
        return pts
    clean = [pts[0]]
    for p in pts[1:]:
        if p != clean[-1]:
            clean.append(p)
    if len(clean) < 2:
        return clean
    pts = clean
    out: list[tuple] = []
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(n - 1, i + 2)]
        for s in range(steps):
            t  = s / steps
            t2 = t * t
            t3 = t2 * t
            x = 0.5 * (2*p1[0] + (-p0[0]+p2[0])*t + (2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2 + (-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3)
            y = 0.5 * (2*p1[1] + (-p0[1]+p2[1])*t + (2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2 + (-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)
            out.append((int(x), int(y)))
    out.append(pts[-1])
    return out


def _parse_pts(pts_raw: list, W: int, H: int) -> list[tuple]:
    out = []
    for p in pts_raw:
        if isinstance(p, dict) and "x" in p and "y" in p:
            x, y = float(p["x"]), float(p["y"])
        elif isinstance(p, (list, tuple)) and len(p) >= 2:
            x, y = float(p[0]), float(p[1])
        else:
            continue
        out.append((
            max(0, min(W - 1, int(x / 100 * W))),
            max(0, min(H - 1, int(y / 100 * H))),
        ))
    return out


def _crack_color(d: dict) -> tuple:
    sev = (d.get("severity") or "medium").lower()
    geo = (d.get("geometry") or "polyline").lower()
    if geo == "polygon" or sev in ("high", "critical"):
        return MAGENTA
    return CYAN


def _crack_width(d: dict, base: float) -> int:
    sev = (d.get("severity") or "medium").lower()
    if sev in ("high", "critical"):
        return max(4, int(base * 4.5))
    if sev == "medium":
        return max(2, int(base * 2.5))
    return max(1, int(base * 1.5))


def _draw_glow(draw: ImageDraw.Draw, pts: list[tuple], color: tuple,
               lw: int, glow_passes: int = 2) -> None:
    """Draw progressively wider semi-transparent strokes for a glow effect."""
    r, g, b = color
    for i in range(glow_passes, 0, -1):
        alpha = int(60 / i)
        glow_color = (r, g, b, alpha)
        glow_lw = lw + i * 3
        if len(pts) >= 2:
            draw.line(pts, fill=glow_color, width=glow_lw)


def _draw_minimal_legend(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    W, H = img.size
    fs   = max(11, W // 85)
    font = _get_font(fs, bold=True)
    pad  = max(8, W // 110)
    sw   = max(24, W // 55)
    sh   = max(8, fs // 3)
    row_h = int(fs * 2.0)

    entries = [
        (CYAN,    "Fine / medium crack"),
        (MAGENTA, "Wide crack / deteriorated zone"),
    ]

    max_tw = max(draw.textbbox((0, 0), lbl, font=font)[2] for _, lbl in entries)
    box_w = sw + pad * 3 + max_tw + pad
    box_h = len(entries) * row_h + pad * 2

    bx = W - box_w - pad * 2
    by = H - box_h - pad * 2

    # Panel background
    panel = Image.new("RGBA", (box_w + 2, box_h + 2), (8, 10, 18, 210))
    img.paste(Image.fromarray(
        __import__("numpy", fromlist=["array"]).array(panel, dtype="uint8")
        if False else panel.convert("RGB")), (bx - 1, by - 1)
    )
    draw.rectangle([bx - 1, by - 1, bx + box_w + 1, by + box_h + 1],
                   outline=(60, 80, 100), width=1)

    ry = by + pad
    for color, label in entries:
        sx0 = bx + pad
        sy0 = ry + (row_h - sh) // 2
        draw.rectangle([sx0, sy0, sx0 + sw, sy0 + sh], fill=color)
        tb = draw.textbbox((0, 0), label, font=font)
        draw.text((sx0 + sw + pad, ry + (row_h - (tb[3] - tb[1])) // 2),
                  label, fill=(220, 230, 240), font=font)
        ry += row_h


def annotate_image(
    image_bytes: bytes,
    defects: list[dict],
    inventory: dict | None = None,
) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    W_orig, H_orig = img.size

    # ── Pass 1: Magenta polygon fills ────────────────────────────────────────
    overlay = Image.new("RGBA", (W_orig, H_orig), (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)

    for d in defects:
        if (d.get("geometry") or "").lower() not in ("polygon", "area"):
            continue
        pts = _parse_pts(d.get("points", []), W_orig, H_orig)
        if len(pts) < 3:
            continue
        smooth = _catmull_rom(pts, steps=12)
        if len(smooth) >= 3:
            ov_draw.polygon(smooth, fill=(*MAGENTA, 25))   # outer glow
        ov_draw.polygon(smooth, fill=(*MAGENTA, 75))        # inner fill

    # Blur for organic painted look
    overlay_blurred = overlay.filter(ImageFilter.GaussianBlur(radius=1.5))
    img = Image.alpha_composite(img, overlay_blurred)

    # ── Pass 2: 3× supersampled line drawing ─────────────────────────────────
    SCALE = 3
    W, H  = W_orig * SCALE, H_orig * SCALE
    big   = img.convert("RGB").resize((W, H), Image.LANCZOS)
    draw  = ImageDraw.Draw(big)
    base  = max(1.5, W / 1800)

    for d in defects:
        pts = _parse_pts(d.get("points", []), W, H)
        if len(pts) < 2:
            continue

        color  = _crack_color(d)
        lw     = _crack_width(d, base)
        geo    = (d.get("geometry") or "polyline").lower()
        smooth = _catmull_rom(pts, steps=16)

        is_poly = geo in ("polygon", "area") and len(smooth) >= 3
        stroke_pts = smooth + [smooth[0]] if is_poly else smooth

        # Draw directly: thin black border then bright color on top
        draw.line(stroke_pts, fill=(0, 0, 0), width=lw + 4)
        draw.line(stroke_pts, fill=color, width=lw)

    # ── Pass 3: Downsample with anti-aliasing ─────────────────────────────────
    out = big.resize((W_orig, H_orig), Image.LANCZOS)

    # ── Pass 4: Minimal legend ────────────────────────────────────────────────
    _draw_minimal_legend(out)

    buf = io.BytesIO()
    out.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def resize_for_api(image_bytes: bytes, max_bytes: int = 4_000_000) -> tuple[bytes, str]:
    if len(image_bytes) <= max_bytes:
        img  = Image.open(io.BytesIO(image_bytes))
        fmt  = img.format or "JPEG"
        mime = f"image/{fmt.lower()}"
        return image_bytes, "image/jpeg" if mime == "image/jpg" else mime
    img   = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    scale = (max_bytes / len(image_bytes)) ** 0.5
    img   = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    buf   = io.BytesIO()
    img.save(buf, "JPEG", quality=85, optimize=True)
    return buf.getvalue(), "image/jpeg"
