import csv
import ezdxf
import math
from collections import defaultdict

doc = ezdxf.readfile("CMT-EXE-RDC.dxf")
msp = doc.modelspace()

# Mapping calques → type de tuyau
CALQUES_PLB = {
    # Eau froide
    "CMT-PLB-EF-U":                      "Eau froide",
    "CMT_PLMB_EAU_FROIDE":               "Eau froide",
    "CMT_PLMB_ROBINETTERIE_EAU_FROIDE":  "Eau froide",
    "CMT-PLB-EFSG-U":                    "Eau froide sans gel",
    "CMT_PLMB_EAU_FROIDE_ADOUCIE":       "Eau froide adoucie",
    "CMT_PLMB_ROBINETTERIE_EAU_FROIDE_ADOUCIE": "Eau froide adoucie",
    # Eau chaude sanitaire
    "CMT-PLB-EC-U":                               "Eau chaude sanitaire",
    "CMT_PLMB_EAU_CHAUDE_SANITAIRE":              "Eau chaude sanitaire",
    "CMT_PLMB_ROBINETTERIE_EAU_CHAUDE_SANITAITE": "Eau chaude sanitaire",
    # Bouclage sanitaire
    "CMT-PLB-REC-U":                      "Bouclage sanitaire",
    "CMT_PLMB_BOUCLAGE":                  "Bouclage sanitaire",
    "CMT_PLMB_ROBINETTERIE_BOUCLAGE":     "Bouclage sanitaire",
    # Eaux usées / vannes
    "CMT-PLB-EU":              "Eaux usées",
    "CMT-PLB-EV":              "Eaux vannes",
    "CMT-PLB-EV-SOUS DALLAGE": "Eaux vannes (sous dallage)",
    # Condensats clim
    "CMT-CONDENSATS":          "Condensats climatisation",
    "CMT-CVC-CONDENSATS":      "Condensats climatisation",
    # Ventilation primaire
    "CMT-PLB-VP":              "Ventilation primaire",
    # Eau chaude primaire CVC
    "CMT_CVC_EAU_CHAUDE_PRIMAIRE_ALLER":  "ECS primaire aller",
    "CMT_CVC_EAU_CHAUDE_PRIMAIRE_RETOUR": "ECS primaire retour",
}

# Mapping type de tuyau → matière
MATIERE = {
    "Eau froide":                    "MC",
    "Eau froide sans gel":           "MC",
    "Eau froide adoucie":            "MC",
    "Eau chaude sanitaire":          "MC",
    "Bouclage sanitaire":            "MC",
    "ECS primaire aller":            "MC",
    "ECS primaire retour":           "MC",
    "Eaux usées":                    "PVC",
    "Eaux vannes":                   "PVC",
    "Eaux vannes (sous dallage)":    "PVC",
    "Condensats climatisation":      "PVC",
    "Ventilation primaire":          "PVC",
}


def longueur_line(e):
    s, f = e.dxf.start, e.dxf.end
    return math.dist((s.x, s.y, s.z), (f.x, f.y, f.z))


def longueur_lwpolyline(e):
    pts = list(e.get_points("xy"))
    total = 0.0
    for i in range(len(pts) - 1):
        total += math.dist(pts[i], pts[i + 1])
    if e.is_closed and len(pts) > 1:
        total += math.dist(pts[-1], pts[0])
    return total


def longueur_polyline(e):
    pts = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) for v in e.vertices]
    total = 0.0
    for i in range(len(pts) - 1):
        total += math.dist(pts[i], pts[i + 1])
    if e.is_closed and len(pts) > 1:
        total += math.dist(pts[-1], pts[0])
    return total


def longueur_arc(e):
    r = e.dxf.radius
    start = math.radians(e.dxf.start_angle)
    end = math.radians(e.dxf.end_angle)
    if end < start:
        end += 2 * math.pi
    return r * (end - start)


longueurs = defaultdict(float)
nb_entites = defaultdict(int)

for entity in msp:
    layer = entity.dxf.get("layer", "")
    if layer not in CALQUES_PLB:
        continue
    type_tuyau = CALQUES_PLB[layer]
    t = entity.dxftype()
    try:
        if t == "LINE":
            l = longueur_line(entity)
        elif t == "LWPOLYLINE":
            l = longueur_lwpolyline(entity)
        elif t == "POLYLINE":
            l = longueur_polyline(entity)
        elif t == "ARC":
            l = longueur_arc(entity)
        else:
            continue
        longueurs[type_tuyau] += l
        nb_entites[type_tuyau] += 1
    except Exception:
        continue

# Conversion unités : le DXF est en mm (AutoCAD par défaut)
# Si les cotes sont en mm → diviser par 1000 pour avoir des mètres
# Si en unités arbitraires il faut ajuster — on affiche les deux

print("=" * 75)
print(f"{'Type de tuyau':<35} {'Matiere':>8}  {'Longueur (m)':>12}  {'Entites':>8}")
print("=" * 75)
total = 0.0
rows = []
for type_tuyau, l in sorted(longueurs.items()):
    total += l
    matiere = MATIERE.get(type_tuyau, "?")
    print(f"{type_tuyau:<35} {matiere:>8}  {l:>12.2f}  {nb_entites[type_tuyau]:>8}")
    rows.append({"Type de tuyau": type_tuyau, "Matiere": matiere,
                 "Longueur (m)": round(l, 2), "Nb entites": nb_entites[type_tuyau]})
print("-" * 75)
print(f"{'TOTAL PLB':<35} {'':>8}  {total:>12.2f}")
print("=" * 75)
print("Unites : metres ($INSUNITS=6)")

csv_path = "resultats_longueurs_PLB.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Type de tuyau", "Matiere", "Longueur (m)", "Nb entites"], delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    writer.writerow({"Type de tuyau": "TOTAL PLB", "Matiere": "", "Longueur (m)": round(total, 2), "Nb entites": ""})
print(f"CSV exporté : {csv_path}")
