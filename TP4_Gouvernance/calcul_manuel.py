"""TP 4 - Calcul de référence, fait hors fédération : réservé à la vérification."""
import sqlite3

VILLE = "São Paulo"

db = sqlite3.connect("file:environnement.db?mode=ro", uri=True)
db.execute("ATTACH 'file:hopital.db?mode=ro' AS h")
lignes = db.execute("""
    SELECT a.pm25 > 30, COUNT(*), SUM(b.nombre)
    FROM qualite_air a JOIN h.admissions b USING (ville, date)
    WHERE a.ville = ?
    GROUP BY a.pm25 > 30
""", (VILLE,)).fetchall()
db.close()

moyennes = {}
for au_dessus, n, somme in lignes:
    nom = "Au-dessus du seuil" if au_dessus else "Sous le seuil"
    moyennes[au_dessus] = somme / n
    print(f"{nom} : {somme} / {n} = {somme / n:.2f}")
print(f"Différence : {moyennes[1]:.2f} - {moyennes[0]:.2f} = {moyennes[1] - moyennes[0]:.2f} admissions par jour")
