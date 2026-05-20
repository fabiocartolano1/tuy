# Fiabilité des données extraites du DXF

## Données fiables à 100%

### Type de réseau
- **Source** : nom du calque (ex: `CMT-PLB-EU` = Eaux usées)
- **Fiabilité** : 100% — convention explicite du bureau d'études, aucune interprétation
- **Exemple** : Eau froide, Eaux vannes, Condensats...

### Matière (MC / PVC)
- **Source** : nom du calque + légende du plan PDF
- **Fiabilité** : 100% — les calques `CMT-PLB-EF/EC/REC` = MC, `CMT-PLB-EU/EV/VP` = PVC
- **Limite** : convention propre à ce bureau d'études, à reverifier sur d'autres plans

### Longueur des tuyaux
- **Source** : géométrie des entités LINE, LWPOLYLINE, ARC dans le DXF
- **Fiabilité** : 100% sur ce qui est dessiné — le calcul est exact
- **Limite** : si le dessinateur a oublié un tronçon ou en a dessiné un en double, le DXF ne le sait pas

### Nombre de coudes
- **Source** : entités ARC + changements d'angle (≥10°) sur les LWPOLYLINE
- **Fiabilité** : 100% sur ce qui est dessiné
- **Limite** : même remarque que pour les longueurs

---

## Données partiellement fiables

### Angle des coudes (90° ou 87°30)
- **Source** : déduit de la matière et du type de réseau (règle métier, pas le DXF)
- **Fiabilité** : ~95% — la règle gravitaire PVC = 87°30 / pression = 90° est standard
- **Limite** : un coude PVC 45° (changement de direction doux) serait compté à tort en 87°30
  Des coudes 45° existent sur les EU/EV, notamment pour les piquages horizontaux

### Diamètre — réseaux PVC (EU, EV, Condensats, VP)
- **Source** : cercles en coupe dans le DXF (rayon = Ø/2), propagés par connectivité réseau
- **Couverture** :
  - Condensats : 100%
  - Eaux vannes : 93%
  - Eaux vannes (sous dallage) : 95%
  - Eaux usées : 86%
  - Ventilation primaire : 68%
- **Fiabilité sur les segments couverts** : ~95% — la méthode cercle/rayon est directe
- **Limite** : 5 à 32% des segments PVC n'ont pas de cercle à portée → diamètre non détecté (marqués `Ø?`)
- **Limite** : la propagation s'arrête aux points de réduction ; si la réduction n'est pas marquée par un cercle, le mauvais diamètre peut se propager

---

## Données non disponibles dans ce DXF

### Diamètre — réseaux MC (Eau froide, Eau chaude, Bouclage)
- **Source** : aucune — le DXF ne contient pas d'annotation de diamètre par segment MC
- **Fiabilité** : 0% — impossible à extraire automatiquement
- **Ce qu'on sait** : les diamètres présents sur ces réseaux (ex: Ø16, Ø20, Ø26, Ø32, Ø40, Ø63 pour EF)
  mais on ne sait pas quelle longueur est en Ø16 vs Ø40
- **Solution possible** : extraction depuis le PDF par OCR (PyMuPDF déjà installé)

### Tés et croix
- **Source** : topologie du réseau — un point où 3 segments se rejoignent = té, 4 segments = croix
- **Fiabilité** : 100% sur ce qui est dessiné (même méthode que les coudes, index spatial)
- **Limite** : même remarque que longueurs/coudes — dépend de la qualité du dessin

### Réductions (changement de diamètre)
- **Source** : points marqués par deux cercles de diamètres différents (déjà utilisés comme
  points d'arrêt dans la propagation)
- **Fiabilité** : ~90% sur les réseaux PVC couverts par les cercles
- **Fiabilité** : 0% sur les réseaux MC

### Manchons, robinetterie
- **Source** : aucune — non modélisés comme entités géométriques mesurables
- **Ce qu'on a** : quelques blocs INSERT (ballon ECS, siphon, descente ECS...) mais sans
  attribut de diamètre ni type standardisé
- **Fiabilité** : 0% — nécessite un relevé manuel ou un modèle BIM

### Pentes des réseaux gravitaires
- **Source** : 5 annotations texte "Pente 2.0 cm/m" sur EV-SOUS DALLAGE uniquement
- **Fiabilité** : information présente mais partielle (une seule valeur, pas par segment)

---

## Résumé tableau

| Donnée                        | Fiable | Couverture | Source            |
|-------------------------------|--------|------------|-------------------|
| Type de réseau                | Oui    | 100%       | Calque DXF        |
| Matière (MC/PVC)              | Oui    | 100%       | Calque DXF        |
| Longueur                      | Oui    | 100%       | Géométrie DXF     |
| Nombre de coudes              | Oui    | 100%       | Géométrie DXF     |
| Nombre de tés                 | Oui    | 100%       | Topologie DXF     |
| Nombre de croix               | Oui    | 100%       | Topologie DXF     |
| Angle des coudes              | ~Oui   | 100%       | Règle métier      |
| Diamètre PVC (EU/EV/VP/Cond.) | ~Oui   | 68-100%    | Cercles DXF + BFS |
| Réductions PVC                | ~Oui   | 68-100%    | Cercles DXF       |
| Diamètre MC (EF/EC/REC/EFSG)  | Non    | 0%         | Absent du DXF     |
| Manchons, robinetterie        | Non    | 0%         | Absent du DXF     |
