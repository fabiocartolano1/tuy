import ezdxf
import math
import csv
from collections import defaultdict

doc = ezdxf.readfile("CMT-EXE-RDC.dxf")
msp = doc.modelspace()

CALQUES_PLB = {
    "CMT-PLB-EF-U":                      "Eau froide",
    "CMT_PLMB_EAU_FROIDE":               "Eau froide",
    "CMT_PLMB_ROBINETTERIE_EAU_FROIDE":  "Eau froide",
    "CMT-PLB-EFSG-U":                    "Eau froide sans gel",
    "CMT-PLB-EC-U":                      "Eau chaude sanitaire",
    "CMT_PLMB_EAU_CHAUDE_SANITAIRE":     "Eau chaude sanitaire",
    "CMT_PLMB_ROBINETTERIE_EAU_CHAUDE_SANITAITE": "Eau chaude sanitaire",
    "CMT-PLB-REC-U":                     "Bouclage sanitaire",
    "CMT_PLMB_BOUCLAGE":                 "Bouclage sanitaire",
    "CMT_PLMB_ROBINETTERIE_BOUCLAGE":    "Bouclage sanitaire",
    "CMT-PLB-EU":              "Eaux usees",
    "CMT-PLB-EV":              "Eaux vannes",
    "CMT-PLB-EV-SOUS DALLAGE": "Eaux vannes (sous dallage)",
    "CMT-CONDENSATS":          "Condensats climatisation",
    "CMT-CVC-CONDENSATS":      "Condensats climatisation",
    "CMT-PLB-VP":              "Ventilation primaire",
}

MATIERE = {
    "Eau froide":                  "MC",
    "Eau froide sans gel":         "MC",
    "Eau chaude sanitaire":        "MC",
    "Bouclage sanitaire":          "MC",
    "Eaux usees":                  "PVC",
    "Eaux vannes":                 "PVC",
    "Eaux vannes (sous dallage)":  "PVC",
    "Condensats climatisation":    "PVC",
    "Ventilation primaire":        "PVC",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def turn_angle(p1, p2, p3):
    """Angle de virage en p2 (0 = tout droit, 90 = coude 90°)."""
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    n1, n2 = math.hypot(*v1), math.hypot(*v2)
    if n1 < 1e-9 or n2 < 1e-9:
        return None
    cos_a = (v1[0]*v2[0] + v1[1]*v2[1]) / (n1 * n2)
    interior = math.degrees(math.acos(max(-1.0, min(1.0, cos_a))))
    return abs(180.0 - interior)


def classify_angle(deg):
    if deg < 1:
        return None          # ligne droite, ignorer
    if 85 <= deg <= 95:
        return "90°"
    if 40 <= deg <= 50:
        return "45°"
    if 130 <= deg <= 140:
        return "135°"
    if 63 <= deg <= 70:
        return "67.5°"
    return f"autre (~{round(deg / 5) * 5}°)"


def round_pt(x, y, tol=1e-3):
    return (round(x / tol) * tol, round(y / tol) * tol)


# ── 1. COUDES — virages intérieurs dans les polylignes ───────────────────────

coudes = defaultdict(int)   # (type_tuyau, matiere, angle) -> n

for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB:
        continue
    tp  = CALQUES_PLB[layer]
    mat = MATIERE.get(tp, "?")
    t   = entity.dxftype()

    pts = []
    if t == "LWPOLYLINE":
        pts = list(entity.get_points("xy"))
    elif t == "POLYLINE":
        pts = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]

    for i in range(1, len(pts) - 1):
        ta = turn_angle(pts[i-1], pts[i], pts[i+1])
        if ta is None:
            continue
        label = classify_angle(ta)
        if label:
            coudes[(tp, mat, label)] += 1

# ── 2. COUDES — entités ARC (courbure explicite) ─────────────────────────────

for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB:
        continue
    if entity.dxftype() != "ARC":
        continue
    tp  = CALQUES_PLB[layer]
    mat = MATIERE.get(tp, "?")
    start = entity.dxf.start_angle
    end   = entity.dxf.end_angle
    if end < start:
        end += 360.0
    arc_deg = end - start
    label = classify_angle(arc_deg) or f"autre (~{round(arc_deg/5)*5}°)"
    coudes[(tp, mat, f"ARC {label}")] += 1

# ── 3. TÉS et CROIX — analyse topologique des extrémités ────────────────────

endpoints = defaultdict(list)   # point_arrondi -> [type_tuyau, ...]

for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB:
        continue
    tp = CALQUES_PLB[layer]
    t  = entity.dxftype()
    pts = []
    if t == "LINE":
        s, f = entity.dxf.start, entity.dxf.end
        pts = [(s.x, s.y), (f.x, f.y)]
    elif t == "LWPOLYLINE":
        raw = list(entity.get_points("xy"))
        if raw:
            pts = [(raw[0][0], raw[0][1]), (raw[-1][0], raw[-1][1])]
    elif t == "POLYLINE":
        verts = list(entity.vertices)
        if verts:
            pts = [(verts[0].dxf.location.x, verts[0].dxf.location.y),
                   (verts[-1].dxf.location.x, verts[-1].dxf.location.y)]
    for (x, y) in pts:
        endpoints[round_pt(x, y)].append(tp)

tes   = defaultdict(int)    # (type_tuyau, matiere) -> n
croix = defaultdict(int)

for pt, types in endpoints.items():
    by_type = defaultdict(int)
    for tp in types:
        by_type[tp] += 1
    for tp, deg in by_type.items():
        mat = MATIERE.get(tp, "?")
        if deg == 3:
            tes[(tp, mat)] += 1
        elif deg >= 4:
            croix[(tp, mat)] += 1

# ── 4. Export CSV ─────────────────────────────────────────────────────────────

rows = []

for (tp, mat, angle), n in coudes.items():
    rows.append(("Coude", tp, mat, angle, n))

for (tp, mat), n in tes.items():
    rows.append(("Te", tp, mat, "-", n))

for (tp, mat), n in croix.items():
    rows.append(("Croix", tp, mat, "-", n))

rows.sort(key=lambda r: (r[1], r[0], r[3]))

out = "resultats_raccords_PLB.csv"
with open(out, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["Raccord", "Type de tuyau", "Matiere", "Angle", "Quantite"])
    w.writerows(rows)

# ── 5. Affichage console ──────────────────────────────────────────────────────

print(f"{'Raccord':<12} {'Type de tuyau':<32} {'Mat':<5} {'Angle':<14} {'Qte':>6}")
print("-" * 75)
for raccord, tp, mat, angle, n in rows:
    print(f"{raccord:<12} {tp:<32} {mat:<5} {angle:<14} {n:>6}")

print(f"\nCSV ecrit : {out}")
