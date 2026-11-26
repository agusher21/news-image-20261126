#!/usr/bin/env python3
"""
Generate the news-image-20261126 entry: a 1024x1024 newspaper front page
summing up Thursday 26 November 2026's world news.

Layout contract (every element owns a fixed box; nothing may cross a box edge):
  masthead 40 | dateline 22 | stat strip 34 | 3 lead panels 180
  | UTC ribbon 68 | 12-card grid 4x84 | world map 120 | ALSO list 134
  | DATE CHECK footer 32. Gaps of 6px between sections, 10px page margin.
Scenes are drawn on their own RGBA layer exactly the size of their picture
box, then pasted — so no scene drawing can ever touch text. Scenes carry
no text at all (one exception: the 490,334 figure, which fits inside its
own box). Region chips use a lightened solid fill (PIL ignores alpha on
RGB images, which made the old chips solid bars with invisible text).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

# ─── Constants ──────────────────────────────────────────────────────────────
W, H = 1024, 1024
BG = "#faf8f0"
INK = "#1a1a1a"
INK_LIGHT = "#3a3a3a"
ACCENT_RED = "#c00000"
ACCENT_BLUE = "#003366"
REGION_COLORS = {
    "North America": "#1f77b4",
    "South America": "#2ca02c",
    "Europe": "#ff7f0e",
    "Africa": "#d62728",
    "Middle East": "#9467bd",
    "South Asia": "#8c564b",
    "East Asia": "#e377c2",
    "Southeast Asia": "#7f7f7f",
    "Oceania": "#17becf",
}
STATUS_COLORS = {
    "REPORTED": "#1f77b4",
    "CONFIRMED": "#2ca02c",
    "CLAIM": "#ff7f0e",
    "ONGOING": "#9467bd",
    "OFFICIAL": "#d62728",
    "FORECAST": "#17becf",
}
STATUS_BG = {
    "REPORTED": "#d6eaff",
    "CONFIRMED": "#d6ffe0",
    "CLAIM": "#ffe6d6",
    "ONGOING": "#f0e6ff",
    "OFFICIAL": "#ffd6d6",
    "FORECAST": "#e6f9ff",
}

# ─── Font loading ───────────────────────────────────────────────────────────
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


FONTS = {
    "masthead": load_font(32, bold=True),
    "dateline": load_font(15, bold=True),
    "stat": load_font(14, bold=True),
    "stat_label": load_font(9),
    "lead_num": load_font(26, bold=True),
    "lead_kicker": load_font(12, bold=True),
    "lead_deck": load_font(9),
    "lead_source": load_font(8),
    "ribbon_title": load_font(8, bold=True),
    "ribbon_time": load_font(7),
    "ribbon_event": load_font(8, bold=True),
    "card_num": load_font(16, bold=True),
    "card_kicker": load_font(9, bold=True),
    "card_deck": load_font(7),
    "card_source": load_font(7),
    "map_title": load_font(10, bold=True),
    "map_pin": load_font(7, bold=True),
    "also_title": load_font(9, bold=True),
    "also_item": load_font(7),
    "datecheck_title": load_font(8, bold=True),
    "datecheck_item": load_font(7),
    "scene_num": load_font(8, bold=True),
}

# ─── Story Data ─────────────────────────────────────────────────────────────
class Story(NamedTuple):
    num: int
    kicker: str
    deck: str
    source: str
    status: str
    region: str
    utc_hour: int | None = None
    lat: float | None = None
    lon: float | None = None
    is_lead: bool = False
    is_card: bool = False
    is_also: bool = False


# Kickers are kept short on purpose: every lead kicker fits one line at
# 12pt bold in 314px, every card kicker fits one line at 9pt bold in 261px.
LEADS = [
    Story(num=1, kicker="Macy's 100th Thanksgiving Parade",
          deck="Nor'easter forces postponement to Saturday; 100 inflatables, 81.5m Americans travelling",
          source="AP", status="REPORTED", region="North America", utc_hour=13, lat=40.75, lon=-73.98, is_lead=True),
    Story(num=2, kicker="India Marks 18 Years Since 26/11",
          deck="Mumbai commemorates 2008 terror siege; 77th Constitution Day adds 6,000 IIT seats",
          source="Reuters", status="OFFICIAL", region="South Asia", utc_hour=6, lat=19.07, lon=72.87, is_lead=True),
    Story(num=3, kicker="Chess Title Game 3: Gukesh vs Sindarov",
          deck="Geneva match tied 1-1 after three games; Indian teen eyes history",
          source="AFP", status="CONFIRMED", region="Europe", utc_hour=14, lat=46.20, lon=6.14, is_lead=True),
]

CARDS = [
    Story(num=4, kicker="Houthis Claim Ras Tanura Refinery Strike",
          deck="Brent crude tops $94; Saudi denies damage; dating disputed — CLAIM only",
          source="Al Jazeera", status="CLAIM", region="Middle East", utc_hour=8, lat=26.65, lon=50.15, is_card=True),
    Story(num=5, kicker="Two Tankers Hit Mines in Strait of Hormuz",
          deck="Crew evacuated; shipping lanes disrupted; investigation under way",
          source="Reuters", status="REPORTED", region="Middle East", utc_hour=10, lat=26.56, lon=56.25, is_card=True),
    Story(num=6, kicker="Israeli Strike Kills Hamas Security Chief",
          deck="Senior operative eliminated in Gaza; IDF confirms operation",
          source="BBC", status="CONFIRMED", region="Middle East", utc_hour=4, lat=31.50, lon=34.46, is_card=True),
    Story(num=7, kicker="Ukraine Hits 5 Russian Jets at Savasleyka",
          deck="Drone strike deep inside Russia; Kyiv claims major blow to bomber fleet",
          source="Reuters", status="CLAIM", region="Europe", utc_hour=2, lat=55.68, lon=42.50, is_card=True),
    Story(num=8, kicker="Russian Drones Kill 7 in Kyiv",
          deck="Overnight barrage hits residential districts; air defences intercept most",
          source="AP", status="CONFIRMED", region="Europe", utc_hour=1, lat=50.45, lon=30.52, is_card=True),
    Story(num=9, kicker="Leaked Data: 490,334 Russian War Dead",
          deck="Mediazona/BBC analysis of probate records; Moscow silent",
          source="BBC", status="REPORTED", region="Europe", utc_hour=12, lat=55.75, lon=37.61, is_card=True),
    Story(num=10, kicker="US Proposes Tariffs on 14 Partners",
          deck="USTR announces sweeping review; China faces 20%; allies also targeted",
          source="Reuters", status="OFFICIAL", region="North America", utc_hour=16, lat=38.90, lon=-77.03, is_card=True),
    Story(num=11, kicker="Bangladesh Garment Wage Up 36%",
          deck="Minimum wage raised to Tk 17,000 after months of worker protests",
          source="AFP", status="OFFICIAL", region="South Asia", utc_hour=5, lat=23.81, lon=90.41, is_card=True),
    Story(num=12, kicker="Shenzhou-24: First Pakistani in Space",
          deck="Muhammad Zeeshan Ali reaches Tiangong; China-Pakistan space ties deepen",
          source="Xinhua", status="CONFIRMED", region="East Asia", utc_hour=3, lat=40.00, lon=116.00, is_card=True),
    Story(num=13, kicker="Cairo Tanker Fire Kills 30-31",
          deck="Fuel truck explosion in dense neighbourhood; dozens injured",
          source="AP", status="CONFIRMED", region="Africa", utc_hour=18, lat=30.04, lon=31.23, is_card=True),
    Story(num=14, kicker="Colombia Frees 25 Hostages in Cartagena",
          deck="Military rescue after weeks of negotiation; ELN captives released",
          source="Reuters", status="CONFIRMED", region="South America", utc_hour=20, lat=10.39, lon=-75.48, is_card=True),
    Story(num=15, kicker="Solomon Islands-Australia Pact ($740m)",
          deck="Canberra commits policing and infrastructure; Beijing watches closely",
          source="BBC", status="OFFICIAL", region="Oceania", utc_hour=22, lat=-9.43, lon=159.95, is_card=True),
]

ALSO_STORIES = [
    Story(num=16, kicker="Suez Canal Revenues Jump 101%", deck="Record tolls amid Red Sea diversions", source="Reuters", status="OFFICIAL", region="Middle East", is_also=True),
    Story(num=17, kicker="Nasdaq Slides ~4%, Nvidia -8.7%", deck="AI rally pauses on tariff fears", source="Bloomberg", status="REPORTED", region="North America", is_also=True),
    Story(num=18, kicker="US Jobless Claims Fall to 189,000", deck="Labour market stays tight", source="AP", status="OFFICIAL", region="North America", is_also=True),
    Story(num=19, kicker="US Q3 Growth 4.3%, Core PCE 3.3%", deck="Economy beats expectations", source="BEA", status="OFFICIAL", region="North America", is_also=True),
    Story(num=20, kicker="Dow Erases 1,100-Point Fall", deck="Volatile session ends flat", source="Reuters", status="REPORTED", region="North America", is_also=True),
    Story(num=21, kicker="Taiwan Shares Drop 1,926.92 Points", deck="Tech selloff hits TWSE", source="AFP", status="REPORTED", region="East Asia", is_also=True),
    Story(num=22, kicker="Petrobras Unveils $122bn Investment Plan", deck="Brazil energy giant targets 2028", source="Reuters", status="OFFICIAL", region="South America", is_also=True),
    Story(num=23, kicker="Venezuela External Debt Hits $237.5bn", deck="PDVSA restructuring stalls", source="Bloomberg", status="REPORTED", region="South America", is_also=True),
    Story(num=24, kicker="Kim Jong Un Calls for Wider Nuclear Deployment", deck="KCNA reports strategic shift", source="KCNA", status="CLAIM", region="East Asia", is_also=True),
    Story(num=25, kicker="Gulf of Mexico Plane Crash Kills 6", deck="Private jet goes down off Texas coast", source="AP", status="CONFIRMED", region="North America", is_also=True),
    Story(num=26, kicker="Virgin Australia Staff Strike Hits 4 Airports", deck="Ground crew walk out over pay", source="ABC", status="ONGOING", region="Oceania", is_also=True),
    Story(num=27, kicker="Bank of Korea Holds Rates Steady", deck="Inflation easing but growth concerns", source="Yonhap", status="OFFICIAL", region="East Asia", is_also=True),
    Story(num=28, kicker="EU Approves EUR50bn Ukraine Aid Package", deck="Hungary drops veto after concessions", source="Reuters", status="OFFICIAL", region="Europe", is_also=True),
    Story(num=29, kicker="South Africa GDP Contracts 0.3%", deck="Load-shedding weighs on output", source="Stats SA", status="OFFICIAL", region="Africa", is_also=True),
    Story(num=30, kicker="Indonesia Elects New Parliament Speaker", deck="Prabowo ally takes gavel", source="Jakarta Post", status="CONFIRMED", region="Southeast Asia", is_also=True),
    Story(num=31, kicker="Nigeria Fuel Price Hike Sparks Protests", deck="NLC calls nationwide strike", source="Channels TV", status="ONGOING", region="Africa", is_also=True),
    Story(num=32, kicker="Mexico Supreme Court Decriminalises Abortion", deck="Landmark ruling for Latin America", source="El Universal", status="OFFICIAL", region="North America", is_also=True),
    Story(num=33, kicker="Turkey Inflation Dips to 47% YoY", deck="Central bank sees peak passed", source="Reuters", status="REPORTED", region="Middle East", is_also=True),
    Story(num=34, kicker="Philippines-US Base Access Deal Expands", deck="Four new EDCA sites agreed", source="Inquirer", status="OFFICIAL", region="Southeast Asia", is_also=True),
    Story(num=35, kicker="Kenya Police Deploy to Haiti (UN Mission)", deck="First contingent arrives Port-au-Prince", source="AFP", status="CONFIRMED", region="Africa", is_also=True),
    Story(num=36, kicker="Chile Wildfires Kill 11, Destroy 5,000ha", deck="Valparaiso region under red alert", source="Reuters", status="CONFIRMED", region="South America", is_also=True),
    Story(num=37, kicker="Vietnam GDP Growth 6.8% in Q3", deck="Manufacturing export surge", source="VnExpress", status="OFFICIAL", region="Southeast Asia", is_also=True),
    Story(num=38, kicker="Iraq Awards Major Gas Contracts to TotalEnergies", deck="Basra fields development", source="AP", status="OFFICIAL", region="Middle East", is_also=True),
    Story(num=39, kicker="New Zealand Cuts Rates to 4.75%", deck="RBNZ signals further easing", source="Bloomberg", status="OFFICIAL", region="Oceania", is_also=True),
    Story(num=40, kicker="Canada Adds 25,000 Jobs in October", deck="Unemployment holds at 6.5%", source="StatCan", status="OFFICIAL", region="North America", is_also=True),
]

ALL_STORIES = LEADS + CARDS + ALSO_STORIES

# UTC Ribbon events: (hour, short label). Labels are short on purpose — the
# old 8 long chips in one row overlapped into one unreadable red band.
# Row A (above the line): hours 1, 3, 5, 10. Row B (below): 2, 4, 8, 14.
UTC_EVENTS_A = [
    (1, "Kyiv: 7 dead"),
    (3, "Shenzhou-24"),
    (5, "Wage +36%"),
    (10, "Hormuz mines"),
]
UTC_EVENTS_B = [
    (2, "Savasleyka"),
    (4, "Gaza chief"),
    (8, "Ras Tanura"),
    (14, "Chess Game 3"),
]

DATE_CHECK_EXCLUSIONS = [
    "Nvidia/Huang reinstatement (earlier)",
    "COP31 (future)",
    "Ukraine drones Libya (25 Nov)",
    "Belgium strike (25 Nov)",
    "Trump-Putin-Xi Shenzhen (fabricated)",
    "UNRWA worker (undated)",
    "BepiColombo Mercury orbit (21 Nov)",
    "Houthi Ras Tanura as confirmed fact (disputed dating)",
    "Murmansk governor detention (25 Nov)",
]

REGIONS = sorted({s.region for s in ALL_STORIES})
SOURCES = sorted({s.source for s in ALL_STORIES})

# ─── Drawing Helpers ────────────────────────────────────────────────────────

def lighten(hexcolor: str, frac: float = 0.75) -> str:
    """Mix a hex colour with white; returns a solid hex (no alpha)."""
    h = hexcolor.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * frac)
    g = int(g + (255 - g) * frac)
    b = int(b + (255 - b) * frac)
    return f"#{r:02x}{g:02x}{b:02x}"


def draw_status_chip(draw, x, y, text, font, status):
    color = STATUS_COLORS.get(status, INK)
    bg = STATUS_BG.get(status, "#eeeeee")
    padding = 3
    tw = draw.textlength(text, font=font)
    w = tw + 2 * padding
    h = font.size + 2 * padding
    draw.rounded_rectangle((x, y, x + w, y + h), radius=3, fill=bg, outline=color, width=1)
    draw.text((x + padding, y + padding - 1), text, font=font, fill=color)
    return w


def draw_region_chip(draw, x, y, text, font):
    color = REGION_COLORS.get(text, INK)
    padding = 3
    tw = draw.textlength(text, font=font)
    w = tw + 2 * padding
    h = font.size + 2 * padding
    draw.rounded_rectangle((x, y, x + w, y + h), radius=2, fill=lighten(color, 0.8), outline=color, width=1)
    draw.text((x + padding, y + padding - 1), text, font=font, fill=color)
    return w


def wrap_text(draw, text: str, font, max_width: int, max_lines: int = 2) -> list[str]:
    """Greedy wrap with widow control: a 2-line wrap never strands one short
    word alone on the last line — pull a word back from the line above."""
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        test = " ".join(current + [w])
        if draw.textlength(test, font=font) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
                if len(lines) >= max_lines:
                    break
            current = [w]
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    lines = lines[:max_lines]
    if len(lines) == 2:
        last = lines[1].split()
        first = lines[0].split()
        if len(last) == 1 and len(last[0]) <= 7 and len(first) > 1:
            moved = first[-1]
            new_first = " ".join(first[:-1])
            new_last = moved + " " + lines[1]
            if draw.textlength(new_last, font=font) <= max_width:
                lines = [new_first, new_last]
    return lines


def truncate(draw, text: str, font, max_width: int) -> str:
    """Cut text to fit max_width, ending with an ellipsis. Returns text
    unchanged when it already fits."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1].rstrip()
    return text + "…"

# ─── Drawn Scenes ───────────────────────────────────────────────────────────
# Every scene paints onto its own transparent RGBA layer exactly (w, h).
# Anything drawn past the layer edge is clipped by PIL, so a scene can
# never touch neighbouring text. Scenes carry NO text — the one exception
# is the "490,334" figure, which is the story itself and fits its box.
# All coordinates are fractions of the layer size, clamped inside [1, w-1].

def _cl(v, lo, hi):
    return max(lo, min(hi, v))


def draw_scene_layer(w: int, h: int, scene_type: str) -> Image.Image:
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = w // 2, h // 2
    u = min(w, h)  # unit: scene scale

    if scene_type == "parade":
        # Three balloons drifting over a skyline band.
        for bx, by, br, color in [
            (w * 0.22, h * 0.28, u * 0.13, "#e74c3c"),
            (w * 0.50, h * 0.20, u * 0.16, "#3498db"),
            (w * 0.78, h * 0.30, u * 0.12, "#f1c40f"),
        ]:
            bx, by = _cl(bx, br + 1, w - br - 1), _cl(by, br + 1, h - br - 1)
            d.ellipse((bx - br, by - br, bx + br, by + br), fill=color, outline="#2c2c2c", width=1)
            d.line((bx, by + br, bx, _cl(by + br + 7, 0, h - 1)), fill="#2c2c2c", width=1)
        band_y = int(h * 0.72)
        d.rectangle((2, band_y, w - 2, h - 2), fill="#5a5a5a")
        for bx in range(4, w - 10, max(12, w // 9)):
            bh = int(h * 0.10 + (bx % 3) * h * 0.04)
            d.rectangle((bx, band_y - bh, bx + max(8, w // 12), band_y), fill="#3d3d3d")
            for wx in range(bx + 2, bx + max(8, w // 12) - 2, 4):
                d.rectangle((wx, band_y - bh + 2, wx + 1, band_y - 2), fill="#ffe9a8")

    elif scene_type == "india":
        # Tricolour band across the top, chakra at its centre, arch below.
        stripe = max(4, int(h * 0.16))
        d.rectangle((2, 2, w - 2, 2 + stripe), fill="#ff9933")
        d.rectangle((2, 2 + stripe, w - 2, 2 + 2 * stripe), fill="#ffffff")
        d.rectangle((2, 2 + 2 * stripe, w - 2, 2 + 3 * stripe), fill="#138808")
        chakra_y = 2 + stripe + stripe // 2
        d.ellipse((cx - 4, chakra_y - 4, cx + 4, chakra_y + 4), outline="#000080", width=1)
        # Gateway arch under the flag.
        ay = 2 + 3 * stripe + int(h * 0.10)
        ar_w, ar_h = int(w * 0.30), int(h * 0.30)
        d.arc((cx - ar_w, ay, cx + ar_w, ay + ar_h), start=180, end=360, fill="#8b4513", width=max(2, u // 14))
        d.arc((cx - ar_w * 0.7, ay + ar_h * 0.25, cx + ar_w * 0.7, ay + ar_h), start=180, end=360, fill="#a0522d", width=max(1, u // 20))
        base_y = ay + ar_h
        d.rectangle((2, base_y, w - 2, h - 2), fill="#444444")
        for wx in range(6, w - 4, max(6, w // 14)):
            d.rectangle((wx, base_y + 2, wx + 2, h - 3), fill="#777777")

    elif scene_type == "chess":
        # 8x8 board, centred, with two kings and two small clocks.
        sq = max(5, (h - 4) // 8)
        side = sq * 8
        bx, by = (w - side) // 2, (h - side) // 2
        for row in range(8):
            for col in range(8):
                color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                d.rectangle((bx + col * sq, by + row * sq, bx + (col + 1) * sq, by + (row + 1) * sq), fill=color)
        kx, ky = bx + 3 * sq + sq // 2, by + sq // 2
        d.ellipse((kx - 4, ky - 3, kx + 4, ky + sq // 2), fill="#ffffff", outline="#333333", width=1)
        d.polygon([(kx, ky - 6), (kx - 3, ky - 1), (kx + 3, ky - 1)], fill="#ffd700")
        kx2, ky2 = bx + 4 * sq + sq // 2, by + 7 * sq + sq // 2
        d.ellipse((kx2 - 4, ky2 - sq // 2, kx2 + 4, ky2 + 3), fill="#1a1a1a", outline="#333333", width=1)
        d.polygon([(kx2, ky2 - 6), (kx2 - 3, ky2 - 1), (kx2 + 3, ky2 - 1)], fill="#ffd700")

    elif scene_type == "houthi":
        # Refinery: base block, three stacks, flame above the middle stack.
        d.rectangle((w * 0.15, h * 0.55, w * 0.85, h * 0.92), fill="#333333")
        for i, px in enumerate([w * 0.25, w * 0.48, w * 0.71]):
            d.rectangle((px, h * 0.32, px + max(3, w * 0.06), h * 0.55), fill="#222222")
        fx = w * 0.51
        d.polygon([(fx, h * 0.10), (fx - w * 0.10, h * 0.32), (fx + w * 0.10, h * 0.32)], fill="#e74c3c")
        d.polygon([(fx, h * 0.20), (fx - w * 0.06, h * 0.32), (fx + w * 0.06, h * 0.32)], fill="#f39c12")

    elif scene_type == "tanker":
        # Two hulls on waves, one explosion star between them.
        for tx in [w * 0.08, w * 0.52]:
            d.rectangle((tx, h * 0.45, tx + w * 0.38, h * 0.62), fill="#444444")
            d.rectangle((tx + w * 0.08, h * 0.32, tx + w * 0.28, h * 0.45), fill="#555555")
        ex, ey = w * 0.50, h * 0.30
        r = max(4, u * 0.10)
        d.ellipse((ex - r, ey - r, ex + r, ey + r), fill="#e74c3c")
        d.polygon([(ex, ey - r - 3), (ex - 2, ey), (ex + 2, ey)], fill="#f39c12")
        for wx in range(2, w - 6, max(8, w // 8)):
            d.arc((wx, h * 0.66, wx + max(8, w // 8), h * 0.82), start=180, end=360, fill="#3498db", width=1)

    elif scene_type == "gaza":
        # Three blocks with lit windows, small flag mast on the middle one.
        for i, bx in enumerate([w * 0.08, w * 0.38, w * 0.68]):
            bw = w * 0.24
            bh = h * (0.42 + (i % 2) * 0.12)
            by = h * 0.88 - bh
            d.rectangle((bx, by, bx + bw, h * 0.88), fill="#555555")
            for wx in range(int(bx) + 2, int(bx + bw) - 2, max(4, w // 14)):
                d.rectangle((wx, by + 2, wx + 1, h * 0.86), fill="#ffcc00")
        d.line((w * 0.50, 2, w * 0.50, h * 0.30), fill="#e74c3c", width=max(1, w // 40))
        d.polygon([(w * 0.50, 2), (w * 0.50 - 6, 10), (w * 0.50 + 6, 10)], fill="#e74c3c")

    elif scene_type == "ukraine":
        # Three aircraft silhouettes in formation, radar dish below.
        for rel_x in [-0.32, 0.0, 0.32]:
            px = cx + rel_x * w
            hw = max(6, w * 0.11)
            d.polygon([(px, h * 0.22), (px - hw, h * 0.42), (px + hw, h * 0.42)], fill="#444444")
            d.rectangle((px - hw * 0.55, h * 0.32, px + hw * 0.55, h * 0.42), fill="#666666")
        rx, ry, rr = cx, h * 0.72, max(8, u * 0.16)
        d.ellipse((rx - rr, ry - rr * 0.6, rx + rr, ry + rr * 0.6), fill="#222222", outline="#444444", width=1)
        d.line((rx - rr, ry, rx + rr, ry), fill="#222222", width=2)

    elif scene_type == "kyiv":
        # Night skyline with three smoke puffs above it.
        for i, bx in enumerate([w * 0.06, w * 0.36, w * 0.66]):
            bw = w * 0.26
            bh = h * (0.40 + (i % 2) * 0.10)
            d.rectangle((bx, h * 0.90 - bh, bx + bw, h * 0.90), fill="#444444")
        for dx in [w * 0.19, w * 0.50, w * 0.80]:
            r = max(4, u * 0.09)
            d.ellipse((dx - r, h * 0.10, dx + r, h * 0.10 + 2 * r), fill="#1a1a1a", outline="#333333", width=1)

    elif scene_type == "casualties":
        # White card, red header band, the figure 490,334 inside the band.
        d.rectangle((2, 2, w - 2, h - 2), fill="#ffffff", outline="#cccccc", width=1)
        d.rectangle((3, 3, w - 3, int(h * 0.38)), fill="#e74c3c")
        num = "490,334"
        font = FONTS["scene_num"]
        tw = d.textlength(num, font=font)
        if tw > w - 8:
            font = load_font(7, bold=True)
            tw = d.textlength(num, font=font)
        d.text(((w - tw) / 2, int(h * 0.38) // 2 - 4), num, font=font, fill="#ffffff")
        d.rectangle((3, int(h * 0.38) + 2, w - 3, int(h * 0.68)), fill="#f0f0f0")
        d.rectangle((3, int(h * 0.68) + 2, w - 3, h - 3), fill="#e6e6e6")

    elif scene_type == "tariffs":
        # A document with a red tariff band across its lower third.
        d.rectangle((w * 0.18, h * 0.08, w * 0.82, h * 0.92), fill="#f5f5f5", outline="#cccccc", width=1)
        d.ellipse((w * 0.30, h * 0.10, w * 0.70, h * 0.34), fill="#ffffff", outline="#cccccc", width=1)
        for i, ly in enumerate([h * 0.42, h * 0.52, h * 0.62]):
            d.line((w * 0.26, ly, w * 0.74, ly), fill="#bbbbbb", width=1)
        d.rectangle((w * 0.18, h * 0.72, w * 0.82, h * 0.88), fill="#e74c3c")

    elif scene_type == "bangladesh":
        # Factory with sawtooth roof and a green growth arrow rising.
        d.rectangle((w * 0.10, h * 0.45, w * 0.90, h * 0.92), fill="#dddddd", outline="#999999", width=1)
        for wx in range(int(w * 0.14), int(w * 0.86), max(7, w // 10)):
            d.rectangle((wx, h * 0.52, wx + max(4, w // 14), h * 0.88), fill="#bbbbbb")
        d.rectangle((w * 0.10, h * 0.30, w * 0.90, h * 0.45), fill="#2ca02c")
        ax = w * 0.50
        d.polygon([(ax, h * 0.06), (ax - w * 0.12, h * 0.22), (ax - w * 0.04, h * 0.22),
                   (ax - w * 0.04, h * 0.28), (ax + w * 0.04, h * 0.28), (ax + w * 0.04, h * 0.22),
                   (ax + w * 0.12, h * 0.22)], fill="#ffffff")

    elif scene_type == "shenzhou":
        # Rocket: central body, nose cone, two side boosters, flame, stars.
        bw = max(6, w * 0.20)
        d.rectangle((cx - bw // 2, h * 0.18, cx + bw // 2, h * 0.72), fill="#444444", outline="#666666", width=1)
        d.polygon([(cx - bw // 2, h * 0.18), (cx + bw // 2, h * 0.18), (cx, h * 0.06)], fill="#e74c3c")
        for sx in [cx - bw // 2 - max(4, w * 0.10), cx + bw // 2]:
            d.rectangle((sx, h * 0.30, sx + max(4, w * 0.10), h * 0.72), fill="#222222")
        d.polygon([(cx, h * 0.92), (cx - bw * 0.45, h * 0.72), (cx + bw * 0.45, h * 0.72)], fill="#f39c12")
        for sx, sy in [(w * 0.12, h * 0.14), (w * 0.88, h * 0.20), (w * 0.82, h * 0.08)]:
            d.ellipse((sx - 1, sy - 1, sx + 1, sy + 1), fill="#ffd700")

    elif scene_type == "cairo":
        # Building with three flame tongues above its roof.
        d.rectangle((w * 0.20, h * 0.55, w * 0.80, h * 0.92), fill="#333333")
        d.rectangle((w * 0.26, h * 0.42, w * 0.74, h * 0.55), fill="#222222")
        for fx in [w * 0.32, w * 0.50, w * 0.68]:
            d.polygon([(fx, h * 0.12), (fx - w * 0.09, h * 0.42), (fx + w * 0.09, h * 0.42)], fill="#e74c3c")
            d.polygon([(fx, h * 0.24), (fx - w * 0.05, h * 0.42), (fx + w * 0.05, h * 0.42)], fill="#f39c12")

    elif scene_type == "colombia":
        # Green field, three freed figures walking.
        d.rectangle((w * 0.06, h * 0.55, w * 0.94, h * 0.92), fill="#2c5f2d", outline="#1e3d1e", width=1)
        for px in [w * 0.22, w * 0.50, w * 0.78]:
            r = max(3, u * 0.07)
            d.ellipse((px - r, h * 0.30, px + r, h * 0.30 + 2 * r), fill="#fdbcb4")
            d.rectangle((px - r * 1.2, h * 0.30 + 2 * r, px + r * 1.2, h * 0.55), fill="#2c5f2d")
        d.ellipse((w * 0.50, h * 0.06, w * 0.50 + 3, h * 0.06 + 3), fill="#ffd700")

    elif scene_type == "solomons":
        # Blue ocean disc, two green islands, two figures on the shore.
        r = max(8, u * 0.38)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#17becf", outline="#0a8a9e", width=1)
        d.ellipse((cx - r * 0.55, cy - r * 0.35, cx + r * 0.10, cy + r * 0.15), fill="#2ca02c")
        d.ellipse((cx + r * 0.15, cy - r * 0.45, cx + r * 0.60, cy - r * 0.05), fill="#2ca02c")
        for px in [cx - r * 0.30, cx + r * 0.30]:
            d.ellipse((px - 3, cy + r * 0.30, px + 3, cy + r * 0.30 + 6), fill="#fdbcb4")

    else:
        d.rectangle((1, 1, w - 1, h - 1), fill="#eeeeee", outline="#cccccc", width=1)

    return layer


def paste_scene(img: Image.Image, x: int, y: int, w: int, h: int, scene_type: str):
    """Paste a scene layer into its picture box; the layer is exactly the
    box size, so nothing can leak into neighbouring text."""
    layer = draw_scene_layer(w, h, scene_type)
    img.paste(layer, (x, y), layer)

# ─── Main Generation ────────────────────────────────────────────────────────
# Vertical budget (1024 total): masthead 40, dateline 22, stat 34+6,
# leads 180+6, ribbon 72+6, cards 4x84+3x6+6, map 120+6, ALSO 130,
# footer 32, 10px bottom margin. Every section owns its rows; text is
# placed at fixed y offsets with line pitches matched to font heights.

def generate() -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    warnings: list[str] = []

    padding = 10
    gap = 6
    content_w = W - 2 * padding
    y = 0

    # ═══ MASTHEAD ═══════════════════════════════════════════════════════════
    masthead_h = 40
    draw.rectangle((0, y, W, y + masthead_h), fill=ACCENT_RED)
    draw.text((W // 2, y + 21), "THE WORLD IN ONE DAY", font=FONTS["masthead"], fill="#ffffff", anchor="mm")
    y += masthead_h

    # Dateline
    dateline_h = 22
    draw.rectangle((0, y, W, y + dateline_h), fill=ACCENT_BLUE)
    draw.text((W // 2, y + 11), "THURSDAY 26 NOVEMBER 2026", font=FONTS["dateline"], fill="#ffffff", anchor="mm")
    y += dateline_h

    # ═══ BIG-NUMBER STAT STRIP (fixed-width cells, number above label) ═════
    stat_h = 34
    draw.rectangle((padding, y, W - padding, y + stat_h), fill="#f5f0e0", outline="#ddd8c8", width=1)
    stats = [
        ("40", "STORIES"), ("9", "REGIONS"), (str(len(SOURCES)), "SOURCES"),
        ("100th", "PARADE"), ("81.5m", "TRAVELLERS"), ("490,334", "RUSSIAN DEAD"),
        ("+36%", "WAGE HIKE"), ("$237.5bn", "VENEZUELA DEBT"), ("4.3%", "US Q3 GDP"),
    ]
    cell_w = content_w // len(stats)
    for i, (val, label) in enumerate(stats):
        cell_x = padding + i * cell_w
        cell_center = cell_x + cell_w // 2
        val_w = draw.textlength(val, font=FONTS["stat"])
        draw.text((cell_center - val_w // 2, y + 2), val, font=FONTS["stat"], fill=ACCENT_RED)
        label_w = draw.textlength(label, font=FONTS["stat_label"])
        draw.text((cell_center - label_w // 2, y + 19), label, font=FONTS["stat_label"], fill=INK_LIGHT)
    bar_y = y + stat_h - 2
    region_w = content_w // len(REGIONS)
    for i, region in enumerate(REGIONS):
        color = REGION_COLORS[region]
        draw.rectangle((padding + i * region_w, bar_y, padding + (i + 1) * region_w, y + stat_h), fill=color)
    y += stat_h + gap

    # ═══ THREE LEAD PANELS ══════════════════════════════════════════════════
    # Row plan inside each 180px panel: badge row 8..48, scene 50..114,
    # kicker 118 (1 line), deck 136+148 (2 lines), source 166.
    lead_h = 180
    lead_w = (content_w - 2 * gap) // 3
    lead_y = y
    scene_types = ["parade", "india", "chess"]

    for i, lead in enumerate(LEADS):
        lx = padding + i * (lead_w + gap)
        ly = lead_y
        draw.rectangle((lx, ly, lx + lead_w, ly + lead_h), fill="#fdfbf5", outline="#e0d8c8", width=1)

        badge_r = 20
        draw.ellipse((lx + 10, ly + 10, lx + 10 + badge_r * 2, ly + 10 + badge_r * 2), fill=ACCENT_RED)
        draw.text((lx + 10 + badge_r, ly + 10 + badge_r), str(lead.num), font=FONTS["lead_num"], fill="#ffffff", anchor="mm")

        draw_region_chip(draw, lx + 55, ly + 8, lead.region, FONTS["stat_label"])
        draw_status_chip(draw, lx + lead_w - 80, ly + 8, lead.status, FONTS["lead_source"], lead.status)

        paste_scene(img, lx + 6, ly + 50, lead_w - 12, 64, scene_types[i])

        kicker = truncate(draw, lead.kicker, FONTS["lead_kicker"], lead_w - 16)
        if kicker != lead.kicker:
            warnings.append(f"lead {lead.num} kicker truncated")
        draw.text((lx + 8, ly + 118), kicker, font=FONTS["lead_kicker"], fill=INK)

        deck_lines = wrap_text(draw, lead.deck, FONTS["lead_deck"], lead_w - 16, max_lines=2)
        for j, line in enumerate(deck_lines):
            draw.text((lx + 8, ly + 136 + j * 12), line, font=FONTS["lead_deck"], fill=INK_LIGHT)

        draw.text((lx + 8, ly + 166), f"Source: {lead.source}", font=FONTS["lead_source"], fill=ACCENT_BLUE)

    y = lead_y + lead_h + gap

    # ═══ UTC RIBBON (THE TWIST) ═════════════════════════════════════════════
    # 72px band: title, row-A chips above the line, time ticks + labels,
    # row-B chips below the line. Short labels, staggered rows — the old
    # single row of 8 long chips overlapped into one red band.
    ribbon_h = 72
    draw.rectangle((padding, y, W - padding, y + ribbon_h), fill="#1a1a2e", outline="#0f0f1a", width=1)
    draw.text((padding + 6, y + 2), "THE DAY IN UTC", font=FONTS["ribbon_title"], fill="#ffffff")

    line_y = y + 36
    draw.line((padding + 6, line_y, W - padding - 6, line_y), fill="#444466", width=2)
    for hour in range(0, 24, 3):
        hx = padding + 6 + (hour / 23) * (W - 2 * padding - 12)
        draw.line((hx, line_y - 3, hx, line_y + 3), fill="#666688", width=1)
        draw.text((hx, line_y + 4), f"{hour:02d}:00", font=FONTS["ribbon_time"], fill="#aaaaaa", anchor="ma")

    def ribbon_chip(evt_hour, label, chip_y, point_down):
        hx = padding + 6 + (evt_hour / 23) * (W - 2 * padding - 12)
        chip_w = int(draw.textlength(label, FONTS["ribbon_event"]) + 10)
        chip_x = int(hx - chip_w // 2)
        chip_x = max(padding + 6, min(W - padding - 6 - chip_w, chip_x))
        chip_h = 15
        draw.rounded_rectangle((chip_x, chip_y, chip_x + chip_w, chip_y + chip_h), radius=4, fill="#e74c3c")
        draw.text((chip_x + 5, chip_y + 2), label, font=FONTS["ribbon_event"], fill="#ffffff")
        pcx = chip_x + chip_w // 2
        if point_down:
            draw.polygon([(pcx, line_y), (pcx - 4, chip_y + chip_h), (pcx + 4, chip_y + chip_h)], fill="#e74c3c")
        else:
            draw.polygon([(pcx, line_y), (pcx - 4, chip_y), (pcx + 4, chip_y)], fill="#e74c3c")

    for evt_hour, label in UTC_EVENTS_A:
        ribbon_chip(evt_hour, label, y + 13, point_down=True)
    for evt_hour, label in UTC_EVENTS_B:
        ribbon_chip(evt_hour, label, y + 51, point_down=False)

    y += ribbon_h + gap

    # ═══ 12 CARD GRID (3x4) ═════════════════════════════════════════════════
    # Row plan inside each 84px card: badge row 5..29, scene 29..79 (50x50),
    # kicker 29 (1 line, right of scene), deck 45+55 (2 lines), source 70.
    card_cols = 3
    card_rows = 4
    card_w = (content_w - (card_cols - 1) * gap) // card_cols
    card_h = 84
    grid_start_y = y
    card_scene_types = ["houthi", "tanker", "gaza", "ukraine", "kyiv", "casualties",
                        "tariffs", "bangladesh", "shenzhou", "cairo", "colombia", "solomons"]

    for idx, card in enumerate(CARDS):
        col = idx % card_cols
        row = idx // card_cols
        cx = padding + col * (card_w + gap)
        cy = grid_start_y + row * (card_h + gap)

        draw.rectangle((cx, cy, cx + card_w, cy + card_h), fill="#fdfbf5", outline="#e0d8c8", width=1)

        badge_r = 12
        draw.ellipse((cx + 5, cy + 5, cx + 5 + badge_r * 2, cy + 5 + badge_r * 2), fill=ACCENT_RED)
        draw.text((cx + 5 + badge_r, cy + 5 + badge_r), str(card.num), font=FONTS["card_num"], fill="#ffffff", anchor="mm")

        draw_region_chip(draw, cx + 33, cy + 5, card.region, FONTS["card_source"])
        draw_status_chip(draw, cx + card_w - 65, cy + 5, card.status, FONTS["card_source"], card.status)

        paste_scene(img, cx + 5, cy + 29, 50, 50, card_scene_types[idx])

        text_x = cx + 61
        text_w = card_w - 61 - 8
        kicker = truncate(draw, card.kicker, FONTS["card_kicker"], text_w)
        if kicker != card.kicker:
            warnings.append(f"card {card.num} kicker truncated")
        draw.text((text_x, cy + 29), kicker, font=FONTS["card_kicker"], fill=INK)

        deck_lines = wrap_text(draw, card.deck, FONTS["card_deck"], text_w, max_lines=2)
        for j, line in enumerate(deck_lines):
            draw.text((text_x, cy + 45 + j * 10), line, font=FONTS["card_deck"], fill=INK_LIGHT)

        draw.text((text_x, cy + 70), f"Source: {card.source}", font=FONTS["card_source"], fill=ACCENT_BLUE)

    y = grid_start_y + card_rows * (card_h + gap) + gap

    # ═══ WORLD MAP WITH PINS ════════════════════════════════════════════════
    # 120px section: title + a 94px-tall equirectangular map. The old 45px
    # map squashed the continents into one thin green strip.
    map_h = 120
    map_y = y
    draw.rectangle((padding, map_y, W - padding, map_y + map_h), fill="#e8f4f8", outline="#b0d0e0", width=1)
    draw.text((W // 2, map_y + 10), "WHERE IT HAPPENED", font=FONTS["map_title"], fill=ACCENT_BLUE, anchor="mm")

    map_left = padding + 18
    map_right = W - padding - 18
    map_top = map_y + 22
    map_bottom = map_y + map_h - 4
    map_w = map_right - map_left
    map_h_px = map_bottom - map_top

    def proj(lon, lat):
        x = map_left + (lon + 180) / 360 * map_w
        y = map_top + (82 - lat) / 140 * map_h_px
        return int(x), int(y)

    continents = [
        # North America
        [(-168, 66), (-150, 60), (-135, 58), (-125, 49), (-120, 38), (-110, 30),
         (-100, 25), (-90, 20), (-85, 15), (-80, 10), (-78, 8), (-85, 12),
         (-95, 16), (-100, 20), (-110, 24), (-120, 32), (-130, 40), (-145, 60),
         (-160, 58), (-168, 66)],
        # South America
        [(-80, 10), (-75, 5), (-70, -5), (-60, -10), (-55, -25), (-50, -35),
         (-60, -45), (-70, -52), (-75, -45), (-80, -30), (-82, -15), (-80, 10)],
        # Europe
        [(-10, 36), (-5, 44), (0, 48), (5, 55), (10, 58), (20, 60), (25, 55),
         (30, 50), (28, 45), (25, 40), (20, 38), (12, 42), (5, 40), (-2, 37), (-10, 36)],
        # Africa
        [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (30, 30), (35, 25),
         (40, 15), (48, 10), (50, 0), (45, -10), (40, -20), (35, -28), (25, -33),
         (15, -35), (10, -25), (5, -10), (0, 0), (-5, 5), (-10, 10), (-17, 15)],
        # Asia
        [(30, 70), (45, 68), (60, 68), (75, 72), (90, 75), (110, 76), (130, 72),
         (150, 70), (160, 65), (170, 60), (175, 55), (180, 50), (175, 40),
         (170, 35), (160, 30), (150, 35), (140, 40), (130, 35), (125, 30),
         (120, 25), (110, 20), (105, 10), (100, 5), (95, 10), (90, 20),
         (85, 25), (80, 30), (75, 25), (70, 20), (65, 25), (60, 25), (55, 28),
         (50, 30), (45, 35), (40, 40), (35, 45), (30, 50), (30, 70)],
        # Oceania
        [(113, -22), (120, -15), (130, -12), (140, -15), (145, -20), (150, -25),
         (150, -35), (145, -40), (140, -38), (135, -35), (130, -32), (125, -30),
         (120, -28), (115, -25), (113, -22)],
    ]

    for poly in continents:
        pts = [proj(lon, lat) for lon, lat in poly]
        pts = [(px, py) for px, py in pts if map_left <= px <= map_right and map_top <= py <= map_bottom]
        if len(pts) >= 3:
            draw.polygon(pts, fill="#a8d5a8", outline="#6bb86b", width=1)

    # Numbered pins. Stories cluster in the Middle East/Europe, so pins that
    # would land on top of each other are nudged apart (standard
    # cartographic practice) until their 12px circles no longer touch.
    placed: list[tuple[int, int]] = []
    for story in ALL_STORIES:
        if story.lat is not None and story.lon is not None:
            px, py = proj(story.lon, story.lat)
            px = max(map_left + 7, min(map_right - 7, px))
            py = max(map_top + 7, min(map_bottom - 7, py))
            for dx, dy in [(0, 0), (0, 14), (0, -14), (14, 0), (-14, 0),
                           (0, 28), (0, -28), (14, 14), (-14, 14), (14, -14), (-14, -14)]:
                nx = max(map_left + 7, min(map_right - 7, px + dx))
                ny = max(map_top + 7, min(map_bottom - 7, py + dy))
                if all((nx - ox) ** 2 + (ny - oy) ** 2 >= 14 ** 2 for ox, oy in placed):
                    px, py = nx, ny
                    break
            placed.append((px, py))
            r = 6
            draw.ellipse((px - r, py - r, px + r, py + r), fill=ACCENT_RED, outline="#8b0000", width=1)
            draw.text((px, py), str(story.num), font=FONTS["map_pin"], fill="#ffffff", anchor="mm")

    y += map_h + gap

    # ═══ ALSO LIST (16-40) ══════════════════════════════════════════════════
    # 3 columns x 9 rows, ONE line per item, fixed 12px row pitch. The old
    # 2-line items in 11px rows overlapped each other vertically.
    also_y = y
    footer_h = 32
    footer_y = H - footer_h - padding
    also_h = footer_y - also_y
    draw.rectangle((padding, also_y, W - padding, also_y + also_h), fill="#fdfbf5", outline="#e0d8c8", width=1)
    draw.text((padding + 6, also_y + 3), "ALSO ON THURSDAY 26 NOVEMBER", font=FONTS["also_title"], fill=ACCENT_RED)

    also_cols = 3
    also_rows = 9
    col_gap = 8
    col_w = (content_w - (also_cols - 1) * col_gap) // also_cols
    start_y = also_y + 16
    row_pitch = 12

    for i, story in enumerate(ALSO_STORIES):
        col = i // also_rows
        row = i % also_rows
        tx = padding + 6 + col * (col_w + col_gap)
        ty = start_y + row * row_pitch
        color = REGION_COLORS.get(story.region, INK)
        draw.ellipse((tx, ty + 2, tx + 5, ty + 7), fill=color)
        text = f"{story.num}. {story.kicker} · {story.source} · {story.status}"
        text = truncate(draw, text, FONTS["also_item"], col_w - 12)
        draw.text((tx + 9, ty), text, font=FONTS["also_item"], fill=INK)

    # ═══ DATE CHECK FOOTER - pinned to the bottom edge ══════════════════════
    draw.rectangle((padding, footer_y, W - padding, footer_y + footer_h), fill="#fff8f0", outline="#ffe0c0", width=1)
    draw.text((padding + 6, footer_y + 2), "DATE CHECK", font=FONTS["datecheck_title"], fill=ACCENT_RED)
    dc_text = "Excluded (not 26 Nov): " + "; ".join(DATE_CHECK_EXCLUSIONS)
    dc_lines = wrap_text(draw, dc_text, FONTS["datecheck_item"], content_w - 12, max_lines=2)
    for i, line in enumerate(dc_lines):
        draw.text((padding + 6, footer_y + 13 + i * 9), line, font=FONTS["datecheck_item"], fill=INK_LIGHT)

    # ═══ Final border ═══════════════════════════════════════════════════════
    draw.rectangle((0, 0, W - 1, H - 1), outline="#cccccc", width=1)

    out_path = Path("/home/hatch/workspace/makefun/news-image-20261126/out/entry.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    root_path = Path("/home/hatch/workspace/makefun/news-image-20261126/entry.png")
    img.save(root_path, "PNG", optimize=True)
    for wmsg in warnings:
        print(f"WARNING: {wmsg}")
    return out_path


def verify_image(path: Path) -> dict:
    img = Image.open(path)
    w, h = img.size
    size = path.stat().st_size
    sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "path": str(path),
        "width": w,
        "height": h,
        "size_bytes": size,
        "size_mib": size / (1024 * 1024),
        "sha256": sha256,
        "valid_dims": w == 1024 and h == 1024,
        "valid_size": size <= 1048576,
        "story_count": len(ALL_STORIES),
        "lead_count": len(LEADS),
        "card_count": len(CARDS),
        "also_count": len(ALSO_STORIES),
        "regions": len(REGIONS),
        "sources": len(SOURCES),
    }


if __name__ == "__main__":
    print("Generating entry.png...")
    out = generate()
    info = verify_image(out)
    print("\n=== VERIFICATION ===")
    for k, v in info.items():
        print(f"  {k}: {v}")
    print(f"\n✓ Image saved to {out}")
    print(f"✓ SHA256: {info['sha256']}")
    print(f"✓ Size: {info['size_bytes']} bytes ({info['size_mib']:.2f} MiB)")
    print(f"✓ Stories: {info['story_count']} ({info['lead_count']} leads + {info['card_count']} cards + {info['also_count']} also)")
    print(f"✓ Regions: {info['regions']}, Sources: {info['sources']}")
