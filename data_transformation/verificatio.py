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
