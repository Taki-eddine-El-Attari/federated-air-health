import sqlite3
from fastapi import FastAPI, Query

app = FastAPI(title="API Hôpital")

@app.get("/")
def accueil():
    return {"organisation": "Hôpital régional"}

@app.get("/admissions")
def obtenir_admissions(
    ville: str | None = None,
    limit: int = Query(default=1000, ge=1, le=10000),
    offset: int = Query(default=0, ge=0),
):
    db = sqlite3.connect("hopital.db")
    db.row_factory = sqlite3.Row
    lignes = db.execute("""
        SELECT date, ville, nombre
        FROM admissions
        WHERE ? IS NULL OR ville = ?
        ORDER BY ville, date
        LIMIT ? OFFSET ?
    """, (ville, ville, limit, offset)).fetchall()
    db.close()
    return [dict(ligne) for ligne in lignes]

@app.get("/statistiques")
def statistiques():
    db = sqlite3.connect("hopital.db")
    resultat = db.execute("""
        SELECT COUNT(*), AVG(nombre) FROM admissions
    """).fetchone()
    db.close()
    return {
        "nombre_jours": resultat[0],
        "moyenne_admissions": round(resultat[1], 2)
    }
