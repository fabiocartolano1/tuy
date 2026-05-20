import os
import ezdxf
import math

_ROOT = os.path.join(os.path.dirname(__file__), "..")
doc = ezdxf.readfile(os.path.join(_ROOT, "plans", "CMT-EXE-RDC.dxf"))
msp = doc.modelspace()

# Unités déclarées dans le header
insunits = doc.header.get("$INSUNITS", "non défini")
unit_names = {0:"Non défini",1:"Pouces",2:"Pieds",3:"Miles",4:"Millimètres",
              5:"Centimètres",6:"Mètres",7:"Kilomètres",14:"Décimètres"}
print(f"$INSUNITS : {insunits} = {unit_names.get(insunits, '?')}")
print(f"$MEASUREMENT : {doc.header.get('$MEASUREMENT', '?')} (0=Impérial, 1=Métrique)")

# Echantillon de lignes sur calque EF (eau froide)
print("\n=== Echantillon lignes CMT-PLB-EF-U (raw) ===")
n = 0
for e in msp.query("LINE[layer=='CMT-PLB-EF-U']"):
    s, f = e.dxf.start, e.dxf.end
    l = math.dist((s.x, s.y), (f.x, f.y))
    print(f"  ({s.x:.1f},{s.y:.1f}) → ({f.x:.1f},{f.y:.1f})  longueur brute={l:.2f}")
    n += 1
    if n >= 5:
        break

print("\n=== Echantillon LWPOLYLINE CMT-PLB-EU (raw) ===")
n = 0
for e in msp.query("LWPOLYLINE[layer=='CMT-PLB-EU']"):
    pts = list(e.get_points("xy"))
    total = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
    print(f"  {len(pts)} pts, longueur brute={total:.2f}")
    n += 1
    if n >= 5:
        break
