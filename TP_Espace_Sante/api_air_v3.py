import os
import sqlite3
from fastapi import FastAPI, Header, HTTPException

app = FastAPI(title="API Environnement - TP3")
CLE_API = os.getenv("CLE_ENVIRONNEMENT", "demo-air-123")

def verifier_cle(x_api_key):
    if x_api_key != CLE_API:
        raise HTTPException(status_code=401, detail="Clé API invalide")

@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement"}

@app.get("/categories")
def categories(ville: str = "São Paulo", x_api_key: str = Header(default="")):
    verifier_cle(x_api_key)
    db = sqlite3.connect("environnement.db")
    lignes = db.execute("""
        SELECT date,
          CASE WHEN pm25 > 30 THEN 'elevee'
               ELSE 'non_elevee' END
        FROM qualite_air WHERE ville = ? ORDER BY date
    """, (ville,)).fetchall()
    db.close()
    return [
        {"date": date, "categorie": categorie}
        for date, categorie in lignes
    ]
