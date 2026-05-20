# Projet : Lecture/Analyse de plans PLB en DWG

## Contexte

Travail sur le fichier `CMT-EXE-RDC.dwg` (plan de plomberie RDC).
PDF de référence disponible : `CMT-EXE-RDC-PLB201.pdf`.

### Légende des tuyaux (`legend.txt`)
| Couleur           | Type                    |
|-------------------|-------------------------|
| Bleu (MC)         | Eau froide              |
| Rouge (MC)        | Eau chaude              |
| Orange (MC)       | Bouclage sanitaire      |
| Violet (PVC)      | Condensat de clim       |
| Vert/Marron (PVC) | Eau usée                |

---

## Environnement (Windows 11, Python 3.12.6)

### Packages installés

```bat
pip install ezdxf
pip install "ezdxf[draw]"
```

**Versions installées :**
- `ezdxf` 1.4.4
- `matplotlib` 3.10.9
- `PySide6` 6.11.1
- `PyMuPDF` 1.27.2.3

---

## Conversion DWG → DXF

ODA File Converter installé dans :
`C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe`

Commande utilisée :
```bat
"C:\Program Files\ODA\ODAFileConverter 27.1.0\ODAFileConverter.exe" ^
  "C:\Users\fcartolano\Desktop\tuy" ^
  "C:\Users\fcartolano\Desktop\tuy" ^
  ACAD2018 DXF 0 1 "*.DWG"
```

Résultat : `CMT-EXE-RDC.dxf` (19 Mo)

**Unités du DXF :** `$INSUNITS=6` → **Mètres** (ne pas diviser par 1000)

---

## Résultats : longueurs de tuyauterie PLB (RDC)

Script : `longueurs_plb.py`

| Type de tuyau              | Longueur (m) | Entités |
|----------------------------|-------------:|--------:|
| Eau froide                 |       114.57 |     181 |
| Eau froide sans gel        |         6.12 |      10 |
| Eau froide adoucie         |         0.00 |       0 |
| Eau chaude sanitaire       |        77.52 |     117 |
| Bouclage sanitaire         |        28.68 |      37 |
| Eaux usées                 |        91.32 |     248 |
| Eaux vannes                |        33.17 |     151 |
| Eaux vannes (sous dallage) |       422.93 |    1799 |
| Condensats climatisation   |        59.55 |      96 |
| Ventilation primaire       |         9.33 |      16 |
| **TOTAL PLB**              |   **843.20** |         |

---

## Calques PLB identifiés dans le DXF

```
CMT-PLB-EF-U            → Eau froide unitaire
CMT_PLMB_EAU_FROIDE     → Eau froide
CMT-PLB-EFSG-U          → Eau froide sans gel
CMT_PLMB_EAU_FROIDE_ADOUCIE → Eau froide adoucie
CMT-PLB-EC-U            → Eau chaude sanitaire
CMT_PLMB_EAU_CHAUDE_SANITAIRE → Eau chaude sanitaire
CMT-PLB-REC-U           → Bouclage sanitaire
CMT_PLMB_BOUCLAGE       → Bouclage sanitaire
CMT-PLB-EU              → Eaux usées
CMT-PLB-EV              → Eaux vannes
CMT-PLB-EV-SOUS DALLAGE → Eaux vannes sous dallage
CMT-CONDENSATS          → Condensats climatisation
CMT-CVC-CONDENSATS      → Condensats climatisation
CMT-PLB-VP              → Ventilation primaire
CMT_CVC_EAU_CHAUDE_PRIMAIRE_ALLER  → ECS primaire aller
CMT_CVC_EAU_CHAUDE_PRIMAIRE_RETOUR → ECS primaire retour
```

---

## Fichiers du projet

```
tuy/
├── CMT-EXE-RDC.dwg          # Plan PLB RDC (source)
├── CMT-EXE-RDC.dxf          # Converti par ODA (19 Mo)
├── CMT-EXE-RDC-PLB201.pdf   # PDF de référence
├── legend.txt                # Légende des types de tuyaux
├── analyse_dxf.py            # Inspection calques + entités
├── longueurs_plb.py          # Calcul longueurs par type (résultat ci-dessus)
├── check_units.py            # Vérification unités DXF
└── NOTES.md                  # Ce fichier
```

---

## Prochaines étapes possibles

- [ ] Vérifier une longueur connue vs le PDF (ex : une gaine avec cote au plan)
- [ ] Ajouter le calcul par diamètre (textes/blocs associés aux tuyaux)
- [ ] Export CSV des résultats
- [ ] Étendre à d'autres niveaux (R+1, R+2…) si disponibles
