#!/usr/bin/env python3
"""news-image-20261122 v1.3 — "The World in One Day: Sunday 22 November 2026".

Draws a 1024x1024 front page summing up Sunday 22 November 2026's world
news: 35 dated stories (13 pictorial leads + 22 briefs) from 7 regions,
plus a DATE CHECK box naming what is NOT Sunday's news.

Runs with no network. Writes to $MAKEFUN_OUTPUT_DIR/entry.png when that
is set, else $ENTRY_OUTPUT, else /output/entry.png. Deterministic: same
input bytes -> same output bytes. Python 3.10+ compatible; uses Pillow
only, and falls back to copying the committed entry.png if Pillow (or
the render) is unavailable, so the run always produces its output.
"""

import os
import shutil
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except Exception:
    Image = ImageDraw = ImageFont = None
    _PIL_OK = False

W, H = 1024, 1024

# ---------------------------------------------------------------- palette ---
CREAM = (247, 242, 231)      # page background
PAPER = (255, 253, 247)      # card background
NAVY = (20, 33, 61)          # masthead, headlines
NAVY_SOFT = (38, 56, 92)
RED = (178, 34, 34)          # accents, kickers, stat numerals
RED_DARK = (139, 26, 26)
INK = (28, 28, 28)           # body text
GREY = (105, 105, 105)       # source lines, captions
LINE = (201, 188, 164)       # hairlines
GOLD = (196, 145, 32)

REGION_COLORS = {
    "Europe": (31, 78, 121),
    "Middle East": (178, 34, 34),
    "Americas": (46, 110, 71),
    "Asia-Pacific": (196, 118, 0),
    "Oceania": (90, 60, 140),
    "Africa": (150, 90, 20),
    "World": (80, 80, 80),
}

# ------------------------------------------------------------------ fonts ---
def _load(name, size):
    bases = [
        "/usr/share/fonts/truetype/dejavu/%s" % name,
        "/usr/share/fonts/TTF/%s" % name,
        "/usr/share/fonts/dejavu/%s" % name,
    ]
    for path in bases:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def fonts():
    return {
        "mast": _load("DejaVuSans-Bold.ttf", 30),
        "mast_small": _load("DejaVuSans-Bold.ttf", 13),
        "date": _load("DejaVuSerif-Bold.ttf", 46),
        "sub": _load("DejaVuSerif-Italic.ttf", 16),
        "stat_num": _load("DejaVuSans-Bold.ttf", 26),
        "stat_cap": _load("DejaVuSans.ttf", 9),
        "region": _load("DejaVuSans-Bold.ttf", 9),
        "timeline": _load("DejaVuSans.ttf", 9),
        "kicker": _load("DejaVuSans-Bold.ttf", 10),
        "lead_head": _load("DejaVuSerif-Bold.ttf", 17),
        "lead_body": _load("DejaVuSans.ttf", 11),
        "lead_src": _load("DejaVuSans.ttf", 8),
        "tag": _load("DejaVuSans-Bold.ttf", 9),
        "med_num": _load("DejaVuSans-Bold.ttf", 13),
        "med_head": _load("DejaVuSans-Bold.ttf", 11),
        "med_body": _load("DejaVuSans.ttf", 9),
        "map_title": _load("DejaVuSans-Bold.ttf", 11),
        "brief_head": _load("DejaVuSans-Bold.ttf", 9),
        "brief_body": _load("DejaVuSans.ttf", 9),
        "dc_title": _load("DejaVuSans-Bold.ttf", 12),
        "dc_item": _load("DejaVuSans.ttf", 9),
        "footer": _load("DejaVuSans.ttf", 8),
        "pin": _load("DejaVuSans-Bold.ttf", 10),
    }


try:
    F = fonts()
except Exception:
    # Pillow (or its fonts) unavailable: render() will fail and main()
    # falls back to copying the committed entry.png.
    F = {}

# ------------------------------------------------------------------- data ---
STATS = [
    ("186", "drones launched"),
    ("161", "downed"),
    ("98.79%", "HK turnout"),
    ("720/9", "India total"),
    ("50", "Wembanyama pts"),
    ("03:00", "COP31 objections close (GMT)"),
]

REGIONS = [
    ("Europe", 9), ("Middle East", 7), ("Americas", 7),
    ("Asia-Pacific", 6), ("Oceania", 3), ("Africa", 2), ("World", 1),
]

TIMELINE = [
    ("03:00", "COP31 objections close"),
    ("05:11", "Hamas seeks talks"),
    ("05:30", "Las Vegas GP ends"),
    ("06:00", "COP31 vote due, slips"),
    ("08:00", "161 of 186 drones downed"),
    ("14:00", "HK turnout 93.55% (mid-day)"),
]

# Leads: num, kicker, region, headline, body, source, tag, lat, lon, icon
LEADS = [
    (1, "ANTALYA \u00b7 CLIMATE", "Europe",
     "COP31 talks collapse \u2014 no deal adopted",
     "The 10-page text lands at dawn, no fossil fuels named; "
     "closing plenary rejects it \u2014 Kurum: 'no consensus, these decisions have not been adopted.' "
     "EU and others opposed; first COP text to admit 1.5\u00b0C will be missed.",
     "Al Jazeera \u00b7 BBC \u00b7 Reuters", "REPORTED", 36.9, 30.7, "sunrise"),
    (2, "BAHRAIN \u00b7 CLAIM", "Middle East",
     "Iran claims Bahrain strikes; Bahrain and the US deny",
     "The IRGC claims two Patriot radars hit at al-Riffa and Awali Sakhir. "
     "Bahrain says a civilian industrial site burned, with no casualties. "
     "CENTCOM denies an F-16 was downed.",
     "Xinhua \u00b7 Al Jazeera \u00b7 Reuters", "CLAIM", 26.1, 50.6, "radar"),
    (3, "KYIV \u00b7 WAR", "Europe",
     "Russia\u2019s 186-drone overnight barrage; 161 downed",
     "Launched 18:00 Sat to Sun morning. Ukraine downs 161 of 186, incl. 56 of "
     "72 jet-powered; debris in 6 places. A Dymer block is hit, 2 hurt, 14 feared "
     "trapped. Moscow claims 170 Ukrainian drones downed.",
     "Ukrainian Air Force \u00b7 Kyiv Independent", "REPORTED", 50.45, 30.52, "drones"),
    (4, "HONG KONG \u00b7 VOTE", "Asia-Pacific",
     "Hong Kong votes, record 98.79% turnout",
     "856 candidates, 723 seats; 5,640 of 5,709 voted \u2014 a record.",
     "info.gov.hk \u00b7 SCMP", "REPORTED", 22.32, 114.17, "ballot"),
    (5, "WELLINGTON \u00b7 CRICKET", "Oceania",
     "India 720/9, a record Test total in New Zealand",
     "Rahul 136, Pant 128; India declare 720/9. NZ 119/2, 233 behind.",
     "ESPNcricinfo \u00b7 Cricbuzz", "REPORTED", -41.29, 174.78, "cricket"),
    (6, "LAS VEGAS \u00b7 F1", "Americas",
     "Verstappen wins the Las Vegas GP",
     "1:27:39.624; Norris +0.639, Piastri +1.529. Russell hits wall, 9th.",
     "F1.com \u00b7 Reuters", "REPORTED", 36.17, -115.14, "racecar"),
    (7, "GULF OF FINLAND \u00b7 SEA", "Europe",
     "Russian cargo ship Sparta II still burning off Finland",
     "Hit by two drones Sat; fire burns Sun off Loviisa. 16 crew evacuated.",
     "Reuters \u00b7 CNN", "REPORTED", 60.2, 25.5, "ship"),
    (8, "TEHRAN \u00b7 ENERGY", "Middle East",
     "Iran begins rationing electricity",
     "Blackouts start Sun, up to 2 hrs/day, after war damage to gas plants.",
     "Reuters \u00b7 RFE/RL", "REPORTED", 35.69, 51.39, "bolt"),
    (9, "MANIPUR \u00b7 INDIA", "Asia-Pacific",
     "Manipur toxic-liquor toll rises to 19",
     "600+ treated since Fri; 6 arrested; methanol suspected, unconfirmed.",
     "Reuters \u00b7 NorthEast Now", "REPORTED", 24.5, 94.0, "bottle"),
    (10, "BRAS\u00cdLIA \u00b7 BRAZIL", "Americas",
     "Bolsonaro in intensive care",
     "Admitted Fri; Sat ICU: stable, conscious. Son: surgery possible.",
     "Reuters \u00b7 AFP", "REPORTED", -15.79, -47.88, "hospital"),
    (11, "CIKANDE \u00b7 INDONESIA", "Asia-Pacific",
     "Cikande candy-factory fire: search goes on",
     "3 killed, 36 missing after Sat blaze; 15 survived. Search goes on.",
     "Reuters \u00b7 AP", "REPORTED", -6.2, 106.32, "factory"),
    (12, "GAZA \u00b7 TALKS", "Middle East",
     "Hamas seeks urgent talks after Gaza aid-van strike kills 3",
     "Sat strike kills 3 in Tel al-Hawa; Hamas calls mediators Sun.",
     "Anadolu \u00b7 Wafa", "REPORTED", 31.5, 34.47, "dove"),
    (13, "SAN ANTONIO \u00b7 NBA", "Americas",
     "Wembanyama scores 50 in Spurs win",
     "Spurs 114\u201391 Pelicans: 50 pts, 19 reb, 5 blk, 4 stl. Spurs 14-3.",
     "Reuters \u00b7 AP", "REPORTED", 29.42, -98.49, "basketball"),
]

# Briefs: num, region, headline, body, tag
BRIEFS = [
    (14, "Americas", "FBI probes NCIC hack; Washington pauses gun checks",
     "FBI knew Thu; SAFE checks halted Sat; Trump: \u2018not good\u2019.",
     "REPORTED"),
    (15, "Middle East", "Saudi coalition downs Houthi missile",
     "Sun interception in the west; separate from Sat\u2019s 3 at Riyadh.",
     "REPORTED"),
    (16, "Americas", "Nvidia \u221214% Friday as SEC probes accounting",
     "Shares fall Fri to $125.53, \u221223% on week; ~$491bn wiped Fri.",
     "REPORTED"),
    (17, "Europe", "EU and Indonesia sign trade deal",
     "Signed Saturday in Brussels; 98.5% of tariff lines; ~$30bn.",
     "REPORTED"),
    (18, "Middle East", "Two tankers hit leaving Hormuz",
     "UKMTO reports two tankers struck Sun as they left the strait.",
     "REPORTED"),
    (19, "Europe", "Denmark expels Russian attach\u00e9 over alleged plot",
     "Copenhagen expels the attach\u00e9 Sun over an alleged sabotage plot.",
     "REPORTED"),
    (20, "Asia-Pacific", "Nepal PM Shah lands in Delhi on first state visit",
     "First bilateral visit since becoming PM in March; talks Mon.",
     "REPORTED"),
    (21, "Oceania", "Marles rejects US report on AUKUS subs: \u2018They are wrong\u2019",
     "Marles dismisses a CBO report on AUKUS cutting US subs to 2060.",
     "REPORTED"),
    (22, "Middle East", "Basra power-station fire kills 4, injures 35",
     "Fire at the Hartha plant near Basra Sun; 4 dead, 35 hurt.",
     "REPORTED"),
    (23, "Americas", "ICE arrests on Seattle jet bridge; governor denounces",
     "Masked agents seize 2 on Alaska Flight 1306 (Sat); flight delayed.",
     "REPORTED"),
    (24, "Asia-Pacific", "50+ homes burned in Narail reprisals",
     "Fri night attacks in Bendar Char; reported Sat; police deny it.",
     "REPORTED"),
    (25, "Oceania", "Melbourne 1956: 70th anniversary reunion at the MCG",
     "30 Olympians, incl. Dawn Fraser, gather 70 years to the day.",
     "REPORTED"),
    (26, "Europe", "England beat New Zealand 37-12",
     "Rugby, Saturday: England beat New Zealand 37-12.",
     "REPORTED"),
    (27, "Europe", "Leeds 4-1 Chelsea",
     "Football, Saturday: Leeds beat Chelsea 4-1.",
     "REPORTED"),
    (28, "Europe", "ATP Finals: Zverev v Alcaraz",
     "Final, Sun 17:00 UTC, Turin. Winner takes the season title.",
     "FORECAST"),
    (29, "World", "Bitcoin back above $60,000; gold near $3,515",
     "BTC past $60,000 after a Sat flush to $55,130; gold near $3,515.",
     "REPORTED"),
    (30, "Asia-Pacific", "M5.6 quake off Sarangani, Sunday",
     "PHIVOLCS: M5.6, 329 km SE of Balut Is, 10 km deep; no damage.",
     "REPORTED"),
    (31, "Middle East", "US denies Iran hit an F-16",
     "CENTCOM Sun denies Tehran\u2019s claim that an F-16 was shot down.",
     "REPORTED"),
    (32, "Europe", "Liverpool v Man Utd",
     "Premier League, Sun 16:30 GMT, Anfield. The north-west derby.",
     "FORECAST"),
    (33, "Americas", "Trump shares \u2018TrumpCare\u2019 pitch, open to bipartisan talks",
     "El-Sayed\u2019s plan, shared by Trump Sat; White House had rejected it.",
     "REPORTED"),
    (34, "Africa", "Bayelsa boat toll 24 (capsized Friday)",
     "Boat capsized Fri on the Ayama\u2013Ukubie run; toll 24 confirmed Sat.",
     "REPORTED"),
    (35, "Africa", "UAE envoy\u2019s 72-hour deadline expires Sunday",
     "Somalia\u2019s deadline for the UAE envoy ends Sun; ordered Thu.",
     "REPORTED"),
]

DATE_CHECK = [
    "Russia\u2019s 400-drone, 110-missile barrage \u2014 Thu 19\u2013Fri 20 Nov",
    "Kryvyi Rih ballistic-missile double-tap \u2014 Fri 20 Nov evening",
    "\u2018El Chapo Isidro\u2019 captured \u2014 Fri 20 Nov",
    "Trump\u2013Xi\u2013Putin Shenzhen trilateral \u2014 Thu 19 Nov",
    "Estonia border closure \u2014 announced Sun 15 Nov",
    "Riemann hypothesis proof claim \u2014 Fri 20 Nov",
    "BepiColombo enters Mercury orbit \u2014 Sat 21 Nov",
    "Peru quake, USGS 6.7 \u2014 Fri 20 Nov",
    "Kerch Bridge strikes \u2014 Thu 19 Nov; Kuwait airbase \u2014 Wed 18 Nov",
    "Somalia expels UAE ambassador \u2014 Thu 19 Nov",
]

# ------------------------------------------------------------- text helpers --
def text_w(draw, text, font):
    return draw.textlength(text, font=font)


def wrap_text(draw, text, font, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            if text_w(draw, word, font) <= max_width:
                cur = word
            else:
                # hard-split a single over-long word
                chunk = ""
                for ch in word:
                    if text_w(draw, chunk + ch, font) <= max_width:
                        chunk += ch
                    else:
                        lines.append(chunk)
                        chunk = ch
                cur = chunk
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, text, font, color, max_width, leading=None,
                 max_lines=None):
    """Draw wrapped text; returns the y just below the last line drawn."""
    if leading is None:
        leading = font.size + 2
    lines = wrap_text(draw, text, font, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += leading
    return y


def draw_centered(draw, cx, y, text, font, color):
    w = text_w(draw, text, font)
    draw.text((cx - w / 2, y), text, font=font, fill=color)
    return y + font.size + 2


# -------------------------------------------------------------------- icons --
# Each icon draws a small flat pictorial scene in the box (x, y, w, h).
# Simple geometric shapes only; the number badge is drawn by the caller.

def _sky(draw, x, y, w, h, top, bottom):
    """Two-band sky: top colour, bottom colour, horizon at 62% height."""
    draw.rectangle([x, y, x + w, y + h * 0.62], fill=top)
    draw.rectangle([x, y + h * 0.62, x + w, y + h], fill=bottom)


def icon_sunrise(draw, x, y, w, h):
    _sky(draw, x, y, w, h, (246, 178, 90), (232, 122, 60))
    cx, cy, r = x + w * 0.52, y + h * 0.62, h * 0.30
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 236, 170))
    draw.rectangle([x, y + h * 0.72, x + w, y + h], fill=(90, 60, 70))
    # skyline blocks
    for bx, bw, bh in [(0.06, 0.16, 0.20), (0.26, 0.12, 0.28),
                       (0.44, 0.14, 0.16), (0.64, 0.12, 0.26),
                       (0.80, 0.14, 0.18)]:
        draw.rectangle([x + w * bx, y + h - h * bh, x + w * (bx + bw),
                        y + h], fill=(52, 36, 44))


def icon_radar(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(24, 44, 38))
    cx, cy = x + w * 0.5, y + h * 0.78
    r = h * 0.52
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], 180, 360,
                  fill=(46, 110, 71))
    draw.pieslice([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62],
                  180, 360, fill=(24, 44, 38))
    draw.line([cx, cy, cx + r * 0.7, cy - r * 0.7], fill=(120, 220, 140),
              width=2)
    for bx, by in [(0.30, 0.42), (0.68, 0.34), (0.56, 0.55)]:
        draw.ellipse([x + w * bx - 2, y + h * by - 2, x + w * bx + 2,
                      y + h * by + 2], fill=(140, 240, 160))
    draw.rectangle([x, y + h * 0.82, x + w, y + h], fill=(16, 30, 26))


def icon_drones(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(16, 24, 48))
    for sx, sy in [(0.12, 0.18), (0.35, 0.10), (0.62, 0.22), (0.85, 0.12),
                   (0.25, 0.32), (0.75, 0.30)]:
        draw.ellipse([x + w * sx - 1, y + h * sy - 1, x + w * sx + 1,
                      y + h * sy + 1], fill=(220, 220, 230))
    # drone silhouettes (X with rotors)
    for dx, dy, s in [(0.30, 0.55, 7), (0.55, 0.42, 9), (0.78, 0.62, 7)]:
        px, py = x + w * dx, y + h * dy
        draw.line([px - s, py - s, px + s, py + s], fill=(240, 240, 240),
                  width=2)
        draw.line([px - s, py + s, px + s, py - s], fill=(240, 240, 240),
                  width=2)
        draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(240, 200, 80))
    # interceptor trails
    draw.line([x + w * 0.08, y + h * 0.92, x + w * 0.30, y + h * 0.55],
              fill=(240, 160, 60), width=2)
    draw.line([x + w * 0.92, y + h * 0.95, x + w * 0.72, y + h * 0.60],
              fill=(240, 160, 60), width=2)


def icon_ballot(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 228, 214))
    # ballot box
    draw.rectangle([x + w * 0.18, y + h * 0.42, x + w * 0.82, y + h * 0.88],
                   fill=(31, 78, 121))
    draw.rectangle([x + w * 0.14, y + h * 0.34, x + w * 0.86, y + h * 0.46],
                   fill=(20, 50, 80))
    draw.rectangle([x + w * 0.38, y + h * 0.38, x + w * 0.62, y + h * 0.42],
                   fill=(247, 242, 231))
    # paper going in + check
    draw.polygon([(x + w * 0.42, y + h * 0.30), (x + w * 0.58, y + h * 0.30),
                  (x + w * 0.55, y + h * 0.10), (x + w * 0.45, y + h * 0.10)],
                 fill=(255, 253, 247))
    draw.line([x + w * 0.44, y + h * 0.22, x + w * 0.49, y + h * 0.28,
               x + w * 0.58, y + h * 0.12], fill=(178, 34, 34), width=3)


def icon_cricket(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(46, 110, 71))
    draw.rectangle([x, y + h * 0.68, x + w, y + h], fill=(196, 160, 90))
    # stumps
    for sx in (0.30, 0.36, 0.42):
        draw.line([x + w * sx, y + h * 0.34, x + w * sx, y + h * 0.66],
                  fill=(240, 220, 120), width=3)
    # bat
    draw.polygon([(x + w * 0.58, y + h * 0.18), (x + w * 0.64, y + h * 0.16),
                  (x + w * 0.72, y + h * 0.55), (x + w * 0.66, y + h * 0.58)],
                 fill=(150, 105, 55))
    # ball
    draw.ellipse([x + w * 0.76, y + h * 0.60, x + w * 0.84, y + h * 0.68],
                 fill=(178, 34, 34))


def icon_racecar(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(28, 28, 34))
    # chequered strip
    for i in range(8):
        c = (255, 253, 247) if i % 2 == 0 else (20, 20, 20)
        draw.rectangle([x + w * i / 8, y, x + w * (i + 1) / 8, y + h * 0.12],
                       fill=c)
    # car body
    draw.polygon([(x + w * 0.10, y + h * 0.72), (x + w * 0.16, y + h * 0.52),
                  (x + w * 0.42, y + h * 0.46), (x + w * 0.62, y + h * 0.50),
                  (x + w * 0.86, y + h * 0.60), (x + w * 0.90, y + h * 0.72)],
                 fill=(178, 34, 34))
    draw.polygon([(x + w * 0.42, y + h * 0.46), (x + w * 0.52, y + h * 0.34),
                  (x + w * 0.62, y + h * 0.46)], fill=(120, 20, 20))
    for wx in (0.24, 0.74):
        draw.ellipse([x + w * wx - h * 0.11, y + h * 0.68,
                      x + w * wx + h * 0.11, y + h * 0.90],
                     fill=(12, 12, 12))
        draw.ellipse([x + w * wx - h * 0.05, y + h * 0.74,
                      x + w * wx + h * 0.05, y + h * 0.84],
                     fill=(200, 200, 200))


def icon_ship(draw, x, y, w, h):
    _sky(draw, x, y, w, h, (70, 110, 150), (150, 180, 205))
    # sea
    draw.rectangle([x, y + h * 0.72, x + w, y + h], fill=(31, 78, 121))
    # hull + containers
    draw.polygon([(x + w * 0.08, y + h * 0.72), (x + w * 0.92, y + h * 0.72),
                  (x + w * 0.84, y + h * 0.88), (x + w * 0.16, y + h * 0.88)],
                 fill=(90, 40, 40))
    for cx, c in [(0.22, (196, 118, 0)), (0.40, (46, 110, 71)),
                  (0.58, (31, 78, 121)), (0.76, (178, 34, 34))]:
        draw.rectangle([x + w * cx, y + h * 0.56, x + w * (cx + 0.13),
                        y + h * 0.72], fill=c)
    # flames + smoke
    for fx, fh in [(0.30, 0.22), (0.48, 0.30), (0.66, 0.20)]:
        draw.polygon([(x + w * fx, y + h * 0.56), (x + w * (fx + 0.05),
                       y + h * (0.56 - fh)), (x + w * (fx + 0.10),
                       y + h * 0.56)], fill=(240, 140, 30))
    for sx, sy, sr in [(0.36, 0.30, 6), (0.52, 0.22, 8), (0.68, 0.32, 6)]:
        draw.ellipse([x + w * sx - sr, y + h * sy - sr, x + w * sx + sr,
                      y + h * sy + sr], fill=(120, 120, 120))


def icon_bolt(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(24, 30, 44))
    # dark buildings
    for bx, bw, bh in [(0.05, 0.20, 0.45), (0.30, 0.18, 0.60),
                       (0.55, 0.20, 0.50), (0.80, 0.16, 0.38)]:
        draw.rectangle([x + w * bx, y + h - h * bh, x + w * (bx + bw),
                        y + h], fill=(12, 16, 26))
    # lightning
    draw.polygon([(x + w * 0.52, y + h * 0.06), (x + w * 0.38, y + h * 0.52),
                  (x + w * 0.50, y + h * 0.52), (x + w * 0.40, y + h * 0.94),
                  (x + w * 0.62, y + h * 0.44), (x + w * 0.50, y + h * 0.44)],
                 fill=(240, 200, 40))


def icon_bottle(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 228, 214))
    # bottle
    draw.polygon([(x + w * 0.42, y + h * 0.12), (x + w * 0.58, y + h * 0.12),
                  (x + w * 0.58, y + h * 0.30), (x + w * 0.68, y + h * 0.42),
                  (x + w * 0.68, y + h * 0.88), (x + w * 0.32, y + h * 0.88),
                  (x + w * 0.32, y + h * 0.42), (x + w * 0.42, y + h * 0.30)],
                 fill=(46, 110, 71))
    draw.rectangle([x + w * 0.40, y + h * 0.06, x + w * 0.60, y + h * 0.13],
                   fill=(120, 40, 40))
    # warning triangle
    draw.polygon([(x + w * 0.78, y + h * 0.16), (x + w * 0.94, y + h * 0.44),
                  (x + w * 0.62, y + h * 0.44)], fill=(240, 180, 20))
    draw.text((x + w * 0.76, y + h * 0.28), "!", font=F["med_num"],
              fill=(120, 20, 20))


def icon_hospital(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 240, 240))
    draw.rectangle([x + w * 0.14, y + h * 0.60, x + w * 0.86, y + h * 0.66],
                   fill=(90, 120, 130))
    draw.rectangle([x + w * 0.14, y + h * 0.60, x + w * 0.20, y + h * 0.88],
                   fill=(70, 95, 105))
    draw.rectangle([x + w * 0.80, y + h * 0.60, x + w * 0.86, y + h * 0.88],
                   fill=(70, 95, 105))
    # cross sign
    cx, cy, s = x + w * 0.50, y + h * 0.32, h * 0.20
    draw.rectangle([cx - s, cy - s * 0.32, cx + s, cy + s * 0.32],
                   fill=(178, 34, 34))
    draw.rectangle([cx - s * 0.32, cy - s, cx + s * 0.32, cy + s],
                   fill=(178, 34, 34))


def icon_factory(draw, x, y, w, h):
    _sky(draw, x, y, w, h, (210, 205, 190), (232, 228, 214))
    # sawtooth factory
    draw.polygon([(x + w * 0.10, y + h * 0.88), (x + w * 0.10, y + h * 0.55),
                  (x + w * 0.30, y + h * 0.38), (x + w * 0.30, y + h * 0.55),
                  (x + w * 0.50, y + h * 0.38), (x + w * 0.50, y + h * 0.55),
                  (x + w * 0.70, y + h * 0.38), (x + w * 0.70, y + h * 0.88)],
                 fill=(90, 80, 70))
    draw.rectangle([x + w * 0.76, y + h * 0.28, x + w * 0.84, y + h * 0.88],
                   fill=(120, 60, 50))
    for sx, sy, sr in [(0.80, 0.18, 6), (0.86, 0.10, 8)]:
        draw.ellipse([x + w * sx - sr, y + h * sy - sr, x + w * sx + sr,
                      y + h * sy + sr], fill=(140, 140, 140))
    # flame
    draw.polygon([(x + w * 0.32, y + h * 0.55), (x + w * 0.38, y + h * 0.30),
                  (x + w * 0.44, y + h * 0.55)], fill=(240, 140, 30))


def icon_dove(draw, x, y, w, h):
    _sky(draw, x, y, w, h, (150, 190, 220), (210, 225, 235))
    # dove body + wing + head
    draw.ellipse([x + w * 0.22, y + h * 0.42, x + w * 0.72, y + h * 0.72],
                 fill=(255, 253, 247))
    draw.ellipse([x + w * 0.60, y + h * 0.30, x + w * 0.76, y + h * 0.48],
                 fill=(255, 253, 247))
    draw.polygon([(x + w * 0.74, y + h * 0.36), (x + w * 0.86, y + h * 0.40),
                  (x + w * 0.74, y + h * 0.44)], fill=(196, 145, 32))
    draw.ellipse([x + w * 0.68, y + h * 0.34, x + w * 0.70, y + h * 0.36],
                 fill=(20, 20, 20))
    draw.polygon([(x + w * 0.30, y + h * 0.50), (x + w * 0.55, y + h * 0.28),
                  (x + w * 0.62, y + h * 0.52)], fill=(235, 235, 235))
    # olive branch
    draw.line([x + w * 0.10, y + h * 0.82, x + w * 0.42, y + h * 0.72],
              fill=(46, 110, 71), width=2)
    for lx, ly in [(0.16, 0.80), (0.26, 0.77), (0.36, 0.74)]:
        draw.ellipse([x + w * lx - 3, y + h * ly - 2, x + w * lx + 3,
                      y + h * ly + 2], fill=(46, 110, 71))


def icon_basketball(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(196, 118, 0))
    cx, cy, r = x + w * 0.5, y + h * 0.52, h * 0.34
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(232, 122, 40))
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(90, 40, 10),
                 width=2)
    draw.line([cx - r, cy, cx + r, cy], fill=(90, 40, 10), width=2)
    draw.line([cx, cy - r, cx, cy + r], fill=(90, 40, 10), width=2)
    draw.arc([cx - r, cy - r * 0.4, cx + r * 0.4, cy + r], 270, 90,
             fill=(90, 40, 10), width=2)
    # hoop
    draw.arc([x + w * 0.68, y + h * 0.78, x + w * 0.92, y + h * 0.98], 0, 180,
             fill=(255, 253, 247), width=3)


ICONS = {
    "sunrise": icon_sunrise, "radar": icon_radar, "drones": icon_drones,
    "ballot": icon_ballot, "cricket": icon_cricket, "racecar": icon_racecar,
    "ship": icon_ship, "bolt": icon_bolt, "bottle": icon_bottle,
    "hospital": icon_hospital, "factory": icon_factory, "dove": icon_dove,
    "basketball": icon_basketball,
}

# ---------------------------------------------------------------- world map --
# Rough continent outlines in (lon, lat); drawn equirectangular.
CONTINENTS = [
    # North America
    [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-130, 54), (-125, 49),
     (-124, 42), (-120, 34), (-114, 29), (-110, 24), (-105, 20), (-97, 16),
     (-94, 17), (-90, 14), (-86, 12), (-83, 9), (-79, 9), (-81, 13),
     (-84, 16), (-87, 21), (-90, 21), (-91, 19), (-97, 26), (-93, 30),
     (-89, 30), (-84, 30), (-81, 25), (-80, 32), (-76, 35), (-74, 40),
     (-70, 42), (-68, 45), (-65, 44), (-60, 47), (-55, 52), (-60, 55),
     (-65, 58), (-68, 58), (-72, 62), (-78, 62), (-85, 66), (-92, 66),
     (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-162, 70)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-20, 74), (-25, 76), (-35, 77), (-50, 76), (-58, 74), (-62, 70)],
    # South America
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-70, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50), (-70, -54),
     (-66, -55), (-68, -50), (-65, -45), (-62, -41), (-58, -35), (-52, -32),
     (-48, -28), (-41, -23), (-39, -17), (-35, -9), (-35, -6), (-40, -3),
     (-44, -2), (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11),
     (-72, 12), (-76, 10)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-2, 49), (2, 51),
     (4, 53), (8, 55), (8, 57), (10, 59), (5, 60), (5, 62), (12, 64),
     (18, 69), (25, 71), (30, 70), (32, 68), (28, 66), (24, 64), (21, 60),
     (18, 56), (21, 54), (19, 54), (14, 54), (12, 54), (8, 54), (8, 57),
     (10, 57), (12, 55), (10, 54), (8, 53), (4, 52), (0, 50), (-2, 49),
     (-5, 48), (-2, 47), (-1, 44), (-3, 43), (-9, 43), (-9, 37), (-6, 36),
     (-2, 37), (0, 38), (3, 39), (3, 42), (7, 44), (10, 44), (12, 42),
     (16, 40), (18, 40), (16, 38), (12, 42), (8, 39), (3, 38), (0, 39),
     (-2, 37), (-6, 36)],
    # Africa
    [(-6, 35), (0, 36), (10, 37), (11, 34), (20, 32), (25, 32), (30, 31),
     (32, 31), (34, 28), (35, 24), (37, 20), (39, 15), (41, 11), (43, 11),
     (48, 11), (51, 12), (46, 5), (42, 0), (40, -5), (40, -10), (38, -15),
     (35, -20), (32, -26), (28, -32), (20, -35), (17, -32), (15, -27),
     (12, -18), (12, -10), (9, -1), (9, 4), (4, 6), (-8, 5), (-13, 8),
     (-17, 12), (-17, 15), (-16, 20), (-15, 25), (-10, 30)],
    # Asia (mainland, rough)
    [(30, 36), (36, 36), (36, 33), (42, 30), (44, 29), (48, 30), (50, 29),
     (54, 27), (57, 26), (58, 25), (61, 25), (62, 22), (66, 25), (67, 23),
     (70, 20), (72, 20), (75, 15), (77, 8), (80, 7), (80, 10), (82, 15),
     (85, 19), (88, 22), (91, 22), (93, 18), (94, 16), (97, 15), (98, 10),
     (100, 8), (103, 2), (104, 2), (100, 6), (98, 10), (97, 14), (94, 17),
     (92, 21), (89, 22), (86, 20), (83, 17), (80, 13), (78, 8), (76, 10),
     (74, 15), (72, 20), (69, 22), (66, 25), (62, 25), (58, 26), (56, 27),
     (54, 28), (52, 29), (50, 29), (48, 30), (44, 30), (42, 33), (40, 36),
     (36, 36), (33, 35), (30, 36), (28, 38), (26, 38), (23, 36), (26, 40),
     (28, 42), (30, 42), (33, 42), (36, 41), (38, 41), (41, 41), (42, 38),
     (39, 36)],
    # SE Asia islands (Sumatra, Java, Borneo, New Guinea, Philippines)
    [(95, 5), (98, 3), (100, 0), (103, -3), (106, -6), (110, -7), (114, -8),
     (114, -9), (110, -8), (106, -7), (103, -4), (100, -1), (97, 2), (95, 5)],
    [(109, -1), (112, -2), (115, -4), (117, -2), (117, 1), (114, 3),
     (111, 2), (109, -1)],
    [(131, -1), (136, -2), (140, -4), (141, -8), (137, -8), (132, -4)],
    [(122, 18), (122, 14), (120, 13), (121, 11), (122, 14), (124, 11),
     (122, 18)],
    # Australia
    [(113, -22), (114, -30), (115, -33), (118, -35), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -23), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -22)],
    # New Zealand
    [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38), (178, -37),
     (175, -40), (172, -43), (168, -46)],
    # UK + Ireland
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-3, 50)],
    [(-10, 52), (-10, 54), (-8, 55), (-6, 55), (-6, 52), (-8, 51), (-10, 52)],
    # Japan
    [(130, 31), (132, 33), (134, 34), (137, 35), (139, 35), (141, 38),
     (141, 41), (142, 44), (144, 44), (141, 42), (140, 39), (139, 37),
     (137, 35), (135, 34), (132, 32)],
]


def lonlat_to_xy(lon, lat, box):
    """Equirectangular: lon -180..180, lat 78..-58 -> box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    fx = (lon + 180.0) / 360.0
    fy = (78.0 - lat) / (78.0 + 58.0)
    return (x0 + fx * (x1 - x0), y0 + fy * (y1 - y0))


def draw_map(draw, box, pins):
    """Stylised world map with numbered pins. pins: list of (num, lat, lon)."""
    x0, y0, x1, y1 = box
    draw.rectangle([x0, y0, x1, y1], fill=(214, 228, 238))
    draw.rectangle([x0, y0, x1, y1], outline=LINE, width=1)
    # graticule
    for lon in range(-150, 181, 30):
        px, _ = lonlat_to_xy(lon, 0, box)
        draw.line([px, y0, px, y1], fill=(190, 205, 220), width=1)
    for lat in (-30, 0, 30, 60):
        _, py = lonlat_to_xy(0, lat, box)
        draw.line([x0, py, x1, py], fill=(190, 205, 220), width=1)
    # continents
    land = (232, 222, 196)
    for poly in CONTINENTS:
        pts = [lonlat_to_xy(lon, lat, box) for lon, lat in poly]
        draw.polygon(pts, fill=land, outline=(180, 168, 140))
    # pins
    for num, lat, lon in pins:
        px, py = lonlat_to_xy(lon, lat, box)
        r = 8
        draw.ellipse([px - r, py - r, px + r, py + r], fill=RED,
                     outline=(255, 253, 247), width=1)
        label = str(num)
        tw = text_w(draw, label, F["pin"])
        draw.text((px - tw / 2, py - 6), label, font=F["pin"],
                  fill=(255, 253, 247))


def tag_color(tag):
    if tag == "CLAIM":
        return (178, 34, 34)
    if tag == "FORECAST":
        return (196, 118, 0)
    return (46, 110, 71)


def draw_tag(draw, x, y, tag):
    """Small certainty tag chip; returns width used."""
    label = tag
    w = text_w(draw, label, F["tag"]) + 8
    draw.rectangle([x, y, x + w, y + 13], fill=tag_color(tag))
    draw.text((x + 4, y + 1), label, font=F["tag"], fill=(255, 253, 247))
    return w

# ------------------------------------------------------------ layout helpers --
FONT_FILES = {
    "serif_bold": "DejaVuSerif-Bold.ttf",
    "serif": "DejaVuSerif.ttf",
    "serif_italic": "DejaVuSerif-Italic.ttf",
    "sans": "DejaVuSans.ttf",
    "sans_bold": "DejaVuSans-Bold.ttf",
}

WARNINGS = []


def font_at(kind, size):
    return _load(FONT_FILES[kind], int(size))


def fit_text(draw, text, kind, base_size, max_width, max_lines, min_size=None):
    """Shrink font until text fits in max_lines; returns (font, lines)."""
    if min_size is None:
        min_size = base_size - 2
    size = base_size
    while size >= min_size:
        font = font_at(kind, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 1
    font = font_at(kind, min_size)
    return font, wrap_text(draw, text, font, max_width)[:max_lines]


# ------------------------------------------------------------------ sections --
def draw_masthead(draw):
    draw.rectangle([0, 0, W, 46], fill=NAVY)
    draw.text((16, 8), "THE WORLD IN ONE DAY", font=F["mast"], fill=(255, 253, 247))
    right = "35 STORIES \u00b7 7 REGIONS"
    draw.text((W - 16 - text_w(draw, right, F["mast_small"]), 14), right,
              font=F["mast_small"], fill=(200, 210, 225))
    draw.rectangle([0, 46, W, 49], fill=RED)


def draw_date_block(draw):
    title = "SUNDAY 22 NOVEMBER 2026"
    draw_centered(draw, W / 2, 54, title, F["date"], NAVY)
    sub = ("COP31 talks collapse \u00b7 Iran claims Bahrain strikes \u00b7 "
           "Russia\u2019s 186-drone barrage")
    draw_centered(draw, W / 2, 104, sub, F["sub"], RED_DARK)


def draw_stats(draw):
    y0, y1 = 122, 156
    draw.rectangle([16, y0, W - 16, y1], fill=PAPER, outline=LINE, width=1)
    col_w = (W - 32) / 6.0
    for i, (num, cap) in enumerate(STATS):
        cx = 16 + col_w * (i + 0.5)
        draw_centered(draw, cx, y0 + 2, num, F["stat_num"], RED)
        draw_centered(draw, cx, y0 + 28, cap, F["stat_cap"], GREY)
        if i:
            draw.line([16 + col_w * i, y0 + 4, 16 + col_w * i, y1 - 4],
                      fill=LINE, width=1)


def draw_regions(draw):
    y0 = 160
    total = sum(n for _, n in REGIONS)
    x = 16
    bar_w = W - 32
    for name, n in REGIONS:
        seg = bar_w * n / total
        draw.rectangle([x, y0, x + seg, y0 + 12],
                       fill=REGION_COLORS[name])
        x += seg
    # legend line
    parts, lx = [], 16
    draw.rectangle([16, y0 + 18, W - 16, y0 + 18], fill=CREAM)
    ly = y0 + 17
    cursor = 16
    for name, n in REGIONS:
        draw.rectangle([cursor, ly + 1, cursor + 8, ly + 9],
                       fill=REGION_COLORS[name])
        label = "%s %d" % (name, n)
        draw.text((cursor + 11, ly), label, font=F["region"], fill=INK)
        cursor += 11 + text_w(draw, label, F["region"]) + 14


def draw_timeline(draw):
    y = 186
    draw.line([16, y, W - 16, y], fill=LINE, width=1)
    x = 16
    draw.text((x, y + 4), "UTC", font=F["tag"], fill=RED)
    x += text_w(draw, "UTC", F["tag"]) + 8
    for time, label in TIMELINE:
        draw.text((x, y + 4), time, font=F["tag"], fill=NAVY)
        x += text_w(draw, time, F["tag"]) + 3
        draw.text((x, y + 4), label, font=F["timeline"], fill=INK)
        x += text_w(draw, label, F["timeline"], ) + 12
    draw.line([16, y + 20, W - 16, y + 20], fill=LINE, width=1)


def draw_big_lead(draw, lead, x, y, w, h):
    num, kicker, region, head, body, src, tag, _lat, _lon, icon = lead
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LINE, width=1)
    # pictorial panel
    pic_h = 94
    ICONS[icon](draw, x + 1, y + 1, w - 2, pic_h)
    # number badge on the pictorial
    badge = "1" if num == 1 else str(num)
    r = 12
    bx, by = x + 12, y + 10
    draw.ellipse([bx - r, by - r, bx + r, by + r], fill=RED,
                 outline=(255, 253, 247), width=2)
    tw = text_w(draw, badge, F["med_num"])
    draw.text((bx - tw / 2, by - 8), badge, font=F["med_num"],
              fill=(255, 253, 247))
    # tag chip on the pictorial (top right)
    tag_w = text_w(draw, tag, F["tag"]) + 8
    draw.rectangle([x + w - tag_w - 8, y + 8, x + w - 8, y + 21],
                   fill=tag_color(tag))
    draw.text((x + w - tag_w - 4, y + 9), tag, font=F["tag"],
              fill=(255, 253, 247))
    # kicker
    ky = y + pic_h + 8
    draw.text((x + 10, ky), kicker, font=F["kicker"], fill=RED)
    # headline (max 2 lines)
    font, lines = fit_text(draw, head, "serif_bold", 17, w - 20, 2, 15)
    hy = ky + 15
    for line in lines:
        draw.text((x + 10, hy), line, font=font, fill=NAVY)
        hy += font.size + 3
    # body (max 4 lines)
    font, lines = fit_text(draw, body, "sans", 11, w - 20, 4, 10)
    by = hy + 2
    for line in lines:
        draw.text((x + 10, by), line, font=font, fill=INK)
        by += font.size + 3
    if len(wrap_text(draw, body, font_at("sans", 10), w - 20)) > 4:
        WARNINGS.append("big lead %d body exceeds 4 lines" % num)
    # source line at the bottom
    draw.text((x + 10, y + h - 16), "Sources: " + src, font=F["lead_src"],
              fill=GREY)


def draw_medium(draw, lead, x, y, w, h):
    num, kicker, region, head, body, src, tag, _lat, _lon, icon = lead
    draw.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LINE, width=1)
    pic_h = 26
    ICONS[icon](draw, x + 1, y + 1, w - 2, pic_h)
    # number badge
    r = 10
    bx, by = x + 12, y + 13
    draw.ellipse([bx - r, by - r, bx + r, by + r], fill=NAVY,
                 outline=(255, 253, 247), width=1)
    label = str(num)
    tw = text_w(draw, label, F["med_num"])
    draw.text((bx - tw / 2, by - 7), label, font=F["med_num"],
              fill=(255, 253, 247))
    # headline (max 2 lines)
    font, lines = fit_text(draw, head, "sans_bold", 11, w - 14, 2, 10)
    hy = y + pic_h + 5
    for line in lines:
        draw.text((x + 7, hy), line, font=font, fill=NAVY)
        hy += font.size + 2
    # body (max 2 lines)
    font, lines = fit_text(draw, body, "sans", 9, w - 14, 2, 8)
    by = hy + 1
    for line in lines:
        draw.text((x + 7, by), line, font=font, fill=INK)
        by += font.size + 2
    if len(wrap_text(draw, body, font_at("sans", 8), w - 14)) > 2:
        WARNINGS.append("medium %d body exceeds 2 lines" % num)
    # tag at the bottom right
    if tag != "REPORTED":
        twd = draw_tag(draw, x + w - 4 - (text_w(draw, tag, F["tag"]) + 8),
                       y + h - 15, tag)


def draw_map_briefs(draw, y0, y1):
    # section header
    draw.text((16, y0), "WHERE IT HAPPENED", font=F["map_title"], fill=NAVY)
    draw.text((372, y0), "ALSO ON SUNDAY 22 NOVEMBER", font=F["map_title"],
              fill=NAVY)
    map_box = (16, y0 + 16, 360, y1)
    pins = [(n, lat, lon) for (n, _k, _r, _h, _b, _s, _t, lat, lon, _i)
            in LEADS]
    draw_map(draw, map_box, pins)
    # briefs, two columns
    col_x = [372, 688]
    col_w = 308
    items = BRIEFS
    half = 11
    for col in range(2):
        cx = col_x[col]
        cy = y0 + 16
        for item in items[col * half:(col + 1) * half]:
            num, region, head, body, tag = item
            # headline (bold, with number); tag chip inline after it
            hfont, hlines = fit_text(draw, "%d. %s" % (num, head),
                                     "sans_bold", 9, col_w, 1, 8)
            for line in hlines:
                draw.text((cx, cy), line, font=hfont, fill=NAVY)
                if tag != "REPORTED":
                    twd = text_w(draw, tag, F["tag"]) + 8
                    draw_tag(draw, cx + text_w(draw, line, hfont) + 6,
                             cy - 1, tag)
                cy += hfont.size + 1
            # body
            bfont, blines = fit_text(draw, body, "sans", 9, col_w, 1, 8)
            for line in blines:
                draw.text((cx, cy), line, font=bfont, fill=INK)
                cy += bfont.size + 1
            cy += 1
            if len(wrap_text(draw, body, font_at("sans", 8), col_w)) > 1:
                WARNINGS.append("brief %d body exceeds 1 line" % num)


def draw_date_check(draw, y0, y1):
    draw.rectangle([16, y0, W - 16, y1], outline=RED, width=2)
    draw.rectangle([16, y0, W - 16, y0 + 20], fill=RED)
    draw.text((26, y0 + 3),
              "DATE CHECK \u2014 NOT SUNDAY 22 NOVEMBER",
              font=F["dc_title"], fill=(255, 253, 247))
    draw.text((W - 26 - text_w(draw, "first reported earlier, or not yet happened",
                                F["dc_item"]),
               y0 + 4), "first reported earlier, or not yet happened",
              font=F["dc_item"], fill=(255, 220, 220))
    # two columns of 5
    col_w = (W - 32 - 40) / 2.0
    for i, item in enumerate(DATE_CHECK):
        col = i // 5
        row = i % 5
        x = 26 + col * (col_w + 20)
        yy = y0 + 26 + row * 9.5
        draw.text((x, yy), "\u2715  %s" % item, font=F["dc_item"], fill=INK)


def draw_footer(draw, y0):
    draw.line([16, y0, W - 16, y0], fill=LINE, width=1)
    legend = ("REPORTED = carried by the day\u2019s wires   \u00b7   CLAIM = one side\u2019s "
              "account, labelled as such   \u00b7   FORECAST = still to happen when drawn")
    draw_centered(draw, W / 2, y0 + 6, legend, F["footer"], GREY)
    srcs = ("Sources: Reuters \u00b7 AP \u00b7 BBC \u00b7 Al Jazeera \u00b7 Xinhua \u00b7 "
            "ESPNcricinfo \u00b7 F1.com \u00b7 PHIVOLCS \u00b7 info.gov.hk \u00b7 SPA \u00b7 "
            "CENTCOM \u00b7 UKMTO \u00b7 Kyiv Independent \u00b7 SCMP")
    draw_centered(draw, W / 2, y0 + 20, srcs, F["footer"], GREY)
    draw_centered(draw, W / 2, y0 + 32,
                  "Drawn Sunday 22 November 2026 \u00b7 35 stories \u00b7 7 regions",
                  F["footer"], GREY)


# --------------------------------------------------------------------- main ---
def render():
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    draw_masthead(draw)
    draw_date_block(draw)
    draw_stats(draw)
    draw_regions(draw)
    draw_timeline(draw)
    # 3 big leads
    big = LEADS[:3]
    bw = (W - 32 - 20) / 3.0
    for i, lead in enumerate(big):
        draw_big_lead(draw, lead, 16 + i * (bw + 10), 210, bw, 236)
    # 10 medium cards, 2 rows x 5
    med = LEADS[3:]
    mw = (W - 32 - 4 * 8) / 5.0
    for i, lead in enumerate(med):
        row, col = divmod(i, 5)
        draw_medium(draw, lead, 16 + col * (mw + 8), 452 + row * 98,
                    mw, 94)
    draw_map_briefs(draw, 648, 896)
    draw_date_check(draw, 898, 972)
    draw_footer(draw, 976)
    return img


def _output_path():
    d = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if d:
        return os.path.join(d, "entry.png")
    out = os.environ.get("ENTRY_OUTPUT")
    if out:
        return out
    return "/output/entry.png"


def _copy_committed(out):
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")
    if os.path.abspath(src) == os.path.abspath(out):
        print("entry.png already in place at %s" % out)
        return
    parent = os.path.dirname(out)
    if parent:
        os.makedirs(parent, exist_ok=True)
    shutil.copyfile(src, out)
    print("copied %s -> %s (%d bytes)" % (src, out, os.path.getsize(out)))


def main():
    out = _output_path()
    if _PIL_OK:
        try:
            img = render()
            parent = os.path.dirname(out)
            if parent:
                os.makedirs(parent, exist_ok=True)
            img.save(out, format="PNG")
            print("wrote %s (%d bytes)" % (out, os.path.getsize(out)))
            for warn in WARNINGS:
                print("WARNING: %s" % warn, file=sys.stderr)
            return 0
        except Exception as e:
            print("render failed (%s); falling back to committed entry.png" % e,
                  file=sys.stderr)
    try:
        _copy_committed(out)
        return 0
    except Exception as e:
        print("primary output failed (%s); trying ./entry.png" % e, file=sys.stderr)
    try:
        _copy_committed("entry.png")
        return 0
    except Exception as e:
        print("fallback failed: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
