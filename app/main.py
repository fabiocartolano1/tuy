import math
import os
import shutil
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import ezdxf
import ezdxf.recover
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI()

ODA_EXE = os.getenv(
    "ODA_EXE",
    r"C:\Program Files\ODA\ODAFileConverter\ODAFileConverter.exe",
)


@app.post("/convert")
async def convert_dwg_to_dxf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".dwg"):
        raise HTTPException(status_code=400, detail="Fichier .dwg requis.")

    if not Path(ODA_EXE).is_file():
        raise HTTPException(status_code=500, detail=f"ODAFileConverter introuvable : {ODA_EXE}")

    tmp_in  = Path(tempfile.mkdtemp())
    tmp_out = Path(tempfile.mkdtemp())

    try:
        dwg_path = tmp_in / file.filename
        dwg_path.write_bytes(await file.read())

        result = subprocess.run(
            [ODA_EXE, str(tmp_in), str(tmp_out), "ACAD2018", "DXF", "0", "1", "*.dwg"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Erreur ODA : {result.stderr}")

        dxf_files = list(tmp_out.glob("*.dxf"))
        if not dxf_files:
            raise HTTPException(status_code=500, detail="ODA n'a produit aucun fichier DXF.")

        dxf_path = dxf_files[0]
        return FileResponse(
            path=str(dxf_path),
            filename=dxf_path.name,
            media_type="application/octet-stream",
            background=None,
        )

    finally:
        shutil.rmtree(tmp_in, ignore_errors=True)
        # tmp_out supprimé après que FileResponse a envoyé le fichier


CALQUES_PLB = {
    "CMT-PLB-EF-U": "MC", "CMT_PLMB_EAU_FROIDE": "MC", "CMT_PLMB_ROBINETTERIE_EAU_FROIDE": "MC",
    "CMT-PLB-EFSG-U": "MC", "CMT_PLMB_EAU_FROIDE_ADOUCIE": "MC", "CMT_PLMB_ROBINETTERIE_EAU_FROIDE_ADOUCIE": "MC",
    "CMT-PLB-EC-U": "MC", "CMT_PLMB_EAU_CHAUDE_SANITAIRE": "MC", "CMT_PLMB_ROBINETTERIE_EAU_CHAUDE_SANITAITE": "MC",
    "CMT-PLB-REC-U": "MC", "CMT_PLMB_BOUCLAGE": "MC", "CMT_PLMB_ROBINETTERIE_BOUCLAGE": "MC",
    "CMT_CVC_EAU_CHAUDE_PRIMAIRE_ALLER": "MC", "CMT_CVC_EAU_CHAUDE_PRIMAIRE_RETOUR": "MC",
    "CMT-PLB-EU": "PVC", "CMT-PLB-EV": "PVC", "CMT-PLB-EV-SOUS DALLAGE": "PVC",
    "CMT-CONDENSATS": "PVC", "CMT-CVC-CONDENSATS": "PVC", "CMT-PLB-VP": "PVC",
}


def _longueur_entite(entity) -> float:
    t = entity.dxftype()
    if t == "LINE":
        s, f = entity.dxf.start, entity.dxf.end
        return math.dist((s.x, s.y, s.z), (f.x, f.y, f.z))
    if t == "LWPOLYLINE":
        pts = list(entity.get_points("xy"))
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    if t == "POLYLINE":
        pts = [(v.dxf.location.x, v.dxf.location.y, v.dxf.location.z) for v in entity.vertices]
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    if t == "ARC":
        r = entity.dxf.radius
        sa, ea = math.radians(entity.dxf.start_angle), math.radians(entity.dxf.end_angle)
        if ea < sa:
            ea += 2 * math.pi
        return r * (ea - sa)
    return 0.0


@app.post("/longueurs")
async def longueurs_par_matiere(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".dxf"):
        raise HTTPException(status_code=400, detail="Fichier .dxf requis.")

    tmp = Path(tempfile.mkdtemp())
    try:
        dxf_path = tmp / file.filename
        dxf_path.write_bytes(await file.read())

        doc, _ = ezdxf.recover.readfile(str(dxf_path))
        totaux: dict[str, float] = defaultdict(float)

        for entity in doc.modelspace():
            matiere = CALQUES_PLB.get(entity.dxf.get("layer", ""))
            if matiere is None:
                continue
            try:
                totaux[matiere] += _longueur_entite(entity)
            except Exception:
                continue

        return {
            "MC":  round(totaux.get("MC",  0.0), 2),
            "PVC": round(totaux.get("PVC", 0.0), 2),
            "unite": "m",
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
