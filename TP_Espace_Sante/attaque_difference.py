import requests

URL_HOPITAL = "http://127.0.0.1:8002"
CLE_HOPITAL = "demo-hopital-456"

# Le laboratoire choisit LUI-MÊME le groupe : un seul jour.
demande = {
    "ville": "São Paulo",
    "classifications": [{"date": "2015-01-01", "categorie": "non_elevee"}],
}

r = requests.post(
    f"{URL_HOPITAL}/analyse-locale",
    headers={"X-API-Key": CLE_HOPITAL},
    json=demande,
    timeout=30,
)
print(r.json())
