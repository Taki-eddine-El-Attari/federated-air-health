"""TP 3, section 7 - Tests du contrôle d'accès (les deux API doivent être actives)."""
import requests

URL_AIR = "http://127.0.0.1:8001"
URL_HOPITAL = "http://127.0.0.1:8002"
CLE_AIR = "demo-air-123"
CLE_HOPITAL = "demo-hopital-456"

corps_valide = {
    "classifications": [{"date": "2015-01-01", "categorie": "non_elevee"}],
}
corps_invalide = {
    "classifications": [{"date": "2015-01-01", "categorie": "inconnue"}],
}

tests = [
    ("1. /categories sans clé", 401,
     lambda: requests.get(f"{URL_AIR}/categories", timeout=30)),
    ("2. /categories, clé incorrecte", 401,
     lambda: requests.get(f"{URL_AIR}/categories", headers={"X-API-Key": "fausse"}, timeout=30)),
    ("3. /categories, bonne clé", 200,
     lambda: requests.get(f"{URL_AIR}/categories", headers={"X-API-Key": CLE_AIR}, timeout=30)),
    ("4. /analyse-locale, clé incorrecte", 401,
     lambda: requests.post(f"{URL_HOPITAL}/analyse-locale", json=corps_valide,
                           headers={"X-API-Key": "fausse"}, timeout=30)),
    ("5. /analyse-locale, catégorie inconnue", 400,
     lambda: requests.post(f"{URL_HOPITAL}/analyse-locale", json=corps_invalide,
                           headers={"X-API-Key": CLE_HOPITAL}, timeout=30)),
]

echecs = 0
for nom, attendu, appel in tests:
    recu = appel().status_code
    echecs += recu != attendu
    print(f"{nom} : attendu {attendu}, reçu {recu}")

print("Tous les tests sont conformes." if not echecs else f"{echecs} test(s) en échec.")
raise SystemExit(1 if echecs else 0)
