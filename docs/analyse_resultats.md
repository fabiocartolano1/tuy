# Analyse PLB - CMT-EXE-RDC

Projet : Plateforme camions - La Mole (83310), Ecopole Maraveou  
Maître d'œuvre : Logabat Ingénierie  
Entreprise : Compagnie Méridionale d'Applications Thermiques  
Plan : CMT-EXE-RDC-PLB201 indice D (19/05/2025)

---

## Résultats longueurs (DXF → API)

| Matière | Longueur |
|---------|----------|
| MC (cuivre/multicouche) | **225,14 m** |
| PVC | **608,91 m** |

Obtenu via `POST /longueurs` avec `CMT-EXE-RDC.dxf`.

Le PVC élevé (608 m) s'explique par le réseau `CMT-PLB-EV-SOUS DALLAGE` (eaux vannes enterrées sous dalle) qui représente une part importante du linéaire.

---

## Cohérence avec le PDF

Le PDF (plan d'exécution échelle 1/50) ne contient pas de nomenclature de longueurs — c'est un plan graphique. Il confirme en revanche :

- Les matières utilisées : MC Ø16 à Ø40, PVC Ø40 à Ø110
- La densité de sanitaires : WC×8, douches×9, LM×7, urinoirs×4 + station lavage 3UP
- Un ballon ECS 1500 L, une pompe de bouclage, une arrivée AEP Ø63

Les ordres de grandeur sont cohérents avec le bâtiment.

---

## Ce qu'on peut détecter dans le DXF

### Longueurs
Fiables pour les deux matières. Les entités LINE, LWPOLYLINE, POLYLINE et ARC sont toutes comptées.

### Diamètres
| Matière | Situation |
|---------|-----------|
| PVC | 95 cercles de coupe détectés (Ø40, Ø50, Ø100, Ø110) — propagation BFS possible |
| MC | **Aucun cercle de coupe** — diamètres non disponibles dans ce DXF |

Le dessinateur n'a pas représenté les sections des tuyaux MC. Pour avoir les diamètres MC il faudrait que le BIM les ajoute, ou les saisir manuellement.

### Raccords

#### Coudes
- **PVC** : coudes réels à commander (87°30 pour gravitaire, 90° pour le reste)
- **MC Ø < 50** : **pas de raccord** — le tuyau est cintré sur chantier (cintreuse ou à la main)
- **MC Ø ≥ 50** : coude à sertir/braser à commander

#### Tés, croix, réductions
- Toujours des raccords physiques, **quelle que soit la matière et le diamètre** — impossible à faire sans pièce.

#### Réductions dans le DXF
Détectées en cherchant deux cercles de diamètres différents qui se touchent. Résultat : **4 réductions PVC détectées** — trop peu pour être exhaustif, le dessinateur ne les a pas systématiquement représentées. Pour le MC : zéro détectable.

---

## Architecture technique

```
tuy/
├── app/
│   └── main.py          ← API FastAPI
├── plans/               ← CMT-EXE-RDC.dxf / .dwg / .pdf
├── scripts/             ← scripts d'analyse standalone
├── resultats/           ← CSV de sortie
└── docs/                ← ce fichier + notes
```

### Routes API disponibles

| Route | Input | Output |
|-------|-------|--------|
| `POST /convert` | `.dwg` | `.dxf` (via ODA File Converter) |
| `POST /longueurs` | `.dxf` | `{ MC: float, PVC: float, unite: "m" }` |

ODA File Converter configuré via variable d'env `ODA_EXE` (défaut : chemin Windows standard).  
Lancement : `uvicorn app.main:app --port 8000`

---

## Limites et points d'attention

1. **Diamètres MC absents** du DXF → liste de matériel MC incomplète sans intervention du dessinateur
2. **Réductions peu fiables** même en PVC (seulement 4 trouvées, probablement sous-représentées)
3. **Coudes MC** ne correspondent pas à des raccords physiques (cintrés) — ne pas les inclure dans les commandes pour Ø < 50
4. **Tés MC** : toujours des raccords réels à commander
5. Le réseau `SOUS DALLAGE` gonfle significativement le linéaire PVC — à isoler si besoin d'un sous-total par zone
