import requests

URL_AIR = "http://127.0.0.1:8001"
URL_HOPITAL = "http://127.0.0.1:8002"
VILLE = "São Paulo"
TAILLE_PAGE = 1000


def tout_recuperer(url):
    resultats = []
    offset = 0
    while True:
        r = requests.get(
            url,
            params={"ville": VILLE, "limit": TAILLE_PAGE, "offset": offset},
            timeout=30,
        )
        r.raise_for_status()
        page = r.json()
        resultats += page
        if len(page) < TAILLE_PAGE:
            return resultats
        offset += TAILLE_PAGE


mesures_air = tout_recuperer(f"{URL_AIR}/mesures")
admissions = tout_recuperer(f"{URL_HOPITAL}/admissions")

air_par_date = {x["date"]: x["pm25"] for x in mesures_air}
hopital_par_date = {x["date"]: x["nombre"] for x in admissions}

elevees = []
non_elevees = []

dates = sorted(air_par_date.keys() & hopital_par_date.keys())
print("Ville :", VILLE, "- jours communs :", len(dates))
print("Date | PM2.5 | Admissions (5 premiers jours)")
for date in dates:
    pm25 = air_par_date[date]
    nombre = hopital_par_date[date]
    if len(elevees) + len(non_elevees) < 5:
        print(date, "|", round(pm25, 2), "|", nombre)
    if pm25 > 30:
        elevees.append(nombre)
    else:
        non_elevees.append(nombre)

print("Jours de pollution élevée :", len(elevees), "- autres jours :", len(non_elevees))
print("Moyenne admissions, pollution élevée :",
      round(sum(elevees) / len(elevees), 2))
print("Moyenne admissions, autres jours :",
      round(sum(non_elevees) / len(non_elevees), 2))
