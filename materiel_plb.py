"""
Liste de materiel PLB - RDC
Methode diametre : cercles en coupe (CIRCLE.rayon = Ø/2) sur les endpoints
des segments, puis propagation BFS via index spatial (grille 5cm).
PVC (EU/EV/VP/Condensats) : diametre par propagation.
MC  (EF/EC/REC/EFSG)      : diametre non disponible dans ce DXF.
"""
import csv
import ezdxf
import math
from collections import defaultdict

doc = ezdxf.readfile("CMT-EXE-RDC.dxf")
msp = doc.modelspace()

CALQUES_PLB = {
    "CMT-PLB-EF-U":                      ("Eau froide",                "MC"),
    "CMT_PLMB_EAU_FROIDE":               ("Eau froide",                "MC"),
    "CMT_PLMB_ROBINETTERIE_EAU_FROIDE":  ("Eau froide",                "MC"),
    "CMT-PLB-EFSG-U":                    ("Eau froide sans gel",        "MC"),
    "CMT_PLMB_EAU_FROIDE_ADOUCIE":       ("Eau froide adoucie",         "MC"),
    "CMT-PLB-EC-U":                      ("Eau chaude sanitaire",       "MC"),
    "CMT_PLMB_EAU_CHAUDE_SANITAIRE":     ("Eau chaude sanitaire",       "MC"),
    "CMT_PLMB_ROBINETTERIE_EAU_CHAUDE_SANITAITE": ("Eau chaude sanitaire","MC"),
    "CMT-PLB-REC-U":                     ("Bouclage sanitaire",         "MC"),
    "CMT_PLMB_BOUCLAGE":                 ("Bouclage sanitaire",         "MC"),
    "CMT-PLB-EU":                        ("Eaux usees",                 "PVC"),
    "CMT-PLB-EV":                        ("Eaux vannes",                "PVC"),
    "CMT-PLB-EV-SOUS DALLAGE":           ("Eaux vannes (sous dallage)", "PVC"),
    "CMT-CONDENSATS":                    ("Condensats climatisation",   "PVC"),
    "CMT-CVC-CONDENSATS":                ("Condensats climatisation",   "PVC"),
    "CMT-PLB-VP":                        ("Ventilation primaire",       "PVC"),
}

GRAVITAIRE = {"Eaux usees", "Eaux vannes", "Eaux vannes (sous dallage)", "Ventilation primaire"}
TOL  = 0.05   # tolerance connexion 5cm
CELL = 0.05   # taille cellule index spatial

def angle_coude(type_tuyau, matiere):
    return "87°30" if (matiere == "PVC" and type_tuyau in GRAVITAIRE) else "90°"

def rayon_to_dia(r):
    candidates = [16, 20, 25, 26, 32, 40, 50, 63, 75, 100, 110, 125]
    d = round(r * 2000)
    best = min(candidates, key=lambda x: abs(x - d))
    return best if abs(best - d) < 8 else None

# -----------------------------------------------------------------------
# Helpers geometrie
# -----------------------------------------------------------------------
def lon_line(e):
    s, f = e.dxf.start, e.dxf.end
    return math.dist((s.x, s.y, s.z), (f.x, f.y, f.z))

def lon_lwpoly(e):
    pts = list(e.get_points("xy"))
    return sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))

def lon_poly(e):
    pts = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) for v in e.vertices]
    return sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))

def lon_arc(e):
    r = e.dxf.radius
    sa = math.radians(e.dxf.start_angle)
    ea = math.radians(e.dxf.end_angle)
    if ea < sa: ea += 2 * math.pi
    return r * (ea - sa)

def ep_line(e):
    s, f = e.dxf.start, e.dxf.end
    return (s.x, s.y), (f.x, f.y)

def ep_lwpoly(e):
    pts = list(e.get_points("xy"))
    return pts[0], pts[-1]

def ep_poly(e):
    verts = list(e.vertices)
    return ((verts[0].dxf.location.x, verts[0].dxf.location.y),
            (verts[-1].dxf.location.x, verts[-1].dxf.location.y))

def ep_arc(e):
    cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
    sa, ea = math.radians(e.dxf.start_angle), math.radians(e.dxf.end_angle)
    return ((cx + r*math.cos(sa), cy + r*math.sin(sa)),
            (cx + r*math.cos(ea), cy + r*math.sin(ea)))

def coudes_lwpoly(e):
    pts = list(e.get_points("xy"))
    n = 0
    for i in range(1, len(pts)-1):
        ax,ay=pts[i-1]; bx,by=pts[i]; cx,cy=pts[i+1]
        v1=(ax-bx,ay-by); v2=(cx-bx,cy-by)
        n1=math.hypot(*v1); n2=math.hypot(*v2)
        if n1<1e-9 or n2<1e-9: continue
        if abs(180-math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))))) >= 10:
            n += 1
    return n

def coudes_poly(e):
    pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
    n = 0
    for i in range(1, len(pts)-1):
        ax,ay=pts[i-1]; bx,by=pts[i]; cx,cy=pts[i+1]
        v1=(ax-bx,ay-by); v2=(cx-bx,cy-by)
        n1=math.hypot(*v1); n2=math.hypot(*v2)
        if n1<1e-9 or n2<1e-9: continue
        if abs(180-math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))))) >= 10:
            n += 1
    return n

# -----------------------------------------------------------------------
# Construction des segments
# -----------------------------------------------------------------------
print("Lecture du DXF...")
segments = {}
sid = 0
for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB: continue
    type_tuyau, matiere = CALQUES_PLB[layer]
    t = entity.dxftype()
    try:
        if   t == "LINE":       l, ep, nc = lon_line(entity),   ep_line(entity),   0
        elif t == "LWPOLYLINE": l, ep, nc = lon_lwpoly(entity), ep_lwpoly(entity), coudes_lwpoly(entity)
        elif t == "POLYLINE":   l, ep, nc = lon_poly(entity),   ep_poly(entity),   coudes_poly(entity)
        elif t == "ARC":        l, ep, nc = lon_arc(entity),    ep_arc(entity),    1
        else: continue
        if l < 1e-6: continue
        segments[sid] = {"layer": layer, "type": type_tuyau, "matiere": matiere,
                         "lon": l, "coudes": nc, "endpoints": ep, "dia": None}
        sid += 1
    except Exception: continue

# -----------------------------------------------------------------------
# Index spatial
# -----------------------------------------------------------------------
cell_idx = defaultdict(list)   # (layer, cx, cy) -> [(sid, (x,y))]
for sid, seg in segments.items():
    for ep in seg["endpoints"]:
        cx = int(ep[0] / CELL)
        cy = int(ep[1] / CELL)
        cell_idx[(seg["layer"], cx, cy)].append((sid, ep))

def neighbors(layer, x, y):
    cx, cy = int(x / CELL), int(y / CELL)
    result = []
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            for s, ep in cell_idx[(layer, cx+dx, cy+dy)]:
                if math.dist((x, y), ep) <= TOL:
                    result.append(s)
    return result

# -----------------------------------------------------------------------
# Cercles -> diametre aux endpoints
# -----------------------------------------------------------------------
# circle_pts[(layer)] = [(dia, x, y)]
circle_pts = defaultdict(list)
for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB or entity.dxftype() != "CIRCLE": continue
    dia = rayon_to_dia(entity.dxf.radius)
    if dia:
        circle_pts[layer].append((dia, entity.dxf.center.x, entity.dxf.center.y))

# Assigner diametre initial : si un endpoint est dans un cercle connu
for sid, seg in segments.items():
    layer = seg["layer"]
    for ep in seg["endpoints"]:
        for dia, cx, cy in circle_pts[layer]:
            if math.dist(ep, (cx, cy)) <= TOL:
                seg["dia"] = dia
                break
        if seg["dia"]: break

# -----------------------------------------------------------------------
# Propagation BFS
# -----------------------------------------------------------------------
# reduction_pts[(layer)] = set of (x,y) ou le diametre change
reduction_pts = defaultdict(set)
for layer, pts in circle_pts.items():
    seen = {}
    for dia, cx, cy in pts:
        key = (round(cx, 2), round(cy, 2))
        if key in seen and seen[key] != dia:
            reduction_pts[layer].add(key)
        seen[key] = dia

def is_reduction(layer, ep):
    key = (round(ep[0], 2), round(ep[1], 2))
    return key in reduction_pts[layer]

changed = True
iterations = 0
while changed and iterations < 100:
    changed = False
    iterations += 1
    for sid, seg in segments.items():
        if seg["dia"] is None: continue
        for ep in seg["endpoints"]:
            if is_reduction(seg["layer"], ep): continue
            for nsid in neighbors(seg["layer"], ep[0], ep[1]):
                if nsid == sid: continue
                neighbor = segments[nsid]
                if neighbor["dia"] is None:
                    neighbor["dia"] = seg["dia"]
                    changed = True

total = len(segments)
with_dia = sum(1 for s in segments.values() if s["dia"] is not None)
print(f"Propagation : {iterations} iterations")
print(f"Segments avec diametre : {with_dia}/{total} ({100*with_dia//total}%)")

# couverture par calque
from collections import Counter
layer_total   = Counter(s["layer"] for s in segments.values())
layer_with_dia = Counter(s["layer"] for s in segments.values() if s["dia"])
print()
for layer in sorted(layer_total):
    t2 = layer_total[layer]
    w = layer_with_dia.get(layer, 0)
    print(f"  {layer:<45} {w}/{t2} ({100*w//t2}%)")

# -----------------------------------------------------------------------
# Detection des tes et croix (degre des noeuds)
# -----------------------------------------------------------------------
# Pour chaque endpoint, compter combien de segments s'y connectent
node_segs = defaultdict(set)   # (layer, cx, cy) -> set of sid
for sid, seg in segments.items():
    for ep in seg["endpoints"]:
        cx, cy = int(ep[0] / CELL), int(ep[1] / CELL)
        # cle de noeud = premier endpoint trouve dans un rayon TOL
        node_key = None
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for s2, ep2 in cell_idx[(seg["layer"], cx+dx, cy+dy)]:
                    if math.dist(ep, ep2) <= TOL:
                        nk = (seg["layer"], round(ep2[0], 2), round(ep2[1], 2))
                        if node_key is None:
                            node_key = nk
        if node_key:
            node_segs[node_key].add(sid)

tes    = defaultdict(int)   # (type, matiere, dia) -> nb
croix  = defaultdict(int)
reductions = defaultdict(int)

for node_key, sids in node_segs.items():
    if len(sids) < 3:
        continue
    layer = node_key[0]
    type_tuyau, matiere = CALQUES_PLB[layer]
    # diametre majoritaire des segments connectes
    dias = [segments[s]["dia"] for s in sids if segments[s]["dia"]]
    dia = max(set(dias), key=dias.count) if dias else 0
    key = (type_tuyau, matiere, dia)
    if len(sids) == 3:
        tes[key] += 1
    elif len(sids) >= 4:
        croix[key] += 1

# Reductions : points ou deux cercles de diametres differents se touchent
for layer, pts in circle_pts.items():
    type_tuyau, matiere = CALQUES_PLB[layer]
    for i, (dia1, x1, y1) in enumerate(pts):
        for dia2, x2, y2 in pts[i+1:]:
            if dia1 != dia2 and math.dist((x1,y1),(x2,y2)) <= TOL * 4:
                key = (type_tuyau, matiere, max(dia1, dia2))
                reductions[key] += 1

# -----------------------------------------------------------------------
# Agregation + export
# -----------------------------------------------------------------------
longueurs = defaultdict(float)
nb_coudes  = defaultdict(int)
for seg in segments.values():
    dia = seg["dia"] or 0
    key = (seg["type"], seg["matiere"], dia)
    longueurs[key] += seg["lon"]
    nb_coudes[key] += seg["coudes"]

rows = []
for key in sorted(longueurs):
    type_tuyau, matiere, dia = key
    l  = longueurs[key]
    nc = nb_coudes[key]
    nt = tes.get(key, 0)
    nx = croix.get(key, 0)
    nr = reductions.get(key, 0)
    dia_str = f"Ø{dia}" if dia else "Ø?"
    angle   = angle_coude(type_tuyau, matiere)
    rem     = "" if dia else "diametre non detecte"
    rows.append({"Designation": f"Tube {matiere} {dia_str}", "Type reseau": type_tuyau,
                 "Matiere": matiere, "Diametre (mm)": dia or "?",
                 "Quantite": round(l, 2), "Unite": "m", "Remarque": rem})
    if nc > 0:
        rows.append({"Designation": f"Coude {matiere} {angle} {dia_str}", "Type reseau": type_tuyau,
                     "Matiere": matiere, "Diametre (mm)": dia or "?",
                     "Quantite": nc, "Unite": "u", "Remarque": rem})
    if nt > 0:
        rows.append({"Designation": f"Te {matiere} {dia_str}", "Type reseau": type_tuyau,
                     "Matiere": matiere, "Diametre (mm)": dia or "?",
                     "Quantite": nt, "Unite": "u", "Remarque": rem})
    if nx > 0:
        rows.append({"Designation": f"Croix {matiere} {dia_str}", "Type reseau": type_tuyau,
                     "Matiere": matiere, "Diametre (mm)": dia or "?",
                     "Quantite": nx, "Unite": "u", "Remarque": rem})
    if nr > 0:
        rows.append({"Designation": f"Reduction {matiere} {dia_str}", "Type reseau": type_tuyau,
                     "Matiere": matiere, "Diametre (mm)": dia or "?",
                     "Quantite": nr, "Unite": "u", "Remarque": rem})

csv_path = "liste_materiel_PLB.csv"
fields = ["Designation", "Type reseau", "Matiere", "Diametre (mm)", "Quantite", "Unite", "Remarque"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)

print(f"\nCSV : {csv_path}  ({len(rows)} lignes)\n")
print(f"{'Designation':<42} {'Qte':>8} {'U':>3}")
print("-" * 60)
for r in rows:
    flag = "  !" if r["Remarque"] else ""
    print(f"{r['Designation']:<42} {r['Quantite']:>8} {r['Unite']:>3}{flag}")
