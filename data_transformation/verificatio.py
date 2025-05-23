import sqlite3
import os

sqlite_db_path = "data_transformation/database.sqlite"
print("Chemin absolu DB :", os.path.abspath(sqlite_db_path))


with sqlite3.connect(sqlite_db_path) as conn:
    cur = conn.cursor()
    # Vérification
    cur.execute("SELECT * FROM wrk_tournaments")
    rows = cur.fetchall()
    print("Contenu de wrk_tournaments :")
    for row in rows:
        print(row)
    conn.commit()


with sqlite3.connect(sqlite_db_path) as conn:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wrk_tournaments'")
    exists = cur.fetchone()
    print("Table wrk_tournaments existe ?", bool(exists))

    # Affiche la structure de la table
    cur.execute("PRAGMA table_info(wrk_tournaments)")
    print("Structure de la table:")
    for col in cur.fetchall():
        print(col)