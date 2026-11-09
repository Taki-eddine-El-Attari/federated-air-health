import sqlite3
from fastapi import FastAPI, Query

app = FastAPI(title="API Environnement")

@app.get("/")
def accueil():
    return {"organisation": "Direction de l'environnement"}

@app.get("/mesures")
def obtenir_mesures(
    ville: str | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
):
    db = sqlite3.connect("environnement.db")
    db.row_factory = sqlite3.Row
    lignes = db.execute("""
        SELECT date, ville, pm25
        FROM qualite_air
        WHERE ? IS NULL OR ville = ?
        ORDER BY ville, date
        LIMIT ? OFFSET ?
    """, (ville, ville, limit, offset)).fetchall()
    db.close()
    return [dict(ligne) for ligne in lignes]

@app.get("/statistiques")
def statistiques():
    db = sqlite3.connect("environnement.db")
    resultat = db.execute("""
        SELECT COUNT(*), AVG(pm25) FROM qualite_air
    """).fetchone()
    db.close()
    return {
        "nombre_jours": resultat[0],
        "moyenne_pm25": round(resultat[1], 2)
    }
