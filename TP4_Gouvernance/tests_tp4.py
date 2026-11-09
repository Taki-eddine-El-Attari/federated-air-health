"""TP 4 - Tableau de tests des nœuds A et B (les deux API doivent être actives).

Après un passage complet, arrêter puis relancer l'API Hôpital, et exécuter
"python tests_tp4.py --apres-redemarrage" pour vérifier que le budget a persisté.
"""
from contextlib import closing
from pathlib import Path
import sqlite3
import sys

import requests

DB_HOPITAL = Path(__file__).resolve().parent / "hopital.db"
URL_AIR = "http://127.0.0.1:8001"
URL_HOPITAL = "http://127.0.0.1:8002"
CLE_A = {"X-API-Key": "secret-air-key-demo"}
CLE_B = {"X-API-Key": "secret-hospital-key-demo"}
FAUSSE = {"X-API-Key": "mauvaise-cle"}
DEMANDE = {"dataset_id": "dataset-air-sao-paulo", "consumer_id": "laboratoire-iasd", "purpose": "research"}

echecs = 0


def verifier(nom, attendu, recu):
    global echecs
    echecs += recu != attendu
    print(f"{nom} : attendu {attendu}, reçu {recu}")


def negocier(cle=CLE_A, **champs):
    return requests.post(f"{URL_AIR}/contracts/negotiate", json={**DEMANDE, **champs}, headers=cle, timeout=30)


def paquet_signe(**champs):
    contract_id = negocier(**champs).json()["contract_id"]
    r = requests.get(f"{URL_AIR}/classifications",
                     params={"contract_id": contract_id, "consumer_id": DEMANDE["consumer_id"]},
                     headers=CLE_A, timeout=30)
    r.raise_for_status()
    return r.json()


def calculer(corps, cle=CLE_B):
    return requests.post(f"{URL_HOPITAL}/compute", json=corps, headers=cle, timeout=30)


def verifier_budget_epuise(nom):
    verifier(nom, 429, calculer({**paquet_signe(), "apply_dp": True, "epsilon": 1.0}).status_code)


def bilan():
    print("\nTous les tests sont conformes." if not echecs else f"\n{echecs} test(s) en échec.")
    raise SystemExit(1 if echecs else 0)


if "--apres-redemarrage" in sys.argv:
    print("--- Budget après redémarrage de l'API Hôpital ---")
    verifier_budget_epuise("Budget toujours épuisé après redémarrage (nouveau contrat)")
    bilan()

print("--- Nœud A ---")
verifier("Catalogue", 200, requests.get(f"{URL_AIR}/catalog", timeout=30).status_code)
verifier("Accès autorisé (research)", 200, negocier().status_code)
verifier("Finalité non autorisée", 403, negocier(purpose="commercial").status_code)
verifier("Jeu de données inexistant", 404, negocier(dataset_id="dataset-inconnu").status_code)
verifier("Commune inexistante", 404, negocier(ville="Atlantis").status_code)
verifier("Consommateur non autorisé", 403, negocier(consumer_id="entreprise-x").status_code)
verifier("Clé API incorrecte", 401, negocier(cle=FAUSSE).status_code)

print("\n--- Nœud B ---")
paquet = paquet_signe()
r = calculer(paquet)
verifier("Calcul sans bruit", 200, r.status_code)
res = r.json()
print("   Résultat :", res["au_dessus_seuil"], res["sous_seuil"])
verifier("Moyenne au-dessus du seuil", 151.4, res["au_dessus_seuil"]["moyenne"])
verifier("Moyenne sous le seuil", 143.69, res["sous_seuil"]["moyenne"])
verifier("Clé API incorrecte", 401, calculer(paquet, cle=FAUSSE).status_code)
verifier("Signature falsifiée (une ligne en moins)", 403,
         calculer({**paquet, "classifications": paquet["classifications"][1:]}).status_code)
verifier("Attaque TP 3 (un seul jour)", 403,
         calculer({**paquet, "classifications": paquet["classifications"][:1]}).status_code)
verifier("Commune modifiée après signature", 403, calculer({**paquet, "ville": "Osasco"}).status_code)

print("\n--- Seuil minimal ---")
g = calculer(paquet_signe(ville="Cubatão")).json()["au_dessus_seuil"]
print("   Cubatão, au-dessus du seuil :", g)
verifier("Groupe de moins de 3 jours", "SUPPRIME_GROUPE_TROP_PETIT", g["statut"])

print("\n--- Bruit et budget (epsilon = 1) ---")
# Le budget est maintenant persistant : on le remet à zéro pour pouvoir relancer les tests.
with closing(sqlite3.connect(DB_HOPITAL)) as conn:
    with conn:
        conn.execute("DELETE FROM budget_confidentialite WHERE consumer_id = ?", (DEMANDE["consumer_id"],))
corps = {**paquet_signe(), "apply_dp": True, "epsilon": 1.0}
moyennes = []
for i in range(1, 4):
    r = calculer(corps)
    verifier(f"Appel {i} avec bruit", 200, r.status_code)
    moyennes.append(r.json()["au_dessus_seuil"]["moyenne"])
print("   Moyennes bruitées au-dessus du seuil :", moyennes)
verifier("Moyennes différentes à chaque appel", True, len(set(moyennes)) > 1)
verifier("Budget épuisé (4e appel)", 429, calculer(corps).status_code)
verifier_budget_epuise("Budget épuisé avec un nouveau contrat")

bilan()
