import sqlite3
import os

sqlite_db_path = "database.sqlite"
print("Chemin absolu DB :", os.path.abspath(sqlite_db_path))

# Création de la table (si pas déjà fait)
create_table_sql = """
DROP TABLE IF EXISTS wrk_tournaments;
CREATE TABLE wrk_tournaments (
  tournament_id TEXT NULL,
  tournament_name TEXT NULL,
  tournament_date TEXT NULL,
  tournament_organizer TEXT NULL,
  tournament_format TEXT NULL,
  tournament_nb_players INTEGER NULL
);
"""

with sqlite3.connect(sqlite_db_path) as conn:
    cur = conn.cursor()
    cur.executescript(create_table_sql)
    conn.commit()

    # Insertion test
    cur.execute(
        "INSERT INTO wrk_tournaments VALUES (?, ?, ?, ?, ?, ?)",
        ("t1", "Tournoi Test", "2025-05-23T00:00:00", "Organisateur X", "Format Y", 42)
    )
    conn.commit()

    # Vérification
    cur.execute("SELECT * FROM wrk_tournaments")
    rows = cur.fetchall()
    print("Contenu de wrk_tournaments :")
    for row in rows:
        print(row)
