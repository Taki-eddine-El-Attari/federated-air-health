"""TP 1 - Création des deux bases SQLite indépendantes (État de São Paulo, 2015-2025).

Source : Arcoverde & Maciel (2026), Zenodo, doi:10.5281/zenodo.23164494 (CC BY 4.0).
Seul le panel agrégé commune-jour est utilisé, jamais les fichiers par patient.
"""
from contextlib import closing
from pathlib import Path
import sqlite3

import pyarrow.compute as pc
import pyarrow.parquet as pq

DOSSIER = Path(__file__).resolve().parent
DOSSIER_PANELS = DOSSIER.parent / "donnees_sao_paulo" / "panels"
DB_AIR = DOSSIER / "environnement.db"
DB_HOPITAL = DOSSIER / "hopital.db"

# hospitalizations_J = diagnostic principal J00-J99 (appareil respiratoire).
COLONNES = ["day", "NM_MUN", "MP2.5_mean", "hospitalizations_J"]

panels = sorted(DOSSIER_PANELS.glob("municipality_day_panel_*.parquet"))
if not panels:
    raise SystemExit(f"Aucun panel trouvé dans {DOSSIER_PANELS}")

lignes_attendues_air = 0
lignes_attendues_hopital = 0
admissions_attendues = 0

# closing() ferme réellement la connexion (verrouillage de fichier sous Windows).
with closing(sqlite3.connect(DB_AIR)) as db_air, closing(sqlite3.connect(DB_HOPITAL)) as db_hopital:
    with db_air, db_hopital:
        db_air.execute("""
            CREATE TABLE IF NOT EXISTS qualite_air (
                date TEXT NOT NULL,
                ville TEXT NOT NULL,
                pm25 REAL NOT NULL,
                PRIMARY KEY (ville, date)
            )
        """)
        db_air.execute("DELETE FROM qualite_air")
        db_hopital.execute("""
            CREATE TABLE IF NOT EXISTS admissions (
                date TEXT NOT NULL,
                ville TEXT NOT NULL,
                nombre INTEGER NOT NULL CHECK(nombre >= 0),
                PRIMARY KEY (ville, date)
            )
        """)
        db_hopital.execute("DELETE FROM admissions")

        for fichier in panels:
            table = pq.read_table(fichier, columns=COLONNES)
            dates = pc.strftime(table["day"], "%Y-%m-%d").to_pylist()
            villes = table["NM_MUN"].to_pylist()
            pm25 = table["MP2.5_mean"].to_pylist()
            nombres = table["hospitalizations_J"].to_pylist()

            # Organisation A : seulement les communes-jours mesurés.
            db_air.executemany(
                "INSERT INTO qualite_air VALUES (?, ?, ?)",
                [(d, v, p) for d, v, p in zip(dates, villes, pm25) if p is not None],
            )
            # Organisation B : toutes les communes-jours, y compris à 0 admission.
            db_hopital.executemany(
                "INSERT INTO admissions VALUES (?, ?, ?)",
                list(zip(dates, villes, nombres)),
            )
            lignes_attendues_air += sum(p is not None for p in pm25)
            lignes_attendues_hopital += table.num_rows
            admissions_attendues += sum(nombres)

    # Contrôle : les bases contiennent exactement ce que les panels annoncent.
    assert db_air.execute("SELECT COUNT(*) FROM qualite_air").fetchone()[0] == lignes_attendues_air
    assert db_hopital.execute("SELECT COUNT(*), SUM(nombre) FROM admissions").fetchone() == (
        lignes_attendues_hopital,
        admissions_attendues,
    )

print(f"Deux bases locales ont été créées : {lignes_attendues_air} mesures, "
      f"{lignes_attendues_hopital} lignes d'admissions.")
