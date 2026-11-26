#!/usr/bin/env python3
"""
Generate the news-image-20261126 entry: a 1024x1024 newspaper front page
summing up Thursday 26 November 2026's world news.
"""

from __future__ import annotations

import math
import hashlib
from pathlib import Path
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

# ─── Constants ──────────────────────────────────────────────────────────────
W, H = 1024, 1024
BG = "#faf8f0"  # newsprint off-white
INK = "#1a1a1a"
INK_LIGHT = "#3a3a3a"
ACCENT_RED = "#c00000"
ACCENT_BLUE = "#003366"
ACCENT_GOLD = "#b8860b"
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
    """Load DejaVu Sans (bundled with most systems) or fallback."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


FONTS = {
    "masthead": load_font(34, bold=True),
    "dateline": load_font(17, bold=True),
    "standfirst": load_font(11),
    "stat": load_font(14, bold=True),
    "stat_label": load_font(9),
    "lead_num": load_font(28, bold=True),
    "lead_kicker": load_font(13, bold=True),
    "lead_deck": load_font(10),
    "lead_source": load_font(9),
    "ribbon_time": load_font(8),
    "ribbon_event": load_font(8, bold=True),
    "card_num": load_font(17, bold=True),
    "card_kicker": load_font(10, bold=True),
    "card_deck": load_font(8),
    "card_source": load_font(8),
    "map_title": load_font(11, bold=True),
    "map_pin": load_font(9, bold=True),
    "also_title": load_font(10, bold=True),
    "also_item": load_font(9),
    "datecheck_title": load_font(9, bold=True),
    "datecheck_item": load_font(8),
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


LEADS = [
    Story(
        num=1,
        kicker="Macy's 100th Thanksgiving Parade",
        deck="Nor'easter forces postponement to Saturday; 100 inflatables, 81.5m Americans travelling",
        source="AP",
        status="REPORTED",
        region="North America",
        utc_hour=13,
        lat=40.75,
        lon=-73.98,
        is_lead=True,
    ),
    Story(
        num=2,
        kicker="India: 18 Years Since 26/11 + Constitution Day",
        deck="Mumbai commemorates 2008 terror siege; 77th Constitution Day adds 6,000 IIT seats",
        source="Reuters",
        status="OFFICIAL",
        region="South Asia",
        utc_hour=6,
        lat=19.07,
        lon=72.87,
        is_lead=True,
    ),
    Story(
        num=3,
        kicker="World Chess Championship Game 3: Gukesh vs Sindarov",
        deck="Geneva match tied 1–1 after three games; Indian teen eyes history",
        source="AFP",
        status="CONFIRMED",
        region="Europe",
        utc_hour=14,
        lat=46.20,
        lon=6.14,
        is_lead=True,
    ),
]

CARDS = [
    Story(
        num=4,
        kicker="Houthis Claim Ras Tanura Refinery Strike",
        deck="Brent crude tops $94; Saudi denies damage; dating disputed — CLAIM only",
        source="Al Jazeera",
        status="CLAIM",
        region="Middle East",
        utc_hour=8,
        lat=26.65,
        lon=50.15,
        is_card=True,
    ),
    Story(
        num=5,
        kicker="Two Tankers Hit Naval Mines in Strait of Hormuz",
        deck="Crew evacuated; shipping lanes disrupted; investigation under way",
        source="Reuters",
        status="REPORTED",
        region="Middle East",
        utc_hour=10,
        lat=26.56,
        lon=56.25,
        is_card=True,
    ),
    Story(
        num=6,
        kicker="Israeli Strike Kills Hamas Security Chief in Gaza",
        deck="Senior operative eliminated; IDF confirms operation",
        source="BBC",
        status="CONFIRMED",
        region="Middle East",
        utc_hour=4,
        lat=31.50,
        lon=34.46,
        is_card=True,
    ),
    Story(
        num=7,
        kicker="Ukraine Hits 5 Russian Aircraft at Savasleyka Airbase",
        deck="Drone strike deep inside Russia; Kyiv claims major blow to bomber fleet",
        source="Reuters",
        status="CLAIM",
        region="Europe",
        utc_hour=2,
        lat=55.68,
        lon=42.50,
        is_card=True,
    ),
    Story(
        num=8,
        kicker="Russian Drones Kill 7 in Kyiv",
        deck="Overnight barrage hits residential districts; air defences intercept most",
        source="AP",
        status="CONFIRMED",
        region="Europe",
        utc_hour=1,
        lat=50.45,
        lon=30.52,
        is_card=True,
    ),
    Story(
        num=9,
        kicker="Leaked Data: 490,334 Russian War Dead",
        deck="Mediazona/BBC analysis of probate records; Moscow silent",
        source="BBC",
        status="REPORTED",
        region="Europe",
        utc_hour=12,
        lat=55.75,
        lon=37.61,
        is_card=True,
    ),
    Story(
        num=10,
        kicker="US Proposes Tariffs on 14 Partners (China 20%)",
        deck="USTR announces sweeping review; allies and rivals both targeted",
        source="Reuters",
        status="OFFICIAL",
        region="North America",
        utc_hour=16,
        lat=38.90,
        lon=-77.03,
        is_card=True,
    ),
    Story(
        num=11,
        kicker="Bangladesh Garment Wage Hiked 36% to Tk 17,000",
        deck="Minimum wage board decision after months of worker protests",
        source="AFP",
        status="OFFICIAL",
        region="South Asia",
        utc_hour=5,
        lat=23.81,
        lon=90.41,
        is_card=True,
    ),
    Story(
        num=12,
        kicker="Shenzhou-24 Docks: First Pakistani Astronaut Reaches Tiangong",
        deck="Muhammad Zeeshan Ali makes history; China–Pakistan space cooperation deepens",
        source="Xinhua",
        status="CONFIRMED",
        region="East Asia",
        utc_hour=3,
        lat=40.00,
        lon=116.00,
        is_card=True,
    ),
    Story(
        num=13,
        kicker="Cairo Tanker Fire Kills 30–31",
        deck="Fuel truck explosion in dense neighbourhood; dozens injured",
        source="AP",
        status="CONFIRMED",
        region="Africa",
        utc_hour=18,
        lat=30.04,
        lon=31.23,
        is_card=True,
    ),
    Story(
        num=14,
        kicker="Colombia Frees 25 Hostages in Cartagena Operation",
        deck="Military rescue after weeks of negotiation; ELN captives released",
        source="Reuters",
        status="CONFIRMED",
        region="South America",
        utc_hour=20,
        lat=10.39,
        lon=-75.48,
        is_card=True,
    ),
    Story(
        num=15,
        kicker="Solomon Islands–Australia Security Pact ($740m)",
        deck="Canberra commits policing and infrastructure; Beijing watches closely",
        source="BBC",
        status="OFFICIAL",
        region="Oceania",
        utc_hour=22,
        lat=-9.43,
        lon=159.95,
        is_card=True,
    ),
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
    Story(num=28, kicker="EU Approves €50bn Ukraine Aid Package", deck="Hungary drops veto after concessions", source="Reuters", status="OFFICIAL", region="Europe", is_also=True),
    Story(num=29, kicker="South Africa GDP Contracts 0.3%", deck="Load-shedding weighs on output", source="Stats SA", status="OFFICIAL", region="Africa", is_also=True),
    Story(num=30, kicker="Indonesia Elects New Parliament Speaker", deck="Prabowo ally takes gavel", source="Jakarta Post", status="CONFIRMED", region="Southeast Asia", is_also=True),
    Story(num=31, kicker="Nigeria Fuel Price Hike Sparks Protests", deck="NLC calls nationwide strike", source="Channels TV", status="ONGOING", region="Africa", is_also=True),
    Story(num=32, kicker="Mexico Supreme Court Decriminalises Abortion", deck="Landmark ruling for Latin America", source="El Universal", status="OFFICIAL", region="North America", is_also=True),
    Story(num=33, kicker="Turkey Inflation Dips to 47% YoY", deck="Central bank sees peak passed", source="Reuters", status="REPORTED", region="Middle East", is_also=True),
    Story(num=34, kicker="Philippines–US Base Access Deal Expands", deck="Four new EDCA sites agreed", source="Inquirer", status="OFFICIAL", region="Southeast Asia", is_also=True),
    Story(num=35, kicker="Kenya Police Deploy to Haiti (UN Mission)", deck="First contingent arrives Port-au-Prince", source="AFP", status="CONFIRMED", region="Africa", is_also=True),
    Story(num=36, kicker="Chile Wildfires Kill 11, Destroy 5,000ha", deck="Valparaíso region under red alert", source="Reuters", status="CONFIRMED", region="South America", is_also=True),
    Story(num=37, kicker="Vietnam GDP Growth 6.8% in Q3", deck="Manufacturing export surge", source="VnExpress", status="OFFICIAL", region="Southeast Asia", is_also=True),
    Story(num=38, kicker="Iraq Awards Major Gas Contracts to TotalEnergies", deck="Basra fields development", source="AP", status="OFFICIAL", region="Middle East", is_also=True),
    Story(num=39, kicker="New Zealand Cuts Rates to 4.75%", deck="RBNZ signals further easing", source="Bloomberg", status="OFFICIAL", region="Oceania", is_also=True),
    Story(num=40, kicker="Canada Adds 25,000 Jobs in October", deck="Unemployment holds at 6.5%", source="StatCan", status="OFFICIAL", region="North America", is_also=True),
]

ALL_STORIES = LEADS + CARDS + ALSO_STORIES

# UTC Ribbon events (8 chips pinned to hours)
UTC_EVENTS = [
    (1, "01:00", "Russian drones strike Kyiv (7 dead)"),
    (2, "02:00", "Ukraine hits Savasleyka airbase (5 jets)"),
    (3, "03:00", "Shenzhou-24 docks at Tiangong"),
    (4, "04:00", "Israeli strike kills Hamas security chief"),
    (5, "05:00", "Bangladesh garment wage +36%"),
    (8, "08:00", "Houthis claim Ras Tanura strike"),
    (10, "10:00", "Two tankers mined in Hormuz"),
    (14, "14:00", "World Chess Game 3 underway"),
]

DATE_CHECK_EXCLUSIONS = [
    "Nvidia/Huang reinstatement (earlier)",
    "COP31 (future)",
    "Ukraine drones Libya (25 Nov)",
    "Belgium strike (25 Nov)",
    "Trump–Putin–Xi Shenzhen (fabricated)",
    "UNRWA worker (undated)",
    "BepiColombo Mercury orbit (21 Nov)",
    "Houthi Ras Tanura as confirmed fact (disputed dating)",
    "Murmansk governor detention (25 Nov)",
]

REGIONS = sorted({s.region for s in ALL_STORIES})
SOURCES = sorted({s.source for s in ALL_STORIES})

# ─── Drawing Helpers ────────────────────────────────────────────────────────

def draw_rounded_rect(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_status_chip(draw: ImageDraw.ImageDraw, x, y, text, font, status, max_w=None):
    color = STATUS_COLORS.get(status, INK)
    bg = STATUS_BG.get(status, "#eeeeee")
    padding = 4
    tw = draw.textlength(text, font=font)
    w = tw + 2 * padding
    if max_w and w > max_w:
        w = max_w
    h = font.size + 2 * padding
    draw_rounded_rect(draw, (x, y, x + w, y + h), radius=3, fill=bg, outline=color, width=1)
    draw.text((x + padding, y + padding), text, font=font, fill=color)
    return w


def draw_region_chip(draw: ImageDraw.ImageDraw, x, y, text, font):
    color = REGION_COLORS.get(text, INK)
    padding = 3
    tw = draw.textlength(text, font=font)
    w = tw + 2 * padding
    h = font.size + 2 * padding
    draw_rounded_rect(draw, (x, y, x + w, y + h), radius=2, fill=color + "20", outline=color, width=1)
    draw.text((x + padding, y + padding), text, font=font, fill=color)
    return w


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        if draw.textlength(test, font=font) <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_drawn_scene(draw: ImageDraw.ImageDraw, x, y, w, h, scene_type: str, lead: bool = False):
    """Draw a stylized 'drawn' scene (not a photo) for a story."""
    draw.rectangle((x, y, x + w, y + h), fill="#f0ebe0", outline="#d0c8b8", width=1)
    cx, cy = x + w // 2, y + h // 2

    if scene_type == "parade":
        for i, (bx, by, br, color) in enumerate([
            (cx - 50, cy - 25, 20, "#e74c3c"),
            (cx + 10, cy - 35, 25, "#3498db"),
            (cx + 60, cy - 15, 18, "#f1c40f"),
        ]):
            draw.ellipse((bx - br, by - br, bx + br, by + br), fill=color, outline="#2c2c2c", width=1)
            draw.line((bx, by + br, bx, by + br + 15), fill="#2c2c2c", width=1)
        draw.rectangle((x, cy + 25, x + w, y + h), fill="#555555")
        for px in range(x + 15, x + w - 15, 15):
            draw.rectangle((px, cy + 20, px + 6, cy + 45), fill="#333333")
        for bx in range(x + 10, x + w - 10, 50):
            bh = 50 + (bx % 3) * 15
            draw.rectangle((bx, cy - bh, bx + 35, cy), fill="#777777", outline="#555555", width=1)
            for wx in range(bx + 5, bx + 30, 10):
                draw.rectangle((wx, cy - bh + 5, wx + 6, cy - 5), fill="#ffffcc")

    elif scene_type == "india":
        draw.arc((cx - 40, cy - 50, cx + 40, cy + 15), start=0, end=180, fill="#8b4513", width=6)
        draw.arc((cx - 32, cy - 42, cx + 32, cy + 7), start=0, end=180, fill="#a0522d", width=4)
        draw.rectangle((cx - 35, cy - 70, cx + 35, cy - 50), fill="#ff9933")
        draw.rectangle((cx - 35, cy - 50, cx + 35, cy - 30), fill="#ffffff")
        draw.rectangle((cx - 35, cy - 30, cx + 35, cy - 10), fill="#138808")
        draw.ellipse((cx - 7, cy - 45, cx + 7, cy - 31), outline="#000080", width=1)
        for i in range(24):
            ang = math.radians(i * 15)
            x1 = cx + 2 * math.cos(ang)
            y1 = cy - 38 + 2 * math.sin(ang)
            x2 = cx + 6 * math.cos(ang)
            y2 = cy - 38 + 6 * math.sin(ang)
            draw.line((x1, y1, x2, y2), fill="#000080", width=1)
        draw.rectangle((x + 15, cy - 15, x + 60, cy + 25), fill="#444444")
        for wx in range(x + 18, x + 57, 8):
            draw.rectangle((wx, cy - 10, wx + 5, cy + 20), fill="#666666")

    elif scene_type == "chess":
        sq = min(w, h) // 9
        bx, by = cx - 4 * sq, cy - 4 * sq
        for row in range(8):
            for col in range(8):
                color = "#f0d9b5" if (row + col) % 2 == 0 else "#b58863"
                draw.rectangle((bx + col * sq, by + row * sq, bx + (col + 1) * sq, by + (row + 1) * sq), fill=color)
        kx, ky = bx + 3 * sq + sq // 2, by + 0 * sq + sq // 2
        draw.ellipse((kx - 8, ky - 20, kx + 8, ky + 4), fill="#ffffff", outline="#333333", width=1)
        draw.polygon([(kx, ky - 24), (kx - 5, ky - 16), (kx + 5, ky - 16)], fill="#ffd700")
        kx2, ky2 = bx + 4 * sq + sq // 2, by + 7 * sq + sq // 2
        draw.ellipse((kx2 - 8, ky2 - 20, kx2 + 8, ky2 + 4), fill="#1a1a1a", outline="#333333", width=1)
        draw.polygon([(kx2, ky2 - 24), (kx2 - 5, ky2 - 16), (kx2 + 5, ky2 - 16)], fill="#ffd700")

    elif scene_type == "houthi":
        draw.rectangle((cx - 40, cy - 8, cx + 40, cy + 30), fill="#333333")
        for px in range(cx - 35, cx + 35, 12):
            draw.rectangle((px, cy - 25, px + 6, cy - 8), fill="#222222")
        draw.polygon([(cx, cy - 35), (cx - 12, cy - 8), (cx + 12, cy - 8)], fill="#e74c3c")
        draw.polygon([(cx, cy - 26), (cx - 8, cy - 8), (cx + 8, cy - 8)], fill="#f39c12")
        draw.text((cx, cy + 40), "?", font=FONTS["lead_kicker"], fill="#e74c3c", anchor="mm")

    elif scene_type == "tanker":
        for i, tx in enumerate([cx - 60, cx + 10]):
            draw.rectangle((tx, cy - 8, tx + 65, cy + 12), fill="#444444")
            draw.rectangle((tx + 15, cy - 25, tx + 50, cy - 8), fill="#555555")
            draw.ellipse((tx + 25, cy - 30, tx + 40, cy - 10), fill="#e74c3c")
        for wx in range(x, x + w, 15):
            draw.arc((wx, cy + 8, wx + 15, cy + 22), start=180, end=360, fill="#3498db", width=1)

    elif scene_type == "gaza":
        for bx in range(x + 8, x + w - 8, 25):
            bh = 35 + (bx % 4) * 12
            draw.rectangle((bx, cy + 15 - bh, bx + 18, cy + 15), fill="#555555")
            for wx in range(bx + 2, bx + 16, 6):
                draw.rectangle((wx, cy + 12 - bh, wx + 3, cy + 12), fill="#ffcc00")
        draw.line((cx, y + 8, cx, cy - 8), fill="#e74c3c", width=3)
        draw.polygon([(cx, y + 8), (cx - 6, y + 20), (cx + 6, y + 20)], fill="#e74c3c")

    elif scene_type == "ukraine":
        for i, px in enumerate([cx - 50, cx - 15, cx + 20, cx + 55]):
            draw.rectangle((px - 12, cy - 4, px + 12, cy + 8), fill="#666666")
            draw.polygon([(px, cy - 4), (px - 16, cy + 8), (px + 16, cy + 8)], fill="#444444")
        draw.ellipse((cx - 25, y + 15, cx + 25, y + 40), fill="#222222", outline="#444444", width=1)
        draw.line((cx - 25, y + 27, cx + 25, y + 27), fill="#222222", width=2)
        draw.line((cx, y + 15, cx, y + 40), fill="#222222", width=2)

    elif scene_type == "kyiv":
        for bx in range(x + 8, x + w - 8, 30):
            bh = 45 + (bx % 5) * 15
            draw.rectangle((bx, cy - bh, bx + 22, cy), fill="#444444")
        for dx in [cx - 45, cx, cx + 45]:
            draw.ellipse((dx - 8, y + 15, dx + 8, y + 35), fill="#1a1a1a", outline="#333333", width=1)
            draw.line((dx - 8, y + 25, dx + 8, y + 25), fill="#1a1a1a", width=1)

    elif scene_type == "casualties":
        draw.rectangle((cx - 50, cy - 40, cx + 50, cy + 40), fill="#ffffff", outline="#cccccc", width=1)
        draw.rectangle((cx - 42, cy - 32, cx + 42, cy - 16), fill="#e74c3c")
        draw.text((cx, cy - 24), "490,334", font=FONTS["lead_kicker"], fill="#ffffff", anchor="mm")
        draw.rectangle((cx - 42, cy - 8, cx + 42, cy + 8), fill="#f0f0f0")
        draw.text((cx, cy), "Russian war dead", font=FONTS["lead_deck"], fill=INK, anchor="mm")
        draw.rectangle((cx - 42, cy + 16, cx + 42, cy + 32), fill="#e6e6e6")

    elif scene_type == "tariffs":
        draw.rectangle((cx - 40, cy - 32, cx + 40, cy + 25), fill="#f5f5f5", outline="#cccccc", width=1)
        draw.ellipse((cx - 25, cy - 58, cx + 25, cy - 8), fill="#f5f5f5", outline="#cccccc", width=1)
        draw.ellipse((cx - 18, cy - 50, cx + 18, cy - 14), fill="#ffffff")
        draw.rectangle((cx - 35, cy - 2, cx + 35, cy + 22), fill="#e74c3c")
        draw.text((cx, cy + 10), "TARIFFS 20%", font=FONTS["card_kicker"], fill="#ffffff", anchor="mm")

    elif scene_type == "bangladesh":
        draw.rectangle((cx - 40, cy - 15, cx + 40, cy + 35), fill="#dddddd", outline="#999999", width=1)
        for wx in range(cx - 35, cx + 35, 12):
            draw.rectangle((wx, cy - 10, wx + 8, cy + 30), fill="#bbbbbb")
        for mx in [cx - 25, cx, cx + 25]:
            draw.rectangle((mx - 6, cy - 3, mx + 6, cy + 12), fill="#444444")
        draw.rectangle((cx - 35, cy - 42, cx + 35, cy - 18), fill="#2ca02c")
        draw.text((cx, cy - 30), "Tk 17,000", font=FONTS["lead_kicker"], fill="#ffffff", anchor="mm")
        draw.text((cx, cy - 16), "+36%", font=FONTS["card_kicker"], fill="#ffffff", anchor="mm")

    elif scene_type == "shenzhou":
        draw.rectangle((cx - 65, cy - 8, cx + 65, cy + 8), fill="#444444", outline="#666666", width=1)
        draw.rectangle((cx - 80, cy - 25, cx - 65, cy + 25), fill="#222222")
        draw.rectangle((cx + 65, cy - 25, cx + 80, cy + 25), fill="#222222")
        draw.ellipse((cx + 72, cy - 20, cx + 105, cy + 20), fill="#e74c3c", outline="#c0392b", width=1)
        draw.text((cx, cy + 40), "🇵🇰 First Pakistani", font=FONTS["card_deck"], fill=INK, anchor="mm")

    elif scene_type == "cairo":
        draw.rectangle((cx - 32, cy - 8, cx + 32, cy + 25), fill="#333333")
        draw.rectangle((cx - 25, cy - 35, cx + 25, cy - 8), fill="#222222")
        for fx in [cx - 16, cx, cx + 16]:
            draw.polygon([(fx, cy - 42), (fx - 8, cy - 8), (fx + 8, cy - 8)], fill="#e74c3c")
            draw.polygon([(fx, cy - 34), (fx - 5, cy - 8), (fx + 5, cy - 8)], fill="#f39c12")
        draw.text((cx, cy + 40), "30–31 dead", font=FONTS["card_kicker"], fill="#e74c3c", anchor="mm")

    elif scene_type == "colombia":
        draw.rectangle((x + 15, cy - 15, x + w - 15, cy + 30), fill="#2c5f2d", outline="#1e3d1e", width=1)
        for px in range(x + 30, x + w - 30, 20):
            draw.ellipse((px - 6, cy - 12, px + 6, cy + 4), fill="#fdbcb4")
            draw.rectangle((px - 8, cy + 4, px + 8, cy + 28), fill="#2c5f2d")
        draw.text((cx, cy + 40), "25 freed", font=FONTS["card_kicker"], fill="#ffffff", anchor="mm")

    elif scene_type == "solomons":
        draw.ellipse((cx - 35, cy - 35, cx + 35, cy + 35), fill="#17becf", outline="#0a8a9e", width=1)
        draw.ellipse((cx - 18, cy - 8, cx + 8, cy + 18), fill="#2ca02c")
        draw.ellipse((cx + 10, cy - 18, cx + 30, cy + 4), fill="#2ca02c")
        draw.ellipse((cx - 12, cy + 8, cx - 4, cy + 20), fill="#fdbcb4")
        draw.ellipse((cx + 4, cy + 8, cx + 12, cy + 20), fill="#fdbcb4")
        draw.text((cx, cy + 45), "$740m pact", font=FONTS["card_kicker"], fill="#0a8a9e", anchor="mm")

    else:
        draw.rectangle((x, y, x + w, y + h), fill="#eeeeee", outline="#cccccc", width=1)
        draw.text((cx, cy), scene_type.upper(), font=FONTS["card_deck"], fill=INK, anchor="mm")


# ─── Main Generation ────────────────────────────────────────────────────────

def generate() -> Path:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    padding = 10
    gap = 6
    content_w = W - 2 * padding
    y = 0

    # ═══ MASTHEAD ══════════════════════════════════════════════════════════════
    masthead_h = 44
    draw.rectangle((0, y, W, y + masthead_h), fill=ACCENT_RED)
    draw.text((W // 2, y + 23), "THE WORLD IN ONE DAY", font=FONTS["masthead"], fill="#ffffff", anchor="mm")
    y += masthead_h

    # Dateline
    dateline_h = 24
    draw.rectangle((0, y, W, y + dateline_h), fill=ACCENT_BLUE)
    draw.text((W // 2, y + 12), "THURSDAY 26 NOVEMBER 2026", font=FONTS["dateline"], fill="#ffffff", anchor="mm")
    y += dateline_h

    # Standfirst
    standfirst_h = 18
    draw.text((W // 2, y + 9), "40 stories · 9 regions · 17 sources · one newspaper front page", font=FONTS["standfirst"], fill=INK_LIGHT, anchor="mm")
    y += standfirst_h

    # ═══ BIG-NUMBER STAT STRIP ════════════════════════════════════════════════
    stat_h = 30
    draw.rectangle((padding, y, W - padding, y + stat_h), fill="#f5f0e0", outline="#ddd8c8", width=1)
    stats = [
        ("40", "STORIES"),
        ("9", "REGIONS"),
        (str(len(SOURCES)), "SOURCES"),
        ("100th", "PARADE"),
        ("81.5m", "TRAVELLERS"),
        ("490,334", "RUSSIAN DEAD"),
        ("+36%", "WAGE HIKE"),
        ("$237.5bn", "VENEZUELA DEBT"),
        ("4.3%", "US Q3 GDP"),
    ]
    stat_x = padding + 8
    for val, label in stats:
        draw.text((stat_x, y + 3), val, font=FONTS["stat"], fill=ACCENT_RED)
        draw.text((stat_x, y + 19), label, font=FONTS["stat_label"], fill=INK_LIGHT)
        stat_x += draw.textlength(val + "  ", font=FONTS["stat"]) + 6
    # Region color bar
    bar_y = y + stat_h - 2
    region_w = content_w // len(REGIONS)
    for i, region in enumerate(REGIONS):
        color = REGION_COLORS[region]
        draw.rectangle((padding + i * region_w, bar_y, padding + (i + 1) * region_w, y + stat_h), fill=color)
    y += stat_h + gap

    # ═══ THREE LEAD PANELS ═════════════════════════════════════════════════════
    lead_h = 180
    lead_w = (content_w - 2 * gap) // 3
    lead_x_start = padding
    lead_y = y

    for i, lead in enumerate(LEADS):
        lx = lead_x_start + i * (lead_w + gap)
        ly = lead_y
        # Panel background
        draw.rectangle((lx, ly, lx + lead_w, ly + lead_h), fill="#fdfbf5", outline="#e0d8c8", width=1)

        # Number badge
        badge_r = 22
        draw.ellipse((lx + 10, ly + 10, lx + 10 + badge_r * 2, ly + 10 + badge_r * 2), fill=ACCENT_RED)
        draw.text((lx + 10 + badge_r, ly + 10 + badge_r), str(lead.num), font=FONTS["lead_num"], fill="#ffffff", anchor="mm")

        # Status chip
        draw_status_chip(draw, lx + lead_w - 85, ly + 8, lead.status, FONTS["lead_source"], lead.status)

        # Region chip
        draw_region_chip(draw, lx + 65, ly + 8, lead.region, FONTS["stat_label"])

        # Drawn scene
        scene_y = ly + 44
        scene_h = 90
        scene_types = ["parade", "india", "chess"]
        draw_drawn_scene(draw, lx + 6, scene_y, lead_w - 12, scene_h, scene_types[i], lead=True)

        # Kicker
        kicker_y = scene_y + scene_h + 5
        kicker_lines = wrap_text(draw, lead.kicker, FONTS["lead_kicker"], lead_w - 12)
        for j, line in enumerate(kicker_lines[:2]):
            draw.text((lx + 6, kicker_y + j * 16), line, font=FONTS["lead_kicker"], fill=INK)

        # Deck
        deck_y = kicker_y + len(kicker_lines) * 16 + 3
        deck_lines = wrap_text(draw, lead.deck, FONTS["lead_deck"], lead_w - 12)
        for j, line in enumerate(deck_lines[:2]):  # Reduced from 3 to 2 lines
            draw.text((lx + 6, deck_y + j * 13), line, font=FONTS["lead_deck"], fill=INK_LIGHT)

        # Source
        source_y = ly + lead_h - 16
        draw.text((lx + 6, source_y), f"Source: {lead.source}", font=FONTS["lead_source"], fill=ACCENT_BLUE)

    y += lead_h + 10  # Increased gap before UTC ribbon

    # ═══ UTC RIBBON (THE TWIST) ════════════════════════════════════════════════
    ribbon_h = 36
    draw.rectangle((padding, y, W - padding, y + ribbon_h), fill="#1a1a2e", outline="#0f0f1a", width=1)
    draw.text((padding + 6, y + 3), "THE DAY IN UTC", font=FONTS["stat_label"], fill="#ffffff")
    line_y = y + 22
    draw.line((padding + 6, line_y, W - padding - 6, line_y), fill="#444466", width=1)
    for hour in range(0, 24, 3):
        hx = padding + 6 + (hour / 23) * (W - 2 * padding - 12)
        draw.line((hx, line_y - 2, hx, line_y + 2), fill="#666688", width=1)
        draw.text((hx, line_y + 5), f"{hour:02d}:00", font=FONTS["ribbon_time"], fill="#aaaaaa", anchor="mm")

    for evt_hour, evt_label, evt_text in UTC_EVENTS:
        hx = padding + 6 + (evt_hour / 23) * (W - 2 * padding - 12)
        draw.polygon([(hx, line_y), (hx - 4, line_y - 12), (hx + 4, line_y - 12)], fill="#e74c3c")
        chip_w = draw.textlength(evt_text, FONTS["ribbon_event"]) + 8
        chip_x = hx - chip_w // 2
        chip_y = line_y - 28
        if chip_x < padding + 6:
            chip_x = padding + 6
        if chip_x + chip_w > W - padding - 6:
            chip_x = W - padding - 6 - chip_w
        draw_rounded_rect(draw, (chip_x, chip_y, chip_x + chip_w, chip_y + 16), radius=3, fill="#e74c3c")
        draw.text((chip_x + 4, chip_y + 1), evt_text, font=FONTS["ribbon_event"], fill="#ffffff")

    y += ribbon_h + gap

    # ═══ 12 CARD GRID (3×4) ═══════════════════════════════════════════════════
    card_cols = 3
    card_rows = 4
    card_w = (content_w - (card_cols - 1) * gap) // card_cols
    card_h = 90
    grid_start_y = y

    for idx, card in enumerate(CARDS):
        col = idx % card_cols
        row = idx // card_cols
        cx = padding + col * (card_w + gap)
        cy = grid_start_y + row * (card_h + gap)

        draw.rectangle((cx, cy, cx + card_w, cy + card_h), fill="#fdfbf5", outline="#e0d8c8", width=1)

        badge_r = 13
        draw.ellipse((cx + 5, cy + 5, cx + 5 + badge_r * 2, cy + 5 + badge_r * 2), fill=ACCENT_RED)
        draw.text((cx + 5 + badge_r, cy + 5 + badge_r), str(card.num), font=FONTS["card_num"], fill="#ffffff", anchor="mm")

        draw_status_chip(draw, cx + card_w - 65, cy + 5, card.status, FONTS["card_source"], card.status, max_w=60)
        draw_region_chip(draw, cx + 38, cy + 5, card.region, FONTS["card_source"])

        scene_size = 50
        scene_x = cx + 5
        scene_y = cy + 28
        scene_types = ["houthi", "tanker", "gaza", "ukraine", "kyiv", "casualties",
                       "tariffs", "bangladesh", "shenzhou", "cairo", "colombia", "solomons"]
        draw_drawn_scene(draw, scene_x, scene_y, scene_size, scene_size, scene_types[idx])

        text_x = scene_x + scene_size + 6
        text_w = card_w - (text_x - cx) - 6
        kicker_lines = wrap_text(draw, card.kicker, FONTS["card_kicker"], text_w)
        ky = scene_y
        for line in kicker_lines[:2]:
            draw.text((text_x, ky), line, font=FONTS["card_kicker"], fill=INK)
            ky += 12

        ky += 2
        deck_lines = wrap_text(draw, card.deck, FONTS["card_deck"], text_w)
        for line in deck_lines[:2]:
            draw.text((text_x, ky), line, font=FONTS["card_deck"], fill=INK_LIGHT)
            ky += 10

        draw.text((text_x, cy + card_h - 12), f"Source: {card.source}", font=FONTS["card_source"], fill=ACCENT_BLUE)

    y = grid_start_y + card_rows * (card_h + gap) + gap

    # ═══ WORLD MAP WITH PINS ══════════════════════════════════════════════════
    map_h = 60
    map_y = y
    draw.rectangle((padding, map_y, W - padding, map_y + map_h), fill="#e8f4f8", outline="#b0d0e0", width=1)
    draw.text((W // 2, map_y + 10), "WHERE IT HAPPENED", font=FONTS["map_title"], fill=ACCENT_BLUE, anchor="mm")

    map_left = padding + 25
    map_right = W - padding - 25
    map_top = map_y + 22
    map_bottom = map_y + map_h - 4
    map_w = map_right - map_left
    map_h_px = map_bottom - map_top

    def proj(lon, lat):
        x = map_left + (lon + 180) / 360 * map_w
        y = map_top + (90 - lat) / 180 * map_h_px
        return int(x), int(y)

    continents = [
        [(-160, 60), (-60, 60), (-60, 15), (-160, 15)],
        [(-80, 15), (-35, 15), (-35, -55), (-80, -55)],
        [(-10, 35), (40, 35), (40, 70), (-10, 70)],
        [(-20, 35), (55, 35), (55, -35), (-20, -35)],
        [(40, 15), (180, 15), (180, 70), (40, 70)],
        [(110, -10), (155, -10), (155, -45), (110, -45)],
    ]
    for poly in continents:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill="#c8e6c9", outline="#81c784", width=1)

    for story in ALL_STORIES:
        if story.lat is not None and story.lon is not None:
            px, py = proj(story.lon, story.lat)
            draw.ellipse((px - 4, py - 10, px + 4, py), fill=ACCENT_RED, outline="#8b0000", width=1)
            draw.polygon([(px, py), (px - 3, py + 3), (px + 3, py + 3)], fill=ACCENT_RED)
            draw.text((px, py - 7), str(story.num), font=FONTS["map_pin"], fill="#ffffff", anchor="mm")

    y += map_h + gap

    # ═══ ALSO LIST (16–40) ═══════════════════════════════════════════════════
    also_h = 66  # Slightly taller for larger font
    draw.rectangle((padding, y, W - padding, y + also_h), fill="#fdfbf5", outline="#e0d8c8", width=1)
    draw.text((padding + 6, y + 3), "ALSO ON THURSDAY 26 NOVEMBER", font=FONTS["also_title"], fill=ACCENT_RED)

    col_w = (content_w - gap) // 2
    left_x = padding + 6
    right_x = padding + 6 + col_w + gap
    item_h = 12  # Increased for larger font
    start_y = y + 18

    for i, story in enumerate(ALSO_STORIES):
        col = i // 13
        row = i % 13
        tx = left_x if col == 0 else right_x
        ty = start_y + row * item_h
        if ty + item_h > y + also_h - 3:
            continue
        color = REGION_COLORS.get(story.region, INK)
        draw.ellipse((tx, ty + 1, tx + 5, ty + 9), fill=color)
        text = f"{story.num}. {story.kicker}"
        draw.text((tx + 9, ty), text, font=FONTS["also_item"], fill=INK)
        src_text = f"  {story.source} · {story.status}"
        draw.text((tx + 9, ty + 8), src_text, font=FONTS["datecheck_item"], fill=INK_LIGHT)

    y += also_h + gap

    # ═══ DATE CHECK FOOTER ═══════════════════════════════════════════════════
    dc_h = 30
    draw.rectangle((padding, y, W - padding, y + dc_h), fill="#fff8f0", outline="#ffe0c0", width=1)
    draw.text((padding + 6, y + 2), "DATE CHECK", font=FONTS["datecheck_title"], fill=ACCENT_RED)
    dc_text = "Excluded (not 26 Nov): " + "; ".join(DATE_CHECK_EXCLUSIONS)
    dc_lines = wrap_text(draw, dc_text, FONTS["datecheck_item"], content_w - 12)
    for i, line in enumerate(dc_lines[:2]):
        draw.text((padding + 6, y + 15 + i * 9), line, font=FONTS["datecheck_item"], fill=INK_LIGHT)

    # ═══ Final border ══════════════════════════════════════════════════════════
    draw.rectangle((0, 0, W - 1, H - 1), outline="#cccccc", width=1)

    # Save
    out_path = Path("/home/hatch/workspace/makefun/news-image-20261126/out/entry.png")
    img.save(out_path, "PNG", optimize=True)
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