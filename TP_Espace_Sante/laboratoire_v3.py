import os
import requests

URL_AIR = "http://127.0.0.1:8001"
URL_HOPITAL = "http://127.0.0.1:8002"
CLE_AIR = os.getenv("CLE_ENVIRONNEMENT", "demo-air-123")
CLE_HOPITAL = os.getenv("CLE_HOPITAL", "demo-hopital-456")
VILLE = "São Paulo"

r_air = requests.get(
    f"{URL_AIR}/categories",
    params={"ville": VILLE},
    headers={"X-API-Key": CLE_AIR}, timeout=30
)
r_air.raise_for_status()
classifications = r_air.json()

r_hopital = requests.post(
    f"{URL_HOPITAL}/analyse-locale",
    headers={"X-API-Key": CLE_HOPITAL},
    json={"ville": VILLE, "classifications": classifications},
    timeout=30
)
r_hopital.raise_for_status()
resultats = r_hopital.json()

elevee = resultats["elevee"]
non_elevee = resultats["non_elevee"]

print("--- Analyse régionale :", VILLE, "---")
print("Pollution élevée :", elevee)
print("Pollution non élevée :", non_elevee)

if (elevee["moyenne_admissions"] is not None
        and non_elevee["moyenne_admissions"] is not None):
    difference = (
        elevee["moyenne_admissions"]
        - non_elevee["moyenne_admissions"]
    )
    print("Différence entre les moyennes :", round(difference, 2))
