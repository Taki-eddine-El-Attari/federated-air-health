"""Étape 1 - Nœud A (Environnement) : catalogue, contrat, classification signée."""
from contextlib import closing
from pathlib import Path
import hashlib
import hmac
import json
import os
import sqlite3
import uuid

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Nœud A - Environnement")

DOSSIER = Path(__file__).resolve().parent
DB_AIR = DOSSIER / "environnement.db"

# Valeurs de démonstration : à ne JAMAIS utiliser en production.
CLE_API_A = os.getenv("CLE_AIR", "secret-air-key-demo")
SECRET_FEDERATION = os.getenv("SECRET_FEDERATION", "secret-federation-demo").encode()

DATASET_ID = "dataset-air-sao-paulo"
FINALITE_AUTORISEE = "research"
CONSOMMATEURS_AUTORISES = {"laboratoire-iasd"}
SEUIL_PM25 = 30.0  # seuil pédagogique (µg/m³), pas une référence réglementaire

with closing(sqlite3.connect(DB_AIR)) as conn:
    VILLES = [v for (v,) in conn.execute("SELECT DISTINCT ville FROM qualite_air ORDER BY ville")]

# Catalogue simplifié inspiré de DCAT (non conforme au standard).
CATALOGUE = [
    {
        "dataset_id": DATASET_ID,
        "title": "Qualité de l'air - PM2.5, État de São Paulo",
        "description": "Concentrations journalières moyennes de PM2.5 par commune "
                       "(CETESB, via Zenodo 10.5281/zenodo.23164494).",
        "publisher": "Organisation Environnement",
        "temporal_coverage": "2015-01-01/2025-12-31",
        "spatial_coverage": VILLES,
        "unit": "µg/m³",
        "access_endpoint": "/contracts/negotiate",
        "allowed_purpose": FINALITE_AUTORISEE,  # règle inspirée d'ODRL
    }
]

# Contrats en mémoire : perdus au redémarrage du serveur.
contrats = {}


class DemandeContrat(BaseModel):
    dataset_id: str
    consumer_id: str
    purpose: str
    ville: str = "São Paulo"


def verifier_cle(x_api_key):
    if x_api_key is None or not hmac.compare_digest(x_api_key.encode(), CLE_API_A.encode()):
        raise HTTPException(status_code=401, detail="Clé API invalide")


def signer(contract_id, consumer_id, ville, classifications):
    """Signature HMAC partagée avec le nœud B : prouve que A a émis ces
    classifications pour ce contrat, ce consommateur et cette commune."""
    message = json.dumps(
        {
            "contract_id": contract_id,
            "consumer_id": consumer_id,
            "ville": ville,
            "classifications": classifications,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(SECRET_FEDERATION, message, hashlib.sha256).hexdigest()


@app.get("/catalog")
def lire_catalogue():
    return CATALOGUE


@app.post("/contracts/negotiate")
def negocier_contrat(demande: DemandeContrat, x_api_key: str | None = Header(default=None)):
    verifier_cle(x_api_key)

    if demande.dataset_id != DATASET_ID or demande.ville not in VILLES:
        raise HTTPException(status_code=404, detail="Jeu de données ou commune inexistant")

    if demande.purpose != FINALITE_AUTORISEE:
        raise HTTPException(status_code=403, detail="Finalité non autorisée")

    if demande.consumer_id not in CONSOMMATEURS_AUTORISES:
        raise HTTPException(status_code=403, detail="Consommateur non autorisé")

    contract_id = f"contract-air-{uuid.uuid4().hex[:8]}"
    contrats[contract_id] = {
        "status": "AGREED",
        "dataset_id": demande.dataset_id,
        "consumer_id": demande.consumer_id,
        "purpose": demande.purpose,
        "ville": demande.ville,
    }
    return {"contract_id": contract_id, "status": "AGREED"}


@app.get("/classifications")
def lire_classifications(
    contract_id: str,
    consumer_id: str,
    x_api_key: str | None = Header(default=None),
):
    verifier_cle(x_api_key)

    contrat = contrats.get(contract_id)
    if contrat is None:
        raise HTTPException(status_code=403, detail="Contrat inconnu")

    if contrat["status"] != "AGREED" or contrat["dataset_id"] != DATASET_ID:
        raise HTTPException(status_code=403, detail="Contrat non applicable")

    if contrat["purpose"] != FINALITE_AUTORISEE or contrat["consumer_id"] != consumer_id:
        raise HTTPException(status_code=403, detail="Consommateur ou finalité non autorisé")

    # La commune vient du contrat : le laboratoire ne peut pas la changer ici.
    ville = contrat["ville"]
    with closing(sqlite3.connect(DB_AIR)) as conn:
        lignes = conn.execute(
            "SELECT date, pm25 FROM qualite_air WHERE ville = ? ORDER BY date", (ville,)
        ).fetchall()

    classifications = [
        {
            "date": date,
            "categorie": "au_dessus_seuil" if pm25 > SEUIL_PM25 else "sous_seuil",
        }
        for date, pm25 in lignes
    ]
    return {
        "contract_id": contract_id,
        "consumer_id": consumer_id,
        "ville": ville,
        "classifications": classifications,
        "signature": signer(contract_id, consumer_id, ville, classifications),
    }
