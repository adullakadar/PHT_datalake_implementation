#!/usr/bin/env python3
"""
Piplodwala Hardware Trading LLC (PHT) - ISIT312 SIMULATED dataset generator, v6 (real TallyPrime export formats).

Based on the company brief: 3 branches (Sharjah 1, Sharjah 2, Dubai 1) each running its
own TallyPrime, 1 warehouse whose stock only Sharjah 1 can see, manual stock transfers
(pink slip + two separate vouchers), ~150 customers/day company-wide, ~50,000 SKUs,
8 years of history, supplier documents arriving in many formats. Scenario: a 4th branch
in Ajman.

All records are synthetic. Names of customers/suppliers are fictional.
Core data: Python 3.4+ standard library only.  Supplier PDFs need reportlab (optional).

    python3 generate_data.py          -> ./data/
"""
import csv, json, math, os, random, bisect
from datetime import date, datetime, timedelta

SEED = 3122026
R = random.Random(SEED)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
START, END = date(2019, 7, 1), date(2026, 10, 31)
STREAM_DAY = date(2027, 2, 1)                       # Ajman branch opening day (Monday)

BRANCHES = ["SHJ1", "DB1", "SHJ2"]
OPEN = {"SHJ1": date(2019, 7, 1), "DB1": date(2021, 4, 1), "SHJ2": date(2023, 2, 1)}
WH = "WH1"
BRANCH_SHARE = [0.45, 0.33, 0.22]                   # SHJ1 > DB1 > SHJ2
STOCKED_SKUS = {"SHJ1": 22000, "DB1": 15000, "SHJ2": 10000}

# ======================================================================= helpers
def path(*p):
    d = os.path.join(OUT, *p[:-1])
    if not os.path.isdir(d):
        os.makedirs(d)
    return os.path.join(d, p[-1])

def write_csv(fp, header, rows):
    with open(fp, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)

class Weighted(object):
    def __init__(self, items, weights):
        self.items, self.cum, t = list(items), [], 0.0
        for w in weights:
            t += w
            self.cum.append(t)
        self.total = t
    def pick(self, rng=None):
        return self.items[bisect.bisect_right(self.cum, (rng or R).random() * self.total)]

def poisson(lam):
    if lam <= 0:
        return 0
    if lam > 50:
        return max(0, int(round(R.gauss(lam, math.sqrt(lam)))))
    L, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= R.random()
        if p <= L:
            return k
        k += 1

def money(x):
    return "%.2f" % x

# ======================================================================= catalogue (~50k SKUs)
MAT_PRICE = {"SS304": 1.0, "SS316": 1.45, "Galvanized": 0.55, "Zinc Plated": 0.45, "Grade 8.8 Black": 0.5,
             "Grade 12.9 Black": 0.7, "Ungalvanized": 0.45, "Grade 80": 1.1, "Brass": 1.3, "Spring Steel": 0.6}
MAT_POP = {"SS304": 1.0, "SS316": 1.3, "Galvanized": 0.9, "Zinc Plated": 0.5, "Grade 8.8 Black": 0.4,
           "Grade 12.9 Black": 0.3, "Ungalvanized": 0.4, "Grade 80": 0.5, "Brass": 0.25, "Spring Steel": 0.5}
MAT_SHORT = {"SS304": "ss304", "SS316": "ss316", "Galvanized": "galv", "Zinc Plated": "zp",
             "Grade 8.8 Black": "8.8 blk", "Grade 12.9 Black": "12.9 blk", "Ungalvanized": "ungalv",
             "Grade 80": "g80", "Brass": "brass", "Spring Steel": "spr stl"}

def threads_lengths(threads, lengths, lo=2.0, hi=10.0):
    out = []
    for t in threads:
        for l in lengths:
            if lo * t <= l <= hi * t:
                out.append(("M%dx%d" % (t, l), (t / 10.0) ** 2.2 * (l / 50.0) ** 0.7, 1.0 / (1 + abs(t - 10) / 4.0)))
    return out

def diam(ds, unit="mm", e=1.8, centre=10.0):
    return [("%s%s" % (("%g" % d), unit), (d / float(centre)) ** e, 1.0 / (1 + abs(d - centre) / centre)) for d in ds]

def threads(ts):
    return [("M%d" % t, (t / 10.0) ** 2.0, 1.0 / (1 + abs(t - 10) / 4.0)) for t in ts]

def pins(ds, ls):
    out = []
    for d in ds:
        for l in ls:
            if 3 * d <= l <= 16 * d:
                out.append(("%gx%dmm" % (d, l), (d / 5.0) ** 1.6 * (l / 40.0) ** 0.5, 1.0 / (1 + abs(d - 4) / 3.0)))
    return out

def springs():
    out = []
    for wd in [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0]:
        for od in [5, 8, 10, 12, 16, 20, 25, 32, 40, 50]:
            if od < 4 * wd or od > 20 * wd:
                continue
            for L in [10, 15, 20, 25, 30, 40, 50, 60, 80, 100]:
                out.append(("%gx%dx%dmm" % (wd, od, L), (wd / 1.5) ** 1.5 * (L / 30.0) ** 0.5, 0.5))
    return out

THR_S = [3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 27, 30]
LEN_S = [6, 8, 10, 12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 90, 100, 110, 120, 130, 140,
         150, 160, 180, 200, 220, 250, 300]
FST_MATS = ["SS304", "SS316", "Galvanized", "Zinc Plated", "Grade 8.8 Black"]
PIN_MATS = ["SS304", "SS316", "Zinc Plated"]
RIG_MATS = ["SS304", "SS316", "Galvanized"]
PACK_SMALL = [("", "Nos", 1.0, 1.0), ("Box/100", "Box", 85.0, 0.5), ("Box/500", "Box", 400.0, 0.15)]
PACK_BIG = [("", "Nos", 1.0, 1.0), ("Box/50", "Box", 45.0, 0.4)]
PACK_PIN = [("", "Nos", 1.0, 1.0), ("Box/100", "Box", 80.0, 0.5)]
PACK_NONE = [("", "Nos", 1.0, 1.0)]
ORIGINS = [("", 1.0, 1.0), ("DE", 1.9, 0.12)]                     # standard / German-made line
# (category, type, materials, specs, packs, origins, base price AED for SS304 at size_mult 1, popularity boost)
TYPES = [
    ("Fasteners - Bolts & Screws", "Hex Bolt DIN933", FST_MATS, threads_lengths(THR_S[2:13], LEN_S), "auto", ORIGINS, 1.4, 1.0),
    ("Fasteners - Bolts & Screws", "Hex Bolt DIN931", FST_MATS, threads_lengths(THR_S[2:14], LEN_S, 3, 12), "auto", ORIGINS, 1.5, 0.8),
    ("Fasteners - Bolts & Screws", "Socket Cap Screw DIN912", ["SS304", "SS316", "Zinc Plated", "Grade 12.9 Black"], threads_lengths(THR_S[0:11], LEN_S), "auto", ORIGINS, 1.3, 0.6),
    ("Fasteners - Bolts & Screws", "CSK Socket Screw DIN7991", ["SS304", "SS316", "Zinc Plated"], threads_lengths(THR_S[0:9], LEN_S), "auto", ORIGINS, 1.2, 0.4),
    ("Fasteners - Bolts & Screws", "Button Head Screw ISO7380", ["SS304", "SS316", "Zinc Plated"], threads_lengths(THR_S[0:8], LEN_S, 2, 8), "auto", ORIGINS, 1.2, 0.3),
    ("Fasteners - Bolts & Screws", "Carriage Bolt DIN603", ["SS304", "SS316", "Galvanized"], threads_lengths(THR_S[2:9], LEN_S, 3, 12), "auto", ORIGINS, 1.3, 0.3),
    ("Fasteners - Bolts & Screws", "Pan Head Machine Screw ISO7045", ["SS304", "SS316", "Zinc Plated"], threads_lengths(THR_S[0:6], LEN_S, 1.5, 10), "auto", ORIGINS, 0.6, 0.5),
    ("Fasteners - Bolts & Screws", "Threaded Rod DIN975 1m", FST_MATS, threads(THR_S[1:13]), PACK_NONE, ORIGINS, 22, 0.8),
    ("Fasteners - Bolts & Screws", "Set Screw Cup Point DIN916", ["SS304", "SS316", "Grade 12.9 Black"], threads_lengths(THR_S[0:8], LEN_S, 1, 5), "auto", ORIGINS, 0.5, 0.3),
    ("Fasteners - Bolts & Screws", "Hex Flange Bolt DIN6921", ["SS304", "Zinc Plated", "Grade 8.8 Black"], threads_lengths(THR_S[2:9], LEN_S, 2, 8), "auto", ORIGINS, 1.5, 0.3),
    ("Fasteners - Bolts & Screws", "Hex Lag Screw DIN571", ["SS304", "SS316", "Galvanized"], threads_lengths(THR_S[2:9], LEN_S, 4, 15), "auto", ORIGINS, 1.2, 0.3),
    ("Fasteners - Bolts & Screws", "U-Bolt", ["SS304", "SS316", "Galvanized"], threads_lengths(THR_S[2:9], [25, 32, 40, 50, 60, 75, 90, 110, 125, 160, 200], 4, 25), PACK_NONE, ORIGINS, 6, 0.6),
    ("Fasteners - Nuts & Washers", "Coupling Nut DIN6334", ["SS304", "SS316", "Zinc Plated"], threads(THR_S[1:11]), "auto", ORIGINS, 2.0, 0.3),
    ("Fasteners - Nuts & Washers", "Flange Nut DIN6923", ["SS304", "Zinc Plated", "Grade 8.8 Black"], threads(THR_S[1:10]), "auto", ORIGINS, 0.7, 0.4),
    ("Fasteners - Anchors", "Blind Rivet Dome Head", ["SS304", "SS316", "Zinc Plated"], pins([3.2, 4.0, 4.8, 6.4], [6, 8, 10, 12, 14, 16, 20, 25, 30]), PACK_SMALL, ORIGINS, 0.2, 0.5),
    ("Fasteners - Nuts & Washers", "Hex Nut DIN934", FST_MATS, threads(THR_S), "auto", ORIGINS, 0.6, 2.0),
    ("Fasteners - Nuts & Washers", "Nylock Nut DIN985", ["SS304", "SS316", "Zinc Plated"], threads(THR_S[0:12]), "auto", ORIGINS, 0.9, 1.2),
    ("Fasteners - Nuts & Washers", "Dome Nut DIN1587", ["SS304", "SS316"], threads(THR_S[1:11]), "auto", ORIGINS, 1.4, 0.4),
    ("Fasteners - Nuts & Washers", "Wing Nut DIN315", ["SS304", "SS316", "Zinc Plated"], threads(THR_S[1:9]), "auto", ORIGINS, 1.5, 0.4),
    ("Fasteners - Nuts & Washers", "Flat Washer DIN125", FST_MATS, threads(THR_S), "auto", ORIGINS, 0.25, 1.8),
    ("Fasteners - Nuts & Washers", "Spring Washer DIN127", ["SS304", "SS316", "Zinc Plated"], threads(THR_S[0:12]), "auto", ORIGINS, 0.25, 1.0),
    ("Fasteners - Nuts & Washers", "Fender Washer DIN9021", ["SS304", "SS316", "Zinc Plated"], threads(THR_S[0:10]), "auto", ORIGINS, 0.4, 0.6),
    ("Fasteners - Self Tapping & Wood Screws", "Self Tapping Pan DIN7981", ["SS304", "SS316", "Zinc Plated"], pins([2.9, 3.5, 3.9, 4.2, 4.8, 5.5, 6.3], [9, 13, 16, 19, 22, 25, 32, 38, 45, 50, 60]), PACK_SMALL, ORIGINS, 0.3, 0.8),
    ("Fasteners - Self Tapping & Wood Screws", "Self Tapping CSK DIN7982", ["SS304", "SS316", "Zinc Plated"], pins([2.9, 3.5, 3.9, 4.2, 4.8, 5.5, 6.3], [9, 13, 16, 19, 22, 25, 32, 38, 45, 50, 60]), PACK_SMALL, ORIGINS, 0.3, 0.6),
    ("Fasteners - Self Tapping & Wood Screws", "Wood Screw CSK", ["SS304", "SS316", "Zinc Plated"], pins([3.0, 3.5, 4.0, 4.5, 5.0, 6.0], [16, 20, 25, 30, 35, 40, 50, 60, 70, 80, 100]), PACK_SMALL, ORIGINS, 0.35, 0.5),
    ("Fasteners - Anchors", "Sleeve Anchor", ["SS304", "SS316", "Zinc Plated"], threads_lengths([6, 8, 10, 12, 16], LEN_S, 6, 15), PACK_BIG, ORIGINS, 3.5, 0.5),
    ("Fasteners - Anchors", "Wedge Anchor", ["SS304", "SS316", "Zinc Plated"], threads_lengths([6, 8, 10, 12, 16, 20], LEN_S, 6, 15), PACK_BIG, ORIGINS, 3.8, 0.5),
    ("Industrial Pins & Retaining Fasteners", "Cotter Pin DIN94", PIN_MATS, pins([1.0, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.3, 8.0, 10.0], [10, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160]), PACK_PIN, ORIGINS, 0.6, 1.5),
    ("Industrial Pins & Retaining Fasteners", "Clevis Pin DIN1444", PIN_MATS, pins([4, 5, 6, 8, 10, 12, 14, 16, 20], [16, 20, 25, 30, 40, 50, 60, 80, 100, 120, 160]), PACK_PIN, ORIGINS, 2.2, 0.8),
    ("Industrial Pins & Retaining Fasteners", "Spring Roll Pin DIN1481", ["SS304", "SS316", "Spring Steel"], pins([1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12, 13], [8, 10, 12, 16, 20, 25, 30, 35, 40, 50, 60, 80, 100]), PACK_PIN, ORIGINS, 0.3, 0.8),
    ("Industrial Pins & Retaining Fasteners", "Dowel Pin ISO2338", ["SS304", "SS316"], pins([2, 3, 4, 5, 6, 8, 10, 12, 16], [8, 10, 12, 16, 20, 25, 30, 40, 50, 60]), PACK_PIN, ORIGINS, 0.4, 0.5),
    ("Industrial Pins & Retaining Fasteners", "Ball Lock Quick Release Pin", ["SS304", "SS316"], pins([5, 6, 8, 10, 12, 16], [20, 30, 40, 50, 60, 80, 100]), PACK_NONE, ORIGINS, 18, 0.9),
    ("Industrial Pins & Retaining Fasteners", "R Clip Safety Pin", PIN_MATS, diam([1.2, 1.6, 2, 2.5, 3, 4, 5, 6], centre=3), PACK_PIN, ORIGINS, 0.6, 1.4),
    ("Industrial Pins & Retaining Fasteners", "Lynch Pin", PIN_MATS, diam([4.5, 6, 8, 9, 11, 12], centre=8), PACK_NONE, ORIGINS, 3.5, 0.7),
    ("Industrial Pins & Retaining Fasteners", "Circlip External DIN471", ["SS304", "Spring Steel"], diam(list(range(8, 61, 2)), centre=20), PACK_PIN, ORIGINS, 0.4, 0.4),
    ("Industrial Pins & Retaining Fasteners", "Circlip Internal DIN472", ["SS304", "Spring Steel"], diam(list(range(10, 63, 2)), centre=24), PACK_PIN, ORIGINS, 0.45, 0.3),
    ("Shackles & Rigging Hardware", "D Shackle", RIG_MATS, diam([4, 5, 6, 8, 10, 12, 14, 16, 19, 22, 25, 28, 32], centre=8), PACK_NONE, ORIGINS, 6, 4.0),
    ("Shackles & Rigging Hardware", "Bow Shackle", RIG_MATS, diam([4, 5, 6, 8, 10, 12, 14, 16, 19, 22, 25, 28, 32], centre=8), PACK_NONE, ORIGINS, 6.5, 3.5),
    ("Shackles & Rigging Hardware", "Long D Shackle", ["SS304", "SS316"], diam([4, 5, 6, 8, 10, 12, 16], centre=6), PACK_NONE, ORIGINS, 7, 1.0),
    ("Shackles & Rigging Hardware", "Twisted Shackle", ["SS304", "SS316"], diam([4, 5, 6, 8, 10, 12], centre=6), PACK_NONE, ORIGINS, 7.5, 0.6),
    ("Shackles & Rigging Hardware", "Snap Hook DIN5299 Form C", RIG_MATS, diam([4, 5, 6, 7, 8, 9, 10, 11, 12, 13], centre=8), PACK_NONE, ORIGINS, 3.5, 3.0),
    ("Shackles & Rigging Hardware", "Snap Hook with Eyelet DIN5299D", ["SS304", "SS316"], diam([5, 6, 7, 8, 10, 11, 12], centre=8), PACK_NONE, ORIGINS, 4.0, 1.5),
    ("Shackles & Rigging Hardware", "Swivel Snap Hook", ["SS304", "SS316"], diam([50, 60, 70, 80, 90, 100, 120], centre=80), PACK_NONE, ORIGINS, 12, 0.8),
    ("Shackles & Rigging Hardware", "Quick Link", RIG_MATS, diam([3, 3.5, 4, 5, 6, 7, 8, 10, 12, 14], centre=6), PACK_NONE, ORIGINS, 2.5, 2.5),
    ("Shackles & Rigging Hardware", "S Hook", RIG_MATS, diam([3, 4, 5, 6, 8, 10, 12, 16], centre=6), PACK_PIN, ORIGINS, 1.2, 1.5),
    ("Shackles & Rigging Hardware", "Eye Bolt DIN580", RIG_MATS, threads([6, 8, 10, 12, 16, 20, 24, 30]), PACK_NONE, ORIGINS, 6, 2.5),
    ("Shackles & Rigging Hardware", "Eye Nut DIN582", RIG_MATS, threads([6, 8, 10, 12, 16, 20, 24, 30]), PACK_NONE, ORIGINS, 6, 2.0),
    ("Shackles & Rigging Hardware", "Turnbuckle Jaw-Jaw", RIG_MATS, threads([5, 6, 8, 10, 12, 16, 20, 24]), PACK_NONE, ORIGINS, 14, 2.0),
    ("Shackles & Rigging Hardware", "Turnbuckle Eye-Eye", RIG_MATS, threads([5, 6, 8, 10, 12, 16, 20, 24]), PACK_NONE, ORIGINS, 13, 1.5),
    ("Shackles & Rigging Hardware", "Turnbuckle Hook-Eye", RIG_MATS, threads([5, 6, 8, 10, 12, 16, 20]), PACK_NONE, ORIGINS, 13, 1.2),
    ("Shackles & Rigging Hardware", "Swivel Eye-Eye", RIG_MATS, diam([5, 6, 8, 10, 12, 16], centre=8), PACK_NONE, ORIGINS, 11, 1.0),
    ("Shackles & Rigging Hardware", "Single Sheave Pulley Block", RIG_MATS, diam([15, 20, 25, 32, 38, 50, 75], centre=32), PACK_NONE, ORIGINS, 22, 1.0),
    ("Shackles & Rigging Hardware", "Double Sheave Pulley Block", ["SS304", "SS316"], diam([20, 25, 32, 38, 50], centre=32), PACK_NONE, ORIGINS, 40, 0.5),
    ("Shackles & Rigging Hardware", "Ball (Drilled) for Rigging", ["SS304", "SS316"], diam([10, 12, 16, 20, 25, 30, 40], centre=20), PACK_NONE, ORIGINS, 4, 0.4),
    ("Wire Rope & Fittings", "Wire Rope Clip DIN741", RIG_MATS, diam([3, 4, 5, 6, 8, 10, 12, 14, 16, 19, 22, 26], centre=8), PACK_NONE, ORIGINS, 2.0, 3.0),
    ("Wire Rope & Fittings", "Duplex Wire Rope Clip", ["SS304", "SS316"], diam([3, 4, 5, 6, 8, 10, 12], centre=6), PACK_NONE, ORIGINS, 3.5, 1.2),
    ("Wire Rope & Fittings", "Wire Rope Thimble DIN6899", RIG_MATS, diam([3, 4, 5, 6, 8, 10, 12, 14, 16, 19, 22, 26], centre=8), PACK_NONE, ORIGINS, 1.2, 2.5),
    ("Wire Rope & Fittings", "Swage Terminal Eye", ["SS316"], diam([3, 4, 5, 6, 8, 10, 12], centre=6), PACK_NONE, ORIGINS, 15, 0.8),
    ("Wire Rope & Fittings", "Swage Terminal Fork", ["SS316"], diam([3, 4, 5, 6, 8, 10, 12], centre=6), PACK_NONE, ORIGINS, 17, 0.6),
    ("Hinges, Locks & Handles", "Butt Hinge", ["SS304", "SS316", "Brass"], diam([50, 63, 75, 89, 100, 125, 150], centre=100), PACK_NONE, ORIGINS, 6, 0.8),
    ("Hinges, Locks & Handles", "Strap Hinge Marine", ["SS316"], diam([50, 75, 100, 150], centre=75), PACK_NONE, ORIGINS, 12, 0.4),
    ("Hinges, Locks & Handles", "Pull Handle", ["SS304", "SS316"], diam([96, 128, 160, 200, 300, 400, 600], centre=200), PACK_NONE, ORIGINS, 9, 0.6),
    ("Hinges, Locks & Handles", "Padlock", ["SS304", "Brass"], diam([30, 40, 50, 60, 70], centre=50), PACK_NONE, ORIGINS, 25, 0.4),
    ("Hinges, Locks & Handles", "Hasp and Staple", ["SS304", "SS316", "Galvanized"], diam([75, 100, 125, 150], centre=100), PACK_NONE, ORIGINS, 8, 0.3),
    ("Hinges, Locks & Handles", "Tower Bolt", ["SS304", "Brass"], diam([75, 100, 150, 200, 250, 300], centre=150), PACK_NONE, ORIGINS, 6, 0.3),
    ("Springs", "Compression Spring", ["SS304", "Spring Steel"], springs(), PACK_NONE, ORIGINS[:1], 2.0, 0.25),
    ("Springs", "Extension Spring", ["SS304", "Spring Steel"], springs(), PACK_NONE, ORIGINS[:1], 2.4, 0.15),
    ("Marine Fittings", "Mooring Cleat", ["SS316"], diam([100, 125, 150, 200, 250, 300], centre=150), PACK_NONE, ORIGINS, 20, 0.6),
    ("Marine Fittings", "Deck Eye Plate", ["SS316"], diam([5, 6, 8, 10, 12], centre=8), PACK_NONE, ORIGINS, 7, 0.6),
    ("Marine Fittings", "Pad Eye", ["SS316"], diam([5, 6, 8, 10], centre=6), PACK_NONE, ORIGINS, 8, 0.4),
    ("Marine Fittings", "Bimini Top Fitting", ["SS316"], diam([22, 25], centre=25), PACK_NONE, ORIGINS, 12, 0.3),
]
WIRE_CONSTR = [("Wire Rope 1x19", ["SS316", "SS304"], [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12], 2.5),
               ("Wire Rope 7x7", ["SS316", "SS304", "Galvanized"], [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12], 2.5),
               ("Wire Rope 7x19", ["SS316", "SS304", "Galvanized"], [2, 3, 4, 5, 6, 8, 10, 12, 14, 16], 2.5),
               ("Wire Rope 6x19 FC", ["Galvanized", "Ungalvanized"], [6, 8, 10, 12, 14, 16, 18, 20, 22, 24], 1.5),
               ("Wire Rope 6x19 IWRC", ["SS316", "Galvanized", "Ungalvanized"], [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32], 2.0),
               ("Wire Rope 6x36 IWRC", ["Galvanized", "Ungalvanized"], [10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 36], 1.2),
               ("Wire Rope 7x19 PVC Coated", ["Galvanized", "SS304"], [2, 3, 4, 5, 6, 8], 1.0)]
CHAIN_TYPES = [("Short Link Chain DIN766", ["SS316", "Galvanized"], [3, 4, 5, 6, 7, 8, 10, 13, 16], 2.0),
               ("Long Link Chain DIN763", ["SS316", "SS304", "Galvanized"], [2, 3, 4, 5, 6, 8, 10], 1.5),
               ("Grade 80 Lifting Chain", ["Grade 80"], [6, 7, 8, 10, 13, 16, 20, 22], 0.8),
               ("Stud Link Anchor Chain", ["Galvanized"], [12.5, 14, 16, 19, 22, 26], 0.3)]

catalogue = []
def add_sku(cat, typ, mat, spec, pack, uom, packmult, origin, price, pop):
    catalogue.append(dict(cat=cat, typ=typ, mat=mat, spec=spec, pack=pack, uom=uom, origin=origin,
                          price=round(max(0.15, price), 2), pop=pop))

for cat, typ, mats, specs, packs, origins, base, boost in TYPES:
    for mat in mats:
        for spec, smult, spop in specs:
            if packs == "auto":
                big = spec.startswith("M") and int(spec[1:].split("x")[0]) >= 16
                pk = PACK_BIG if big else PACK_SMALL
            else:
                pk = packs
            for pack, uom, pmult, ppop in pk:
                for org, omult, opop in origins:
                    price = base * smult * MAT_PRICE[mat] * pmult * omult * R.uniform(0.9, 1.1)
                    pop = R.paretovariate(1.15) * boost * spop * MAT_POP[mat] * ppop * opop
                    add_sku(cat, typ, mat, spec, pack, uom, pmult, org, price, pop)
for typ, mats, ds, boost in WIRE_CONSTR:
    for mat in mats:
        for d in ds:
            sm = (d / 10.0) ** 1.9
            for pack, uom, pmult, ppop in [("", "Mtr", 1.0, 1.0), ("Reel/100m", "Reel", 92.0, 0.08),
                                           ("Reel/500m", "Reel", 440.0, 0.03)]:
                price = 9.0 * sm * MAT_PRICE[mat] * pmult * R.uniform(0.9, 1.1)
                pop = R.paretovariate(1.15) * boost * MAT_POP[mat] * ppop / (1 + abs(d - 8) / 6.0)
                add_sku("Wire Rope & Fittings", typ, mat, "%gmm" % d, pack, uom, pmult, "", price, pop)
for typ, mats, ds, boost in CHAIN_TYPES:
    for mat in mats:
        for d in ds:
            sm = (d / 8.0) ** 2.0
            for pack, uom, pmult, ppop in [("", "Mtr", 1.0, 1.0), ("Drum/50m", "Drum", 46.0, 0.06)]:
                price = 22.0 * sm * MAT_PRICE[mat] * pmult * R.uniform(0.9, 1.1)
                pop = R.paretovariate(1.15) * boost * MAT_POP[mat] * ppop / (1 + abs(d - 6) / 5.0)
                add_sku("Chains", typ, mat, "%gmm" % d, pack, uom, pmult, "", price, pop)

_pops = sorted(p["pop"] for p in catalogue)
_cap = _pops[int(len(_pops) * 0.995)]
for p in catalogue:
    p["pop"] = min(p["pop"], _cap * (1 + 0.5 * R.random()))   # no single item dominates the business
R.shuffle(catalogue)
for i, p in enumerate(catalogue):
    p["id"] = "PHT-%05d" % (i + 1)
    p["cost"] = round(p["price"] * (1 - R.uniform(0.22, 0.42)), 2)
    p["code_compact"] = p["id"].replace("-", "")
    if p["pop"] < 0.05 and R.random() < 0.5:        # long tail: many items hardly ever move
        p["pop"] *= 0.1
PRODUCT = dict((p["id"], p) for p in catalogue)

def canon_name(p):
    s = "%s %s %s" % (p["mat"], p["typ"], p["spec"])
    if p["pack"]:
        s += " %s" % p["pack"]
    if p["origin"]:
        s += " [%s]" % p["origin"]
    return s

def name_style(p, style):
    """Each branch's Tally names stock items in its own way (no shared item master)."""
    if style == "canon":
        return canon_name(p)
    if style == "upper":                       # SHJ2: type first, material last, upper case
        s = "%s %s %s" % (p["typ"], p["spec"], p["mat"])
        if p["pack"]:
            s += " /%s" % p["pack"].replace("Box/", "BX").replace("Reel/", "RL").replace("Drum/", "DR")
        if p["origin"]:
            s += " (%s)" % p["origin"]
        return s.upper()
    s = "%s %s %s" % (MAT_SHORT[p["mat"]], p["typ"].lower().replace(" ", "-"), p["spec"])   # DB1
    if p["pack"]:
        s += " %s" % p["pack"].lower()
    if p["origin"]:
        s += " %s" % p["origin"].lower()
    return s

for p in catalogue:
    p["names"] = {"SHJ1": name_style(p, "canon"), "SHJ2": name_style(p, "upper"), "DB1": name_style(p, "lower")}

# ======================================================================= suppliers
# (name, location, country, type, lead range, late prob, delay range, document channel)
SUPPLIER_SPECS = [
    ("Deira Wire Rope Trading", "Deira, Dubai", "UAE", "Wholesaler", (1, 3), 0.10, (1, 5), "pdf"),
    ("Al Ras Rigging Supplies", "Al Ras, Dubai", "UAE", "Wholesaler", (1, 2), 0.12, (1, 4), "whatsapp"),
    ("Creekside Marine Hardware", "Deira, Dubai", "UAE", "Wholesaler", (1, 3), 0.15, (1, 6), "whatsapp"),
    ("Naif Fasteners & Tools", "Naif, Dubai", "UAE", "Wholesaler", (1, 2), 0.08, (1, 3), "csv"),
    ("Industrial Area Bolt House", "Industrial Area 6, Sharjah", "UAE", "Wholesaler", (1, 2), 0.10, (1, 4), "csv"),
    ("Sharjah Industrial Rigging", "Industrial Area 4, Sharjah", "UAE", "Wholesaler", (1, 3), 0.20, (1, 6), "pdf"),
    ("Hamriyah Marine Supplies", "Hamriyah Free Zone, Sharjah", "UAE", "Distributor", (2, 5), 0.25, (2, 9), "email"),
    ("Jebel Ali Steel Wire Distribution", "Jebel Ali Free Zone", "UAE", "Distributor", (3, 6), 0.20, (2, 8), "pdf"),
    ("JAFZA Chain & Lifting", "Jebel Ali Free Zone", "UAE", "Distributor", (3, 6), 0.18, (2, 8), "email"),
    ("Ajman Pins & Springs Trading", "Al Jurf, Ajman", "UAE", "Wholesaler", (2, 4), 0.12, (1, 5), "whatsapp"),
    ("Al Qusais Hardware Distributors", "Al Qusais, Dubai", "UAE", "Distributor", (2, 5), 0.22, (2, 10), "csv"),
    ("Musaffah Stainless Supplies", "Musaffah, Abu Dhabi", "UAE", "Distributor", (3, 5), 0.20, (2, 7), "email"),
    ("Dammam Wire & Chain Co.", "Dammam", "Saudi Arabia", "Distributor", (6, 10), 0.30, (3, 12), "email"),
    ("Ningbo Marine Hardware Co.", "Ningbo (via Jebel Ali)", "China", "Importer", (30, 42), 0.40, (5, 21), "wechat"),
    ("Qingdao Stainless Fasteners Co.", "Qingdao (via Jebel Ali)", "China", "Importer", (32, 45), 0.40, (5, 21), "wechat"),
    ("Mumbai Rigging Exports", "Mumbai (via Jebel Ali)", "India", "Importer", (18, 26), 0.35, (4, 15), "pdf"),
]
suppliers = []
for i, (nm, loc, ctry, typ, (lo, hi), lp, dr, ch) in enumerate(SUPPLIER_SPECS):
    suppliers.append(dict(id="SUP%03d" % (i + 1), name=nm, location=loc, country=ctry, type=typ,
                          lead=R.randint(lo, hi), late_prob=lp, delay=dr, channel=ch,
                          terms=R.choice(["Cash", "30 days", "30 days", "60 days"]), seq=0))
SUP = dict((s["name"], s) for s in suppliers)
CAT_SUP = [
    ("Fasteners - Bolts & Screws", ["Naif Fasteners & Tools", "Industrial Area Bolt House", "Al Qusais Hardware Distributors", "Qingdao Stainless Fasteners Co."]),
    ("Fasteners - Nuts & Washers", ["Industrial Area Bolt House", "Naif Fasteners & Tools", "Qingdao Stainless Fasteners Co."]),
    ("Fasteners - Self Tapping & Wood Screws", ["Naif Fasteners & Tools", "Al Qusais Hardware Distributors", "Qingdao Stainless Fasteners Co."]),
    ("Fasteners - Anchors", ["Al Qusais Hardware Distributors", "Industrial Area Bolt House"]),
    ("Industrial Pins & Retaining Fasteners", ["Ajman Pins & Springs Trading", "Naif Fasteners & Tools", "Qingdao Stainless Fasteners Co."]),
    ("Shackles & Rigging Hardware", ["Al Ras Rigging Supplies", "Sharjah Industrial Rigging", "Ningbo Marine Hardware Co.", "Mumbai Rigging Exports"]),
    ("Wire Rope & Fittings", ["Deira Wire Rope Trading", "Jebel Ali Steel Wire Distribution", "Al Ras Rigging Supplies", "Ningbo Marine Hardware Co.", "Dammam Wire & Chain Co."]),
    ("Chains", ["JAFZA Chain & Lifting", "Al Ras Rigging Supplies", "Dammam Wire & Chain Co.", "Mumbai Rigging Exports"]),
    ("Hinges, Locks & Handles", ["Al Qusais Hardware Distributors", "Musaffah Stainless Supplies", "Ningbo Marine Hardware Co."]),
    ("Springs", ["Ajman Pins & Springs Trading", "Qingdao Stainless Fasteners Co."]),
    ("Marine Fittings", ["Creekside Marine Hardware", "Hamriyah Marine Supplies", "Ningbo Marine Hardware Co."]),
]
cat_sup = {}
for cat, names in CAT_SUP:
    pool = [SUP[n] for n in names]
    cat_sup[cat] = Weighted(pool, [0.6 if s["type"] == "Importer" else (6 if k == 0 else 2) for k, s in enumerate(pool)])

# ======================================================================= customers (Tally ledgers)
W1 = ["Gulf", "Al Noor", "Blue Wave", "Crescent", "Al Bahar", "Sealine", "Falcon", "Oasis", "Coral", "Anchor",
      "Al Khaleej", "Harbour", "Desert Star", "Al Saqr", "Pearl", "Emirates Line", "Al Waha", "Marina", "Dhow",
      "Al Fajr", "Northstar", "Sandcastle", "Bay", "Lagoon", "Al Mina", "Tidal", "Keel", "Compass", "Mast", "Beacon"]
W2 = ["Marine", "Rigging", "Engineering", "Shipping", "Contracting", "Boats", "Steel", "Technical", "Offshore",
      "Yachts", "Industrial", "Lifting", "Fabrication", "Maintenance", "Electromechanical", "Logistics"]
W3 = ["Services", "Works", "Trading", "Solutions", "Supplies", "Co."]
LEGAL = ["LLC", "L.L.C", "FZE", "FZCO", "Est."]
CTYPES = [("Shipyard / Dry Dock", 0.10, 0.10), ("Marine Contractor", 0.22, 0.08), ("Offshore / Oil & Gas", 0.06, 0.10),
          ("Steel Fabricator / Workshop", 0.18, 0.07), ("Construction / MEP Contractor", 0.16, 0.06),
          ("Marina / Yacht Services", 0.10, 0.05), ("Hardware Reseller", 0.06, 0.12), ("Dhow / Boat Operator", 0.12, 0.0)]
EMIRATES = Weighted(["Sharjah", "Dubai", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah", "Abu Dhabi"],
                    [36, 34, 11, 4, 6, 4, 5])
ctype_pick = Weighted(CTYPES, [c[1] for c in CTYPES])
customers, used_names = [], set()
for i in range(2400):
    t = ctype_pick.pick()
    while True:
        nm = "%s %s %s" % (R.choice(W1), R.choice(W2), R.choice(W3))
        if nm not in used_names:
            used_names.add(nm); break
    em = EMIRATES.pick()
    opened = START - timedelta(days=R.randint(0, 3000)) if R.random() < 0.55 else \
        START + timedelta(days=R.randint(0, (END - START).days - 60))
    customers.append(dict(id="C%05d" % (i + 1), name=nm, legal=R.choice(LEGAL), type=t[0], emirate=em,
                          disc=t[2], act=R.paretovariate(1.15), opened=opened,
                          trn="10%012d3" % R.randint(10 ** 10, 10 ** 12 - 1)))
CUST = dict((c["id"], c) for c in customers)

def ledger_name(c, branch=None):
    return "%s %s" % (c["name"], c["legal"])                 # unified masters: same ledger name everywhere

# branch preference by emirate
BR_PREF = {"Sharjah": [0.62, 0.05, 0.33], "Dubai": [0.12, 0.83, 0.05], "Ajman": [0.70, 0.05, 0.25],
           "Umm Al Quwain": [0.70, 0.05, 0.25], "Ras Al Khaimah": [0.65, 0.05, 0.30], "Fujairah": [0.60, 0.10, 0.30],
           "Abu Dhabi": [0.20, 0.75, 0.05]}
POOLS = {}
def acct_pool(b, d):
    """Customers likely to buy at branch b, given which branches were open on day d."""
    open_now = tuple(x for x in BRANCHES if OPEN[x] <= d)
    key = (b, open_now)
    if key not in POOLS:
        bi = BRANCHES.index(b)
        ws = []
        for c in customers:
            pref = BR_PREF[c["emirate"]]
            ws.append(c["act"] * pref[bi] / sum(pref[BRANCHES.index(x)] for x in open_now))
        POOLS[key] = Weighted(customers, ws)
    return POOLS[key]

# ======================================================================= calendar
EID = [(2019, 6, 4), (2019, 8, 11), (2020, 5, 24), (2020, 7, 31), (2021, 5, 13), (2021, 7, 20), (2022, 5, 2),
       (2022, 7, 9), (2023, 4, 21), (2023, 6, 28), (2024, 4, 10), (2024, 6, 16), (2025, 3, 30), (2025, 6, 6),
       (2026, 3, 20), (2026, 5, 27)]
CLOSED = set()
for y, m, d in EID:
    for k in range(3):
        CLOSED.add(date(y, m, d) + timedelta(days=k))
for y in range(2019, 2027):
    CLOSED.add(date(y, 12, 2)); CLOSED.add(date(y, 1, 1))
RAMADAN = [date(2019, 5, 6), date(2020, 4, 24), date(2021, 4, 13), date(2022, 4, 2), date(2023, 3, 23),
           date(2024, 3, 11), date(2025, 3, 1), date(2026, 2, 18)]

def open_day(d):
    return d.weekday() != 6 and d not in CLOSED            # Mon-Sat (website), closed holidays

def day_factor(d):
    f = [1.05, 1.05, 1.0, 1.05, 0.85, 0.95, 0][d.weekday()]
    if any(r <= d < r + timedelta(days=30) for r in RAMADAN):
        f *= 0.85
    if d.month in (7, 8):
        f *= 0.88
    if date(2020, 3, 26) <= d <= date(2020, 4, 24):
        f *= 0.25                                           # COVID restrictions
    elif date(2020, 4, 25) <= d <= date(2020, 6, 30):
        f *= 0.6
    elif date(2020, 7, 1) <= d <= date(2020, 12, 31):
        f *= 0.85
    return f

BR_GROWTH = {"SHJ1": (38, 58), "DB1": (18, 44), "SHJ2": (12, 30)}   # customers/day at opening -> Oct 2026
def customers_today(b, d):
    if d < OPEN[b]:
        return 0.0
    a, z = BR_GROWTH[b]
    age = (d - OPEN[b]).days
    t = age / float((END - OPEN[b]).days)
    ramp = 0.6 + 0.4 * min(1.0, age / 365.0)                 # new branch builds its customer base in year 1
    return (a + (z - a) * t) * ramp

HOURS = Weighted([8, 9, 10, 11, 12, 15, 16, 17, 18], [6, 10, 10, 8, 6, 6, 9, 9, 6])   # 8-1, 3-7
def rand_ts(d, rng=None):
    rng = rng or R
    h = HOURS.pick(rng)
    return datetime(d.year, d.month, d.day, h, rng.randint(0, 59), rng.randint(0, 59))

# ======================================================================= demand & stock policy
prod_pick = Weighted(catalogue, [p["pop"] for p in catalogue])
TOTAL_POP = sum(p["pop"] for p in catalogue)
CHANNEL = {"walkin": Weighted(["Counter"], [1]),
           "acct": Weighted(["Counter", "Phone", "WhatsApp", "Email"], [30, 22, 35, 13])}
PAY = {"walkin": Weighted(["Cash", "Card"], [60, 40]),
       "acct": Weighted(["Cash", "Card", "Credit"], [10, 15, 75])}
STAFF = {"SHJ1": Weighted(["S1A", "S1B", "S1C", "S1D"], [4, 3, 3, 2]), "DB1": Weighted(["D1A", "D1B", "D1C"], [4, 3, 2]),
         "SHJ2": Weighted(["S2A", "S2B"], [3, 2]), "AJM1": Weighted(["A1A", "A1B"], [3, 2])}

def qty_for(p, walkin, rng=None):
    rng = rng or R
    if p["uom"] == "Mtr":
        return rng.randint(2, 20) if walkin else rng.choice([5, 10, 10, 20, 25, 30, 50, 100])
    if p["uom"] in ("Reel", "Drum", "Box"):
        return 1 if walkin else rng.choice([1, 1, 1, 2, 2, 3, 5])
    if p["price"] < 2:
        return rng.randint(2, 20) if walkin else rng.choice([10, 20, 25, 50, 50, 100, 200])
    if p["price"] < 15:
        return rng.randint(1, 10) if walkin else rng.choice([2, 4, 5, 10, 10, 20, 50])
    return rng.randint(1, 3) if walkin else max(1, int(rng.paretovariate(1.7) * 2))

LINES_PER_DAY = 140 * 2.2
QR = random.Random(7)
for p in catalogue:
    qs = sorted(qty_for(p, QR.random() < 0.3, QR) for _ in range(20))
    p["est"] = LINES_PER_DAY * p["pop"] / TOTAL_POP * (sum(qs) / 20.0)   # company-wide units/day
    p["typ_q"] = qs[17]                                                   # ~90th pct order size

# which SKUs each branch keeps on its shelves (most popular + some noise)
ranked = sorted(catalogue, key=lambda p: -p["pop"] * QR.uniform(0.5, 1.5))
stock = {WH: {}}
rop, upto = {WH: {}}, {WH: {}}
for b in BRANCHES:
    stock[b], rop[b], upto[b] = {}, {}, {}
    share = BRANCH_SHARE[BRANCHES.index(b)]
    for p in ranked[:STOCKED_SKUS[b]]:
        e = p["est"] * share
        rop[b][p["id"]] = max(1, int(round(max(e * R.uniform(4, 9), p["typ_q"] * 0.5))))
        upto[b][p["id"]] = rop[b][p["id"]] + max(p["typ_q"], int(round(e * R.uniform(12, 28))))
        stock[b][p["id"]] = upto[b][p["id"]]
for p in catalogue:
    lead = cat_sup[p["cat"]].items[0]["lead"]
    slow = p["est"] < 0.05                                         # long tail: keep only a token quantity
    rop[WH][p["id"]] = int(round(max(p["est"] * (lead + 10) * R.uniform(0.8, 1.4), 0 if slow else p["typ_q"])))
    upto[WH][p["id"]] = rop[WH][p["id"]] + max(max(1, p["typ_q"] // 3) if slow else p["typ_q"], int(round(p["est"] * R.uniform(30, 60))))
    stock[WH][p["id"]] = upto[WH][p["id"]]                      # warehouse holds the full range

# ======================================================================= simulation state & logs
sales = []           # (branch, inv, line, ts, cust_id or '', pid, qty, unit, disc, total, channel, pay, staff)
transfers = []       # truth: dict per line
pos = []             # purchase order lines
pending_dispatch = {}   # date -> list of (from, to, pid, qty, special_sale or None)
in_transit = {}      # date -> list of transfer line dicts (arrivals)
po_arrivals = {}     # date -> list of (pid, qty)
open_req = set()     # (branch, pid) replenishment already requested / in transit
open_po = set()
dirty = set()        # (loc, pid) touched today
inv_seq = {}
slip_seq = [0]
tv_seq = [0]
lost = {"stockout_lost_lines": 0, "special_orders": 0}

def next_inv(b, d):
    k = (b, d.year)
    inv_seq[k] = inv_seq.get(k, 0) + 1
    return "%s/%d/%05d" % (b, d.year, inv_seq[k])

def price_at(p, d):
    t = (d - START).days / float((END - START).days)
    return p["price"] * (0.88 + 0.12 * t)

def record_sale(b, inv, line, ts, cust, p, q, walkin, channel, pay, staff):
    disc = cust["disc"] if (cust and R.random() < 0.8) else 0.0
    unit = price_at(p, ts.date())
    sales.append((b, inv, line, ts, cust["id"] if cust else "", p["id"], q, unit, disc,
                  round(unit * q * (1 - disc), 2), channel, pay, staff))

ONEOFF_SEQ = [len(catalogue)]
ONEOFF_BY_NAME = {}
PACK_DIV = {"Box/100": 85.0, "Box/500": 400.0, "Box/50": 45.0, "Reel/100m": 92.0, "Reel/500m": 440.0, "Drum/50m": 46.0}
ONEOFF_SPECS = ["7mm", "9mm", "11mm", "15mm", "17mm", "M7", "M9", "M11", "M15", "custom length", "special finish", "non-standard"]
def make_oneoff(d, cust, b):
    """A one-off item created in Tally for a single customer request (bought in, sold once)."""
    base = prod_pick.pick()
    spec = R.choice(ONEOFF_SPECS) if R.random() < 0.6 else "%s %s" % (base["spec"], R.choice(["cut to size", "drilled", "polished", "imported"]))
    nm = "SPECIAL " + canon_name(dict(mat=base["mat"], typ=base["typ"], spec=spec, pack="", origin=""))
    if nm in ONEOFF_BY_NAME:                      # same special request seen before: reuse the item
        p = ONEOFF_BY_NAME[nm]
        return _oneoff_po(p, d)
    ONEOFF_SEQ[0] += 1
    pid = "PHT-%05d" % ONEOFF_SEQ[0]
    p = dict(id=pid, cat=base["cat"], typ=base["typ"], mat=base["mat"], spec=spec,
             pack="", uom=base["uom"] if base["uom"] in ("Nos", "Mtr") else "Nos", origin="", oneoff=True,
             price=round(base["price"] / PACK_DIV.get(base["pack"], 1.0) * R.uniform(1.5, 4.0) + R.uniform(5, 60), 2), pop=0.0, est=0.0, typ_q=1,
             created=d, code_compact=pid.replace("-", ""))
    p["cost"] = round(p["price"] * R.uniform(0.6, 0.75), 2)
    p["names"] = {"SHJ1": nm}
    catalogue.append(p); PRODUCT[pid] = p; ONEOFF_BY_NAME[nm] = p
    rop[WH][pid], upto[WH][pid], stock[WH][pid] = 0, 0, 0
    return _oneoff_po(p, d)

def _oneoff_po(p, d):
    pid = p["id"]
    q = R.choice([1, 2, 2, 4, 5, 10, 20]) if p["uom"] == "Nos" else R.choice([5, 10, 20, 50])
    s_ = cat_sup[p["cat"]].pick()
    while s_["type"] == "Importer":
        s_ = cat_sup[p["cat"]].pick()
    arrive = d + timedelta(days=s_["lead"] + (R.randint(*s_["delay"]) if R.random() < s_["late_prob"] else 0))
    po_arrivals.setdefault(arrive, []).append((pid, q))
    pos.append(dict(po="PO%07d" % (len(pos) + 1), date=d, pid=pid, sid=s_["id"], qty=q, cost=p["cost"],
                    expected=d + timedelta(days=s_["lead"]), actual=arrive))
    return p, q, arrive

def run_sales(d):
    for b in BRANCHES:
        n = poisson(customers_today(b, d) * day_factor(d))
        for _ in range(n):
            walkin = R.random() < 0.30
            cust = None if walkin else acct_pool(b, d).pick()
            if cust and cust["opened"] > d:
                cust, walkin = None, True
            kind = "walkin" if walkin else "acct"
            n_lines = Weighted([1, 2, 3], [55, 30, 15]).pick() if walkin else min(10, 1 + int(R.paretovariate(1.45)))
            inv = next_inv(b, d)
            ts = rand_ts(d)
            ch, pay, staff = CHANNEL[kind].pick(), PAY[kind].pick(), STAFF[b].pick()
            line, chosen = 0, set()
            for _ in range(n_lines):
                if not walkin and R.random() < 0.03:                 # special request -> one-off item
                    p, q, arrive = make_oneoff(d, cust, b)
                    lost["special_orders"] += 1
                    pending_dispatch.setdefault(arrive, []).append(
                        (None, b, p["id"], q, dict(cust=cust, walkin=walkin, ch=ch, pay=pay, staff=staff, inv=inv)))
                    continue
                p = prod_pick.pick()
                if p["id"] in chosen:
                    continue
                chosen.add(p["id"])
                q = qty_for(p, walkin)
                have = stock[b].get(p["id"], 0)
                if have >= q or (have > 0 and R.random() < 0.85):
                    q = min(q, have)
                    stock[b][p["id"]] = have - q
                    dirty.add((b, p["id"]))
                    line += 1
                    record_sale(b, inv, line, ts, cust, p, q, walkin, ch, pay, staff)
                elif R.random() < 0.75:          # customer waits: branch asks for it to be sent over
                    lost["special_orders"] += 1
                    lag = 1 if b == "SHJ1" else R.randint(2, 4)          # SHJ2/DB1 must ask SHJ1 first
                    pending_dispatch.setdefault(d + timedelta(days=lag), []).append(
                        (None, b, p["id"], q, dict(cust=cust, walkin=walkin, ch=ch, pay=pay, staff=staff, inv=inv)))
                else:
                    lost["stockout_lost_lines"] += 1

def replenish_requests(d):
    for loc, pid in sorted(dirty):
        if loc == WH:
            continue
        if stock[loc].get(pid, 0) <= rop[loc].get(pid, -1) and (loc, pid) not in open_req:
            open_req.add((loc, pid))
            lag = 1 if loc == "SHJ1" else R.randint(2, 5)   # SHJ2/DB1 phone/WhatsApp SHJ1 first
            if R.random() < 0.12:
                lag += 7                                                   # request forgotten for a week
            qty = upto[loc][pid] - stock[loc].get(pid, 0)
            pending_dispatch.setdefault(d + timedelta(days=lag), []).append((None, loc, pid, qty, None))

def dispatch(d):
    todays = pending_dispatch.pop(d, [])
    for src, dst, pid, qty, special in todays:
        if not open_day(d):
            pending_dispatch.setdefault(d + timedelta(days=1), []).append((src, dst, pid, qty, special))
            continue
        source = WH if stock[WH].get(pid, 0) >= qty else None
        if source is None:                                   # warehouse short: borrow from another branch
            for b in BRANCHES:
                if b != dst and OPEN[b] <= d and stock[b].get(pid, 0) - qty > rop[b].get(pid, 0):
                    source = b; break
        if source is None and stock[WH].get(pid, 0) > 0:
            short = qty - stock[WH][pid]                     # send what the warehouse has
            qty = stock[WH][pid]
            source = WH
            dirty.add((WH, pid))
            if special is None:                              # restock remainder later
                pending_dispatch.setdefault(d + timedelta(days=5), []).append((src, dst, pid, short, None))
        if source is None:
            dirty.add((WH, pid))
            if special is None:
                pending_dispatch.setdefault(d + timedelta(days=3), []).append((src, dst, pid, qty, special))
            elif R.random() < 0.88:                          # customer still waiting
                pending_dispatch.setdefault(d + timedelta(days=3), []).append((src, dst, pid, qty, special))
            else:
                lost["stockout_lost_lines"] += 1
                lost["lost_waiting_for_transfer"] = lost.get("lost_waiting_for_transfer", 0) + 1
            continue
        stock[source][pid] -= qty
        dirty.add((source, pid))
        arrive = d + timedelta(days=0 if dst == "SHJ1" and source == WH else R.choice([0, 1, 1, 2]))
        slip_seq[0] += 1
        tr = dict(tid="TR%07d" % (len(transfers) + 1), slip="PS%06d" % slip_seq[0], src=source, dst=dst,
                  pid=pid, qty=qty, sent=d, arrive=arrive, special=special)
        transfers.append(tr)
        in_transit.setdefault(arrive, []).append(tr)

def receive(d):
    for tr in in_transit.pop(d, []):
        b, pid = tr["dst"], tr["pid"]
        if tr["special"] is None:
            stock[b][pid] = stock[b].get(pid, 0) + tr["qty"]
            open_req.discard((b, pid))
        elif not open_day(d):                                # shop closed: invoice next day
            in_transit.setdefault(d + timedelta(days=1), []).append(tr)
        else:                                                # customer's waiting order is invoiced now
            s = tr["special"]
            inv = next_inv(b, d)
            record_sale(b, inv, 1, rand_ts(d), s["cust"], PRODUCT[pid], tr["qty"], s["walkin"], s["ch"],
                        s["pay"], STAFF[b].pick())
    for pid, q in po_arrivals.pop(d, []):
        stock[WH][pid] = stock[WH].get(pid, 0) + q
        open_po.discard(pid)

def warehouse_reorder(d):
    for loc, pid in sorted(dirty):
        if loc != WH or pid in open_po or PRODUCT[pid].get("oneoff") or stock[WH].get(pid, 0) > rop[WH][pid] + PRODUCT[pid]["typ_q"]:
            continue
        p = PRODUCT[pid]
        s = cat_sup[p["cat"]].pick()
        expected = d + timedelta(days=s["lead"])
        actual = expected + timedelta(days=R.randint(*s["delay"]) if R.random() < s["late_prob"] else R.choice([-1, 0, 0, 0]))
        actual = max(actual, d + timedelta(days=1))
        qty = max(upto[WH][pid] - stock[WH].get(pid, 0), 1)
        open_po.add(pid)
        po_arrivals.setdefault(actual, []).append((pid, qty))
        pos.append(dict(po="PO%07d" % (len(pos) + 1), date=d, pid=pid, sid=s["id"], qty=qty,
                        cost=p["cost"] * (0.9 + 0.1 * (d - START).days / float((END - START).days)),
                        expected=expected, actual=actual))

# month-end / year-end stock summary snapshots exported from Tally
snapshots = []
def snapshot_wanted(d):
    nxt = d + timedelta(days=1)
    if nxt.month == d.month:
        return False
    return d.month == 12 or (d.year == 2026 and d.month >= 8)

OPENING = {}
d = START
while d <= END:
    for b in BRANCHES:
        if d == OPEN[b]:
            OPENING[b] = dict(stock[b])
            if b == "SHJ1":
                OPENING[WH] = dict(stock[WH])
    receive(d)
    dispatch(d)
    receive(d)                                   # same-day transfers (e.g. warehouse -> SHJ1)
    if open_day(d):
        run_sales(d)
        replenish_requests(d)
    warehouse_reorder(d)
    dirty.clear()
    if snapshot_wanted(d):
        snapshots.append((d, dict((loc, dict(v)) for loc, v in stock.items())))
    d += timedelta(days=1)
print("simulation done: %d sales lines, %d transfer lines, %d PO lines" % (len(sales), len(transfers), len(pos)))


# ======================================================================= EXPORTS: TallyPrime formats (unified masters)
XR = random.Random(SEED + 1)

def tdate(d):
    """TallyPrime date style, e.g. 5-Mar-25."""
    return "%d-%s" % (d.day, d.strftime("%b-%y")) if d else ""

def tqty(q, uom):
    return "%d %s" % (q, uom)

GODOWN = {"WH1": "Main Warehouse", "SHJ1": "Sharjah 1 Showroom", "DB1": "Dubai 1 Showroom", "SHJ2": "Sharjah 2 Showroom",
          "AJM1": "Ajman Showroom"}
BRANCH_GD = {"SHJ1": "Sharjah 1 Branch", "DB1": "Dubai 1 Branch", "SHJ2": "Sharjah 2 Branch"}
AREAS = {"Sharjah": ["Industrial Area 4", "Industrial Area 6", "Hamriyah Free Zone", "Al Sajaa", "Sharjah Creek"],
         "Dubai": ["Al Qusais", "Al Quoz", "Jebel Ali", "Deira", "Dubai Maritime City", "Al Jaddaf"],
         "Ajman": ["Al Jurf", "Ajman Free Zone", "Al Nuaimiya"], "Umm Al Quwain": ["UAQ Industrial Area"],
         "Ras Al Khaimah": ["Al Jazeera Al Hamra", "RAK Maritime City"], "Fujairah": ["Fujairah Free Zone", "Port Area"],
         "Abu Dhabi": ["Musaffah", "Mina Zayed"]}
for c in customers:
    c["address"] = "%s, %s" % (XR.choice(AREAS[c["emirate"]]), c["emirate"])
for s_ in suppliers:
    s_["trn"] = "10%012d3" % XR.randint(10 ** 10, 10 ** 12 - 1) if s_["country"] == "UAE" else ""
PAYTERMS = {"Cash": "Cash", "Card": "Card", "Credit": None}
NARR = {"WhatsApp": ["WA order", "Whatsapp order - deliver", ""], "Phone": ["per phone", ""], "Email": ["LPO by email", ""],
        "Counter": ["", "", "", "collected by customer"]}

def item_name(p):
    return p["names"]["SHJ1"]                 # unified item master: identical name in every branch

def stock_group(p):
    return "Special Orders" if p.get("oneoff") else p["cat"]

# ---------------------------------------------------------------- sales invoices + quotations
SALES_HDR = ["Voucher Type", "Voucher Mode", "Voucher No", "Date", "Effective Date", "Reference No", "Reference Date",
             "Party Ledger", "Buyer Name", "Buyer Address", "Buyer Emirate", "Buyer Country", "Buyer TRN",
             "Consignee Name", "Consignee Address", "Delivery Note No", "Delivery Note Date", "Dispatch Doc No",
             "Dispatched Through", "Destination", "Carrier Name/Agent", "Bill of Lading/LR-RR No", "Motor Vehicle No",
             "Sales Order No", "Sales Order Date", "Mode/Terms of Payment", "Other References", "Terms of Delivery",
             "Port of Loading", "Port of Discharge", "Shipping Bill No",
             "Name of Item", "Item Description", "Godown", "Actual Qty", "Billed Qty", "Rate", "per", "Disc %", "Amount",
             "VAT %", "VAT Amount", "Narration"]
invoices = {}
for r in sales:
    invoices.setdefault((r[0], r[1]), []).append(r)
seq = {}
def nxt(kind, b, y):
    k = (kind, b, y); seq[k] = seq.get(k, 0) + 1
    return seq[k]

quotes = []           # (branch, quote_no, date, cust, lines[(pid, qty, rate, disc)], converted_inv or "")
inv_quote = {}
for (b, inv), rows in sorted(invoices.items(), key=lambda kv: kv[1][0][3]):
    cid = rows[0][4]
    if cid and XR.random() < 0.35:
        d0 = rows[0][3].date()
        qd = max(OPEN[b], d0 - timedelta(days=XR.randint(0, 10)))
        qno = "%s/Q/%d/%05d" % (b, qd.year, nxt("Q", b, qd.year))
        lines = [(r[5], r[6], r[7] * XR.uniform(1.0, 1.05), r[8]) for r in rows]
        if XR.random() < 0.3:
            p = prod_pick.pick(XR); lines.append((p["id"], qty_for(p, False, XR), price_at(p, qd), CUST[cid]["disc"]))
        quotes.append((b, qno, qd, cid, lines, inv))
        inv_quote[(b, inv)] = qno
acct_invoices = sum(1 for k, rows in invoices.items() if rows[0][4])
inv_dates = [rows[0][3].date() for rows in invoices.values() if rows[0][4]]
inv_dates.sort()
for _ in range(int(acct_invoices * 0.55)):           # quotes that never became invoices
    dd = XR.choice(inv_dates)                         # quotes follow business activity
    obr = [b for b in BRANCHES if OPEN[b] <= dd]
    b = obr[bisect.bisect_right([0.45, 0.78, 1.0][:len(obr)], XR.random() * [0.45, 0.78, 1.0][len(obr) - 1])] if len(obr) > 1 else obr[0]
    c = acct_pool(b, dd).pick(XR)
    lines = []
    for _ in range(min(8, 1 + int(XR.paretovariate(1.8)))):
        p = prod_pick.pick(XR); lines.append((p["id"], qty_for(p, False, XR), price_at(p, dd) * XR.uniform(1.0, 1.08), c["disc"]))
    qno = "%s/Q/%d/%05d" % (b, dd.year, nxt("Q", b, dd.year))
    quotes.append((b, qno, dd, c["id"], lines, ""))

def header(vtype, vno, d, c, b, pay, ref_other, dispatch, narr):
    if c:
        ref = ("LPO-%d" % XR.randint(10000, 99999)) if XR.random() < 0.4 else ""
        buyer = [ledger_name(c), ledger_name(c), c["address"], c["emirate"], "United Arab Emirates", c["trn"]]
        cons = [ledger_name(c), XR.choice(AREAS[c["emirate"]]) + " site, " + c["emirate"]] if XR.random() < 0.1 else ["", ""]
    else:
        ref, buyer, cons = "", ["Cash", "", "", "", "", ""], ["", ""]
    if dispatch:
        dn = "DN/%s/%d/%05d" % (b, d.year, nxt("DN", b, d.year))
        disp = [dn, tdate(d), "", XR.choice(["Own Vehicle", "Own Vehicle", "Courier", "Customer Collection"]),
                c["emirate"] if c else "", "", "", "%s %d %05d" % ({"SHJ1": "SHJ", "SHJ2": "SHJ", "DB1": "DXB"}[b], XR.randint(1, 3), XR.randint(10000, 99999))]
    else:
        disp = [""] * 8
    so = ["SO/%s/%d/%04d" % (b, d.year, nxt("SO", b, d.year)), tdate(d)] if (c and XR.random() < 0.08) else ["", ""]
    terms = pay if pay != "Credit" else ("Credit %d Days" % XR.choice([30, 30, 60]))
    return ([vtype, "Item Invoice", vno, tdate(d), "", ref, tdate(d) if ref else ""] + buyer + cons + disp + so +
            [terms, ref_other, "", "", "", ""])

by_month = {}
for (b, inv), rows in invoices.items():
    r0 = rows[0]; d0 = r0[3].date(); c = CUST.get(r0[4])
    dispatch = bool(c) and r0[10] in ("WhatsApp", "Phone", "Email") and XR.random() < 0.6
    h = header("Sales", inv, d0, c, b, r0[11], inv_quote.get((b, inv), ""), dispatch, None)
    narr = XR.choice(NARR[r0[10]])
    for r in rows:
        p = PRODUCT[r[5]]
        actual = r[6] + (XR.choice([1, 2, 5]) if XR.random() < 0.005 else 0)    # occasional free extra units
        by_month.setdefault((b, d0.year, d0.month), []).append(
            (r[3], h + [item_name(p), "" if XR.random() < 0.9 else "as per sample", GODOWN[b], tqty(actual, p["uom"]),
                        tqty(r[6], p["uom"]), "%.2f" % r[7], p["uom"], "%g" % round(r[8] * 100), "%.2f" % r[9], "5%",
                        "%.2f" % (r[9] * 0.05), narr]))
for (b, y, m), rows in sorted(by_month.items()):
    rows.sort(key=lambda x: (x[0], x[1][2]))
    write_csv(path("tally_exports", b, "sales", "SalesInvoices_%s_%d_%02d.csv" % (b, y, m)), SALES_HDR, [x[1] for x in rows])

q_by_month = {}
for b, qno, qd, cid, lines, conv in quotes:
    c = CUST[cid]
    h = header("Quotation", qno, qd, c, b, XR.choice(["Credit", "Cash"]), "", False, None)
    for pid, q, rate, disc in lines:
        p = PRODUCT[pid]; amt = rate * q * (1 - disc)
        q_by_month.setdefault((b, qd.year, qd.month), []).append(
            (qd, qno, h + [item_name(p), "", GODOWN[b], tqty(q, p["uom"]), tqty(q, p["uom"]), "%.2f" % rate, p["uom"],
                           "%g" % round(disc * 100), "%.2f" % amt, "5%", "%.2f" % (amt * 0.05), XR.choice(["", "valid 7 days", "subject to stock"])]))
for (b, y, m), rows in sorted(q_by_month.items()):
    rows.sort(key=lambda x: (x[0], x[1]))
    write_csv(path("tally_exports", b, "quotations", "Quotations_%s_%d_%02d.csv" % (b, y, m)), SALES_HDR, [x[2] for x in rows])

# ---------------------------------------------------------------- purchase invoices (warehouse is booked in SHJ1's Tally)
PUR_HDR = ["Voucher Type", "Voucher Mode", "Voucher No", "Date", "Supplier Invoice No", "Supplier Invoice Date", "Party Ledger",
           "Supplier Address", "Supplier Country", "Supplier TRN", "Receipt Note No", "Receipt Note Date", "Order No",
           "Order Date", "Mode/Terms of Payment", "Name of Item", "Item Description", "Godown", "Actual Qty", "Billed Qty",
           "Rate", "per", "Disc %", "Amount", "VAT %", "VAT Amount", "Narration"]
sup_inv = {}
for po in pos:
    if po["actual"] > END:
        continue
    sup_inv.setdefault((po["sid"], po["actual"]), []).append(po)
p_by_month, sup_seq = {}, {}
for (sid, dd), lines in sorted(sup_inv.items(), key=lambda kv: (kv[0][1], kv[0][0])):
    s_ = suppliers[int(sid[3:]) - 1]
    sup_seq[sid] = sup_seq.get(sid, 0) + 1
    sinv = "%s-%d-%05d" % (sid.replace("SUP", "S"), dd.year, sup_seq[sid])
    entry = dd + timedelta(days=XR.choice([0, 0, 1, 1, 2, 3, 5]))            # bills typed in by hand
    vno = "PUR/%d/%05d" % (entry.year, nxt("PUR", "SHJ1", entry.year))
    grn = "GRN/%d/%05d" % (dd.year, nxt("GRN", "SHJ1", dd.year))
    for po in lines:
        p = PRODUCT[po["pid"]]; amt = po["cost"] * po["qty"]
        rec_q = po["qty"] - (XR.choice([1, 2]) if XR.random() < 0.01 else 0)  # short delivery
        p_by_month.setdefault((entry.year, entry.month), []).append(
            (entry, vno, ["Purchase", "Item Invoice", vno, tdate(entry), sinv, tdate(dd), s_["name"], s_["location"], s_["country"],
                          s_["trn"], grn, tdate(dd), po["po"] if XR.random() < 0.85 else "", tdate(po["date"]), s_["terms"],
                          item_name(p), "", GODOWN["WH1"], tqty(rec_q, p["uom"]), tqty(po["qty"], p["uom"]), "%.2f" % po["cost"],
                          p["uom"], "0", "%.2f" % amt, "5%" if s_["country"] == "UAE" else "5% (RCM)", "%.2f" % (amt * 0.05),
                          XR.choice(["", "", "short supply - follow up", "special order item"]) if p.get("oneoff") is None
                          else "special order for customer"]))
for (y, m), rows in sorted(p_by_month.items()):
    rows.sort(key=lambda x: (x[0], x[1]))
    write_csv(path("tally_exports", "SHJ1", "purchases", "PurchaseInvoices_SHJ1_%d_%02d.csv" % (y, m)), PUR_HDR, [x[2] for x in rows])

# ---------------------------------------------------------------- stock journals: inter-godown transfers, recorded in BOTH Tallys
SJ_HDR = ["Voucher Type", "Voucher Class", "Voucher No", "Date", "Day", "Destination Godown", "Name of Item", "Source Godown",
          "Quantity", "Rate", "per", "Amount", "Narration"]
voucher_of = {}
for t in sorted(transfers, key=lambda t: (t["sent"], t["src"], t["dst"], t["tid"])):
    key = (t["sent"], t["src"], t["dst"])
    if key not in voucher_of:
        voucher_of[key] = "PS%06d" % (len(voucher_of) + 1)
    t["slip"] = voucher_of[key]
vno_of = {}
def sj_vno(owner, key, d):
    k = (owner, key)
    if k not in vno_of:
        vno_of[k] = "SJ/%d/%05d" % (d.year, nxt("SJ", owner, d.year))
    return vno_of[k]
journal = dict((b, {}) for b in BRANCHES)
truth_rows, jstats = [], {"receipts_missing": 0, "qty_mismatch": 0}
NOTES = ["", "", "per call with Sharjah 1", "urgent - customer waiting", "as per WA msg", "partial, balance later"]
def jrow(owner, d, vno, p, q, src_gd, dst_gd, note):
    journal[owner].setdefault((d.year, d.month), []).append(
        (d, vno, ["Stock Journal", "Transfer of Materials - Inter Godown", vno, tdate(d), d.strftime("%A"), dst_gd, item_name(p),
                  src_gd, tqty(q, p["uom"]), "%.2f" % p["cost"], p["uom"], "%.2f" % (q * p["cost"]), note]))
for t in transfers:
    p = PRODUCT[t["pid"]]
    note = ((("PS#%s " % t["slip"][2:]) if XR.random() < 0.7 else "") + XR.choice(NOTES)).strip()
    src, dst = t["src"], t["dst"]
    key = (t["sent"], src, dst)
    if src == WH:
        # warehouse lives inside SHJ1's Tally: everything is booked through SHJ1 first
        jrow("SHJ1", t["sent"], sj_vno("SHJ1", key + ("GT",), t["sent"]), p, t["qty"], GODOWN["WH1"], GODOWN["SHJ1"], note)
        if dst != "SHJ1":
            jrow("SHJ1", t["sent"], sj_vno("SHJ1", key, t["sent"]), p, t["qty"], GODOWN["SHJ1"], BRANCH_GD[dst], note)
        sender = "SHJ1"
    else:
        jrow(src, t["sent"], sj_vno(src, key, t["sent"]), p, t["qty"], GODOWN[src], BRANCH_GD[dst], note)
        sender = src
    rec_q, rec_d = t["qty"], None
    if sender != dst:
        if XR.random() < 0.03:
            jstats["receipts_missing"] += 1
        else:
            rec_d = t["arrive"] + timedelta(days=XR.choice([0, 0, 0, 1, 1, 2, 3]))
            if XR.random() < 0.02:
                rec_q = max(0, t["qty"] + XR.choice([-5, -2, -1, 1, 2, 10])); jstats["qty_mismatch"] += 1
            jrow(dst, rec_d, sj_vno(dst, ("RCV",) + key, rec_d), p, rec_q, BRANCH_GD[sender], GODOWN[dst],
                 note if XR.random() < 0.6 else XR.choice(NOTES))
    else:
        rec_d = t["sent"]
    truth_rows.append([t["tid"], t["slip"], src, dst, t["pid"], t["qty"], t["sent"].isoformat(), t["arrive"].isoformat(),
                       "Y" if t["special"] else "N", sender, rec_d.isoformat() if rec_d else "", rec_q if rec_d else ""])
for b in BRANCHES:
    for (y, m), rows in sorted(journal[b].items()):
        rows.sort(key=lambda x: (x[0], x[1]))
        write_csv(path("tally_exports", b, "stock_journal", "StockJournal_%s_%d_%02d.csv" % (b, y, m)), SJ_HDR, [x[2] for x in rows])

# ---------------------------------------------------------------- List of Stock Items (unified master, opening balances per Tally)
ITEM_HDR = ["Sl. No.", "Name of Item", "Under", "Units", "Opening Qty", "Rate", "per", "Opening Balance"]
for b in BRANCHES:
    op = dict(OPENING.get(b, {}))
    if b == "SHJ1":
        for pid, q in OPENING.get(WH, {}).items():
            op[pid] = op.get(pid, 0) + q
    rows = []
    for i, p in enumerate(sorted(catalogue, key=lambda x: item_name(x)), 1):
        q = op.get(p["id"], 0)
        rows.append([i, item_name(p), stock_group(p), p["uom"], tqty(q, p["uom"]) if q else "", "%.2f" % p["cost"], p["uom"],
                     "%.2f" % (q * p["cost"]) if q else ""])
    write_csv(path("tally_exports", b, "ListOfStockItems_%s.csv" % b), ITEM_HDR, rows)

LEDGER_HDR = ["Name of Ledger", "Under", "Address", "Emirate / Country", "TRN"]
cust_used = dict((b, set()) for b in BRANCHES)
for r in sales:
    if r[4]:
        cust_used[r[0]].add(r[4])
for b, qno, qd, cid, lines, conv in quotes:
    cust_used[b].add(cid)
for b in BRANCHES:
    rows = [[ledger_name(CUST[c]), "Sundry Debtors", CUST[c]["address"], CUST[c]["emirate"], CUST[c]["trn"]] for c in sorted(cust_used[b])]
    rows.append(["Cash", "Cash-in-Hand", "", "", ""])
    if b == "SHJ1":
        rows += [[s_["name"], "Sundry Creditors", s_["location"], s_["country"], s_["trn"]] for s_ in suppliers]
    write_csv(path("tally_exports", b, "ListOfLedgers_%s.csv" % b), LEDGER_HDR, rows)

# ---------------------------------------------------------------- godown summaries (closing stock)
GS_HDR = ["Godown", "Name of Item", "Closing Qty", "Rate", "per", "Closing Value"]
for d0, snap in snapshots:
    for b in BRANCHES:
        if OPEN[b] > d0:
            continue
        locs = [WH, b] if b == "SHJ1" else [b]
        rows = []
        for loc in locs:
            for pid in sorted(snap[loc]):
                q = snap[loc][pid]
                if q > 0:
                    p = PRODUCT[pid]
                    rows.append([GODOWN[loc], item_name(p), tqty(q, p["uom"]), "%.2f" % p["cost"], p["uom"], "%.2f" % (q * p["cost"])])
        write_csv(path("tally_exports", b, "stock_summary", "GodownSummary_%s_%s.csv" % (b, d0.isoformat())), GS_HDR, rows)
print("tally exports written")

# ---------------------------------------------------------------- lake item IDs: PHT-xxxxx by alphabetical item name
NEWID = dict((p["id"], "PHT-%05d" % (i + 1)) for i, p in enumerate(sorted(catalogue, key=item_name)))

# ---------------------------------------------------------------- streaming scenario: Ajman (AJM1) opening day, unified event feed
SR = random.Random(SEED + 2)
LOCS = BRANCHES + ["AJM1"]
sstock = dict((loc, dict(stock[loc])) for loc in BRANCHES + [WH])
srop = dict((loc, dict(rop[loc])) for loc in BRANCHES + [WH])
sstock["AJM1"], srop["AJM1"] = {}, {}
for p in ranked[:6000]:
    e = p["est"] * 0.13
    srop["AJM1"][p["id"]] = max(1, int(round(max(e * SR.uniform(4, 9), p["typ_q"] * 0.5))))
    sstock["AJM1"][p["id"]] = srop["AJM1"][p["id"]] + max(p["typ_q"], int(round(e * SR.uniform(10, 20))))
for loc in LOCS:                                  # a few shelves already near their reorder point at opening
    for pid in sorted(sstock[loc]):
        if SR.random() < 0.012:
            sstock[loc][pid] = srop[loc][pid] + SR.randint(1, max(2, PRODUCT[pid]["typ_q"]))
opening_s = dict((loc, dict(v)) for loc, v in sstock.items())
events, eseq = [], [0]
def ev(ts, etype, loc, pid, q, unit=None, cust="", ref="", cp=""):
    eseq[0] += 1
    events.append([ "EV%07d" % eseq[0], ts.strftime("%Y-%m-%d %H:%M:%S"), etype, loc, pid, q,
                    "%.2f" % unit if unit is not None else "", "%.2f" % (unit * q) if unit is not None else "", cust, ref, cp])
share = Weighted(LOCS, [0.40, 0.30, 0.17, 0.13])
AJM_PREF = Weighted(customers, [c["act"] * (3.0 if c["emirate"] in ("Ajman", "Umm Al Quwain", "Ras Al Khaimah") else 0.3) for c in customers])
pending_in = []
for _ in range(150):
    loc = share.pick(SR)
    walkin = SR.random() < 0.3
    cust = None if walkin else (AJM_PREF.pick(SR) if loc == "AJM1" else acct_pool(loc, STREAM_DAY).pick(SR))
    ts = rand_ts(STREAM_DAY, SR)
    inv = "%s/%d/%05d" % (loc, STREAM_DAY.year, eseq[0] + 1)
    for _ in range(Weighted([1, 2, 3, 4], [40, 30, 20, 10]).pick(SR)):
        p = prod_pick.pick(SR)
        q = qty_for(p, walkin, SR)
        have = sstock[loc].get(p["id"], 0)
        if have <= 0:
            continue
        q = min(q, have)
        sstock[loc][p["id"]] = have - q
        ev(ts, "SALE", loc, p["id"], q, price_at(p, END) * (1 - (cust["disc"] if cust else 0)), cust["id"] if cust else "WALKIN", inv)
        if sstock[loc][p["id"]] <= srop[loc].get(p["id"], -1) and sstock[WH].get(p["id"], 0) > 0:
            q2 = min(sstock[WH][p["id"]], max(p["typ_q"], srop[loc][p["id"]] * 2))
            out_ts = ts + timedelta(minutes=SR.randint(10, 40))
            in_ts = out_ts + timedelta(minutes=SR.randint(60, 150))
            ref = "TR-%s-%04d" % (loc, eseq[0])
            pending_in.append((out_ts, in_ts, loc, p["id"], q2, ref))
            sstock[WH][p["id"]] -= q2
for out_ts, in_ts, loc, pid, q2, ref in pending_in:
    ev(out_ts, "TRANSFER_OUT", WH, pid, q2, ref=ref, cp=loc)
    if in_ts.hour < 19:
        ev(in_ts, "TRANSFER_IN", loc, pid, q2, ref=ref, cp=WH)
for k in range(6):                                # supplier deliveries into the warehouse
    p = prod_pick.pick(SR)
    ev(datetime(2027, 2, 1, SR.choice([9, 10, 11, 16]), SR.randint(0, 59)), "GOODS_RECEIPT", WH, p["id"], max(p["typ_q"] * 3, 10),
       ref="GRN-%04d" % (k + 1), cp=cat_sup[p["cat"]].pick(SR)["id"])
events.sort(key=lambda e: e[1])
EV_HDR = ["event_id", "event_ts", "event_type", "location_id", "product_id", "qty", "unit_price_aed", "line_total_aed", "customer_id", "reference", "counterparty"]
buckets = {}
for e in events:
    ts = datetime.strptime(e[1], "%Y-%m-%d %H:%M:%S")
    buckets.setdefault(ts.replace(minute=(ts.minute // 10) * 10, second=0), []).append(e)
for k, rows in sorted(buckets.items()):
    write_csv(path("stream", "events_%s" % STREAM_DAY.isoformat(), "events_%s.csv" % k.strftime("%H%M")), EV_HDR,
              [r[:4] + [NEWID[r[4]]] + r[5:] for r in rows])
write_csv(path("stream", "opening_stock_%s.csv" % STREAM_DAY.isoformat()), ["location_id", "product_id", "qty_on_hand", "reorder_point_units"],
          sorted([[loc, NEWID[pid], opening_s[loc][pid], srop[loc].get(pid, 0)] for loc in [WH] + LOCS for pid in opening_s[loc]]))
# expected alerts (location/product pairs crossing reorder point during the day, ignoring incoming transfers)
net = {}
for e in events:
    if e[2] in ("SALE", "TRANSFER_OUT"):
        net[(e[3], e[4])] = net.get((e[3], e[4]), 0) - int(e[5])
alerts = sorted(k for k, v in net.items() if opening_s[k[0]].get(k[1], 0) > srop[k[0]].get(k[1], -1) >= opening_s[k[0]].get(k[1], 0) + v)


# ---------------------------------------------------------------- reference (answer keys - NOT lake input)
write_csv(path("reference", "products_canonical.csv"),
          ["product_id", "item_name", "category", "product_type", "material", "spec", "pack", "unit_of_measure", "origin_line",
           "is_one_off", "list_price_aed", "unit_cost_aed"],
          [[NEWID[p["id"]], item_name(p), p["cat"], p["typ"], p["mat"], p["spec"], p["pack"], p["uom"], p["origin"] or "STD",
            "Y" if p.get("oneoff") else "N", "%.2f" % p["price"], "%.2f" % p["cost"]] for p in sorted(catalogue, key=item_name)])
write_csv(path("reference", "customers_canonical.csv"), ["customer_id", "ledger_name", "trn", "customer_type", "emirate", "address"],
          [[c["id"], ledger_name(c), c["trn"], c["type"], c["emirate"], c["address"]] for c in customers])
write_csv(path("reference", "suppliers.csv"), ["supplier_id", "supplier_name", "location", "country", "supplier_type", "standard_lead_time_days", "payment_terms"],
          [[s_["id"], s_["name"], s_["location"], s_["country"], s_["type"], s_["lead"], s_["terms"]] for s_ in suppliers])
write_csv(path("reference", "transfers_truth.csv"),
          ["transfer_id", "pink_slip", "from_location", "to_location", "product_id", "qty_sent", "sent_date", "arrival_date",
           "for_waiting_customer", "booked_by", "receipt_entry_date", "qty_receipt_entered"], [r[:4] + [NEWID[r[4]]] + r[5:] for r in truth_rows])
write_csv(path("reference", "stream_expected_alerts.csv"), ["location_id", "product_id"], sorted([a[0], NEWID[a[1]]] for a in alerts))
write_csv(path("locations.csv"), ["location_id", "godown_name", "emirate", "type", "opened", "tally_setup", "status"],
          [["SHJ1", "Sharjah 1 Showroom", "Sharjah", "Branch (main)", "2019-07-01", "TallyPrime server + client PCs; also books the warehouse", "Operating"],
           ["WH1", "Main Warehouse", "Sharjah", "Warehouse", "2019-07-01", "Godown inside SHJ1 Tally", "Operating"],
           ["DB1", "Dubai 1 Showroom", "Dubai", "Branch", "2021-04-01", "TallyPrime on a single PC, no server", "Operating"],
           ["SHJ2", "Sharjah 2 Showroom", "Sharjah", "Branch", "2023-02-01", "TallyPrime server + client PCs", "Operating"],
           ["AJM1", "Ajman Showroom", "Ajman", "Branch", "", "Proposed - joins the data lake", "Provisional"]])

def per_day(rows):
    inv = set((r[0], r[1]) for r in rows)
    return round(len(inv) / float(max(1, len(set(r[3].date() for r in rows)))), 1)
total_bytes = sum(os.path.getsize(os.path.join(rt, f)) for rt, _, fs in os.walk(OUT) for f in fs)
cust_rev, tot25 = {}, 0.0
for r in sales:
    if r[3].year == 2025:
        em = CUST[r[4]]["emirate"] if r[4] else "(walk-in)"
        cust_rev[em] = cust_rev.get(em, 0) + r[9]; tot25 += r[9]
summary = {
    "company": "Piplodwala Hardware Trading LLC (academic case study - SIMULATED data, TallyPrime export formats)",
    "seed": SEED, "period": [START.isoformat(), END.isoformat()], "branch_openings": dict((b, OPEN[b].isoformat()) for b in BRANCHES),
    "items_in_master": len(catalogue), "one_off_items": sum(1 for p in catalogue if p.get("oneoff")),
    "customer_accounts": len(customers), "suppliers": len(suppliers),
    "sales_invoice_lines": len(sales), "sales_invoices": len(invoices),
    "customers_per_day_by_year": dict((str(y), per_day([r for r in sales if r[3].year == y])) for y in range(2019, 2027)),
    "customers_per_day_Aug_Oct_2026": per_day([r for r in sales if r[3].date() >= date(2026, 8, 1)]),
    "sales_lines_by_branch": dict((b, sum(1 for r in sales if r[0] == b)) for b in BRANCHES),
    "quotations": len(quotes), "quotation_lines": sum(len(q[4]) for q in quotes),
    "quotes_converted_to_invoice": sum(1 for q in quotes if q[5]),
    "revenue_aed_2025": round(tot25, 2),
    "revenue_share_2025_by_customer_emirate_pct": dict((k, round(100 * v / tot25, 1)) for k, v in sorted(cust_rev.items(), key=lambda kv: -kv[1])),
    "transfer_lines": len(transfers), "pink_slips": len(voucher_of),
    "transfer_receipts_missing": jstats["receipts_missing"], "transfer_qty_mismatches": jstats["qty_mismatch"],
    "purchase_invoice_lines": sum(len(v) for v in sup_inv.values()), "supplier_invoices": len(sup_inv),
    "stock_snapshots": [d0.isoformat() for d0, _ in snapshots],
    "hidden_truth": {"sales_lines_lost_to_stockouts": lost["stockout_lost_lines"], "special_orders_customer_waited": lost["special_orders"]},
    "stream_day": STREAM_DAY.isoformat(), "stream_events": len(events), "stream_expected_low_stock_alerts": len(alerts),
    "total_size_mb": round(total_bytes / 1e6, 1),
}
with open(path("summary.json"), "w") as fh:
    json.dump(summary, fh, indent=2)
print(json.dumps(summary, indent=2))
