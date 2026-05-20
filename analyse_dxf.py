import ezdxf
from collections import defaultdict

doc = ezdxf.readfile("CMT-EXE-RDC.dxf")
msp = doc.modelspace()

# Calques
print("=== CALQUES ===")
for layer in sorted(doc.layers, key=lambda l: l.dxf.name):
    color = layer.dxf.get("color", "?")
    print(f"  {layer.dxf.name:<40} couleur={color}")

# Entités par type
print("\n=== ENTITES PAR TYPE ===")
counts = defaultdict(int)
for e in msp:
    counts[e.dxftype()] += 1
for t, n in sorted(counts.items(), key=lambda x: -x[1]):
    print(f"  {t:<20} {n}")

# Entités par calque
print("\n=== ENTITES PAR CALQUE (top 20) ===")
by_layer = defaultdict(int)
for e in msp:
    by_layer[e.dxf.get("layer", "?")] += 1
for layer, n in sorted(by_layer.items(), key=lambda x: -x[1])[:20]:
    print(f"  {layer:<40} {n}")
