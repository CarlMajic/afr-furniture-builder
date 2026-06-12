"""
AFR Furniture Builder — branding utilities.

Downloads the AFR logo from their CDN on first use and caches it alongside
the addon.  Falls back to a programmatic badge icon if the download fails.
Call load_icons() on register and unload_icons() on unregister.
"""

import bpy
import math
import os
import re
import urllib.request

# ── Brand colours (sRGB floats, used for programmatic icons) ───────────────
BLUE  = (0.271, 0.455, 0.729, 1.0)   # #4574BA — header blue
GOLD  = (0.784, 0.659, 0.251, 1.0)   # #C8A840 — accent gold
WHITE = (1.0,   1.0,   1.0,   1.0)

# ── Logo candidate URLs (tried in order) ──────────────────────────────────
_LOGO_CANDIDATES = [
    "https://www.afrevents.com/wp-content/themes/afrevents/images/afr-events-logo.png",
    "https://www.afrevents.com/wp-content/themes/afr/images/afr-events-logo.png",
    "https://www.afrevents.com/wp-content/themes/afrevents/img/logo.png",
    "https://www.afrevents.com/images/afr-logo.png",
    "https://www.afrevents.com/img/afr-logo.png",
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
    return (
        len(data) > 2000
        and (data[:8] == b"\x89PNG\r\n\x1a\n" or data[:3] == b"\xff\xd8\xff")
    )


def _fetch_logo():
    """Try to download the AFR logo; return local path or None."""
    path = _cache_path()
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return path

    candidates = list(_LOGO_CANDIDATES)

    # Try to find the real logo URL by scraping the homepage
    try:
        req = urllib.request.Request("https://www.afrevents.com/", headers=_HEADERS)
        with urllib.request.urlopen(req, timeout=3) as resp:
            html = resp.read().decode("utf-8", errors="replace")
        patterns = [
            r'<img[^>]+class=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
            r'<img[^>]+src=["\']([^"\']+)["\'][^>]+class=["\'][^"\']*logo[^"\']*["\']',
            r'<img[^>]+alt=["\'][^"\']*logo[^"\']*["\'][^>]+src=["\']([^"\']+)["\']',
        ]
        for pat in patterns:
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


# ── Programmatic icon generators ───────────────────────────────────────────

def _badge(size=32):
    """Blue circle with a gold border ring — fallback logo icon."""
    pixels = []
    cx = cy = size / 2.0
    r_outer = size / 2.0 - 0.5
    r_gold  = r_outer - max(2, size // 10)
    for row in range(size):
        for col in range(size):
            dx = col - cx + 0.5
            dy = row - cy + 0.5
            d  = math.sqrt(dx * dx + dy * dy)
            if d > r_outer:
                pixels += [0.0, 0.0, 0.0, 0.0]  # transparent
            elif d > r_gold:
                pixels += list(GOLD)             # gold ring
            else:
                pixels += list(BLUE)             # blue fill
    return pixels


# ── Preview collection ─────────────────────────────────────────────────────

_pcoll = None


def load_icons():
    global _pcoll
    if _pcoll is not None:
        return

    _pcoll = bpy.utils.previews.new()

    logo_path = _fetch_logo()
    if logo_path:
        try:
            _pcoll.load("afr_logo", logo_path, "IMAGE")
        except Exception:
            logo_path = None

    if not logo_path:
        t = _pcoll.new("afr_logo")
        t.image_size = (32, 32)
        t.image_pixels_float = _badge(32)


def unload_icons():
    global _pcoll
    if _pcoll is not None:
        bpy.utils.previews.remove(_pcoll)
        _pcoll = None


def icon(name="afr_logo"):
    """Return the icon_value for a branding icon, or 0 if unavailable."""
    if _pcoll is None:
        return 0
    thumb = _pcoll.get(name)
    return thumb.icon_id if thumb else 0
