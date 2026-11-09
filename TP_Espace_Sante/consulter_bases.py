import sqlite3

requetes = [
    ("environnement.db", "qualite_air"),
    ("hopital.db", "admissions"),
]

for fichier, table in requetes:
    print("\nBase :", fichier)
    db = sqlite3.connect(fichier)
    print("Nombre de lignes :", db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    # Aperçu seulement : hopital.db contient 2,6 millions de lignes.
    for ligne in db.execute(f"SELECT * FROM {table} ORDER BY ville, date LIMIT 5"):
        print(ligne)
    db.close()
