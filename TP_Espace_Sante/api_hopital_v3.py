import os
import sqlite3
from collections import defaultdict
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="API Hôpital - TP3")
CLE_API = os.getenv("CLE_HOPITAL", "demo-hopital-456")

def verifier_cle(x_api_key):
    if x_api_key != CLE_API:
        raise HTTPException(status_code=401, detail="Clé API invalide")

class Classification(BaseModel):
    date: str
    categorie: str

class DemandeAnalyse(BaseModel):
    ville: str = "São Paulo"
    classifications: list[Classification]

@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}

@app.post("/analyse-locale")
def analyse_locale(
    demande: DemandeAnalyse,
    x_api_key: str = Header(default="")
):
    verifier_cle(x_api_key)
    autorisees = {"elevee", "non_elevee"}
    if any(c.categorie not in autorisees
           for c in demande.classifications):
        raise HTTPException(status_code=400, detail="Catégorie invalide")

    dates = [c.date for c in demande.classifications]
    if len(dates) != len(set(dates)):
        raise HTTPException(status_code=400, detail="Dates en double")

    groupes = {c.date: c.categorie for c in demande.classifications}
    db = sqlite3.connect("hopital.db")
    lignes = db.execute(
        "SELECT date, nombre FROM admissions WHERE ville = ?", (demande.ville,)
    ).fetchall()
    db.close()

    statistiques = defaultdict(list)
    for date, nombre in lignes:
        categorie = groupes.get(date)
        if categorie is not None:
            statistiques[categorie].append(nombre)

    resultat = {}
    for categorie in ("elevee", "non_elevee"):
        valeurs = statistiques[categorie]
        resultat[categorie] = {
            "nombre_jours": len(valeurs),
            "moyenne_admissions": (
                round(sum(valeurs) / len(valeurs), 2)
                if valeurs else None
            )
        }
    return resultat
