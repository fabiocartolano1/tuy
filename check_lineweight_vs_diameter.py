# -*- coding: utf-8 -*-
"""
Compare lineweights des tuyaux avec les cercles (coupes) proches
pour tester si lineweight * echelle = diametre reel.
"""
import sys
import ezdxf
import math
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

doc = ezdxf.readfile("CMT-EXE-RDC.dxf")
msp = doc.modelspace()

CALQUES_PLB = {
    "CMT-PLB-EF-U", "CMT_PLMB_EAU_FROIDE",
    "CMT-PLB-EC-U", "CMT_PLMB_EAU_CHAUDE_SANITAIRE",
    "CMT-PLB-REC-U", "CMT_PLMB_BOUCLAGE",
    "CMT-PLB-EU", "CMT-PLB-EV", "CMT-PLB-EV-SOUS DALLAGE",
}

# 1. Inventaire des lineweights sur les tuyaux
print("=== LINEWEIGHTS SUR TUYAUX PLB ===")
lw_counts = defaultdict(int)
for e in msp:
    if e.dxf.get("layer", "") not in CALQUES_PLB:
        continue
    if e.dxftype() not in ("LINE", "LWPOLYLINE", "POLYLINE", "ARC"):
        continue
    lw = e.dxf.get("lineweight", -1)  # en 1/100 mm, -1 = BYLAYER
    lw_counts[lw] += 1

for lw, n in sorted(lw_counts.items()):
    lw_mm = lw / 100 if lw > 0 else "BYLAYER"
    print(f"  lineweight={lw} ({lw_mm} mm) -> {n} entites")

# 2. Diametres des cercles (coupes)
print("\n=== CERCLES (coupes de tuyaux) ===")
circles = []
for e in msp:
    if e.dxftype() != "CIRCLE":
        continue
    r = e.dxf.radius
    d_mm = r * 1000  # unites = metres, convertir en mm
    circles.append((e.dxf.center.x, e.dxf.center.y, d_mm))

diam_counts = defaultdict(int)
for _, _, d in circles:
    d_round = round(d)
    diam_counts[d_round] += 1

print(f"  Nombre total de cercles : {len(circles)}")
print("  Diametres les plus frequents (mm) :")
for d, n in sorted(diam_counts.items(), key=lambda x: -x[1])[:15]:
    print(f"    D {d:3d} mm -> {n} cercles")

# 3. Pour chaque lineweight, chercher les cercles proches
print("\n=== CORRELATION lineweight / cercles proches (rayon 0.5m) ===")
RAYON = 0.5  # metres

segments_by_lw = defaultdict(list)
for e in msp:
    if e.dxf.get("layer", "") not in CALQUES_PLB:
        continue
    if e.dxftype() == "LINE":
        lw = e.dxf.get("lineweight", -1)
        mx = (e.dxf.start.x + e.dxf.end.x) / 2
        my = (e.dxf.start.y + e.dxf.end.y) / 2
        segments_by_lw[lw].append((mx, my))

for lw, midpoints in sorted(segments_by_lw.items()):
    lw_mm = lw / 100 if lw > 0 else "BYLAYER"
    diams_found = []
    for mx, my in midpoints[:50]:  # limiter a 50 pour la rapidite
        for cx, cy, d in circles:
            if math.dist((mx, my), (cx, cy)) < RAYON:
                diams_found.append(d)
    if diams_found:
        avg = sum(diams_found) / len(diams_found)
        unique = sorted(set(round(d) for d in diams_found))
        print(f"  LW={lw} ({lw_mm} mm)  ->  {len(diams_found)} cercles trouves"
              f"  |  D moy={avg:.1f}mm  |  valeurs uniques: {unique[:10]}")
    else:
        print(f"  LW={lw} ({lw_mm} mm)  ->  aucun cercle proche trouve")

# 4. Lineweights par calque
print("\n=== LINEWEIGHT PAR CALQUE PLB ===")
for layer in doc.layers:
    if layer.dxf.name in CALQUES_PLB:
        lw = layer.dxf.get("lineweight", -1)
        lw_mm = lw / 100 if lw > 0 else "BYLAYER"
        print(f"  {layer.dxf.name:<40} LW={lw} ({lw_mm} mm)")
