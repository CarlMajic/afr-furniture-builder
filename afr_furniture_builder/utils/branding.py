"""AFR Furniture Builder — branding utilities."""

import bpy
import math
import os
import re
import urllib.request

# ── Brand colours ──────────────────────────────────────────────────────────
BLUE  = (0.271, 0.455, 0.729, 1.0)   # #4574BA
GOLD  = (0.784, 0.659, 0.251, 1.0)   # #C8A840

# ── CDN fallback URLs ──────────────────────────────────────────────────────
_LOGO_CANDIDATES = [
    "https://www.afrevents.com/wp-content/themes/afrevents/images/afr-events-logo.png",
    "https://www.afrevents.com/wp-content/themes/afr/images/afr-events-logo.png",
    "https://www.afrevents.com/images/afr-logo.png",
    "https://www.rentfurniture.com/wp-content/themes/afr/images/logo.png",
]
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "image/png,image/webp,image/jpeg,*/*;q=0.8",
}


def _addon_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _cache_path():
    return os.path.join(_addon_dir(), "_afr_logo_cache.png")

def _valid_image(data):
    return len(data) > 2000 and (
        data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff"
    )

def _fetch_logo():
    path = _cache_path()
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path
    candidates = list(_LOGO_CANDIDATES)
    try:
        req = urllib.request.Request("https://www.afrevents.com/", headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=3) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        for pat in [
            r'<img[^>]+class=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*logo[^"\']*["\']',
        ]:
            m = re.search(pat, html, re.I)
            if m:
                url = m.group(1)
                if not url.startswith("http"):
                    url = "https://www.afrevents.com" + url
                candidates.insert(0, url)
                break
    except Exception:
        pass
    for url in candidates:
        try:
            req = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = resp.read()
            if _valid_image(data):
                with open(path, "wb") as f:
                    f.write(data)
                return path
        except Exception:
            continue
    return None

def _remove_white_bg(thumb, threshold=0.90):
    try:
        w, h = thumb.image_size
        if w == 0 or h == 0:
            return
        pixels = list(thumb.image_pixels_float)
        for i in range(0, len(pixels), 4):
            if pixels[i] > threshold and pixels[i+1] > threshold and pixels[i+2] > threshold:
                pixels[i+3] = 0.0
        thumb.image_pixels_float = pixels
    except Exception as e:
        print(f"[AFR Branding] bg-removal error: {e}")


# ── Pixel-art icon helpers ─────────────────────────────────────────────────

def _px(buf, w, col, row, color):
    if 0 <= col < w and 0 <= row < w:
        i = (row * w + col) * 4
        buf[i:i+4] = list(color)

def _rect(buf, w, x1, y1, x2, y2, color):
    for r in range(max(0,y1), min(w,y2)):
        for c in range(max(0,x1), min(w,x2)):
            _px(buf, w, c, r, color)

def _circle(buf, w, cx, cy, radius, color):
    r2 = radius * radius
    for r in range(max(0, cy-radius-1), min(w, cy+radius+2)):
        for c in range(max(0, cx-radius-1), min(w, cx+radius+2)):
            if (c-cx+0.5)**2 + (r-cy+0.5)**2 <= r2:
                _px(buf, w, c, r, color)

def _empty(size):
    return [0.0] * (size * size * 4)


def _icon_cafe(size=32):
    """Top-down view: round table with four chairs."""
    buf = _empty(size)
    c = size // 2
    _circle(buf, size, c, c,  5, BLUE)           # table
    _circle(buf, size, c,    c-10, 3, BLUE)       # chair N
    _circle(buf, size, c,    c+10, 3, BLUE)       # chair S
    _circle(buf, size, c-10, c,    3, BLUE)       # chair W
    _circle(buf, size, c+10, c,    3, BLUE)       # chair E
    return buf


def _icon_lounge(size=32):
    """Side profile: sofa with coffee table."""
    buf = _empty(size)
    # sofa seat
    _rect(buf, size,  3, 18, 25, 26, BLUE)
    # sofa back (tall, left)
    _rect(buf, size,  3,  9,  9, 26, BLUE)
    # right arm
    _rect(buf, size, 21, 14, 26, 26, BLUE)
    # coffee table (gold, in front)
    _rect(buf, size, 26, 19, 31, 23, GOLD)
    _rect(buf, size, 27, 23, 30, 26, GOLD)       # table leg
    return buf


def _icon_bar(size=32):
    """Front view: tall bar table with two stools."""
    buf = _empty(size)
    # table top
    _rect(buf, size,  4,  7, 28, 11, BLUE)
    # table leg
    _rect(buf, size, 13, 11, 19, 27, BLUE)
    # left stool seat + leg
    _circle(buf, size, 5, 19, 4, GOLD)
    _rect(buf, size,  4, 23,  7, 28, GOLD)
    # right stool seat + leg
    _circle(buf, size, 27, 19, 4, GOLD)
    _rect(buf, size, 26, 23, 29, 28, GOLD)
    return buf


def _icon_dining(size=32):
    """Top-down view: rectangular dining table with chairs on long sides."""
    buf = _empty(size)
    # table top (rectangular, landscape)
    _rect(buf, size, 4, 11, 28, 21, BLUE)
    # front chairs (gold)
    _circle(buf, size,  9, 25, 3, GOLD)
    _circle(buf, size, 23, 25, 3, GOLD)
    # back chairs (gold)
    _circle(buf, size,  9,  7, 3, GOLD)
    _circle(buf, size, 23,  7, 3, GOLD)
    return buf


# ── Preview collection ─────────────────────────────────────────────────────

_pcoll = None


def load_icons():
    global _pcoll
    if _pcoll is not None:
        return
    _pcoll = bpy.utils.previews.new()

    # Main AFR logo
    logo_path = _fetch_logo()
    if logo_path:
        try:
            thumb = _pcoll.load("afr_logo", logo_path, "IMAGE")
            _remove_white_bg(thumb)
        except Exception as e:
            print(f"[AFR Branding] logo error: {e}")
            logo_path = None
    if not logo_path:
        # fallback: blue/gold badge
        t = _pcoll.new("afr_logo")
        t.image_size = (32, 32)
        import math as _m
        t.image_pixels_float = _icon_lounge(32)   # use lounge as generic badge

    # Category icons
    for name, fn in [("icon_cafe", _icon_cafe), ("icon_lounge", _icon_lounge), ("icon_bar", _icon_bar), ("icon_dining", _icon_dining)]:
        t = _pcoll.new(name)
        t.image_size = (32, 32)
        t.image_pixels_float = fn(32)


def unload_icons():
    global _pcoll
    if _pcoll is not None:
        bpy.utils.previews.remove(_pcoll)
        _pcoll = None


def icon(name="afr_logo"):
    if _pcoll is None:
        return 0
    thumb = _pcoll.get(name)
    return thumb.icon_id if thumb else 0


def draw_logo(layout, scale=5.0):
    """Draw the AFR logo centred in a panel row."""
    row = layout.row()
    row.alignment = 'CENTER'
    logo = icon("afr_logo")
    if logo:
        row.template_icon(icon_value=logo, scale=scale)
    else:
        row.label(text="AFR Furniture Builder")
