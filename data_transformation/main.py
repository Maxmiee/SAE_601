import sqlite3
import os
import json
from datetime import datetime

# Chemin vers la base SQLite
script_dir = os.path.dirname(os.path.abspath(__file__))

# Chemin absolu vers le fichier SQL
sql_file_path = os.path.join(script_dir, "00_create_wrk_tables.sql")

# Chemin vers la base SQLite (même dossier que le script)
sqlite_db_path = os.path.join(script_dir, "database.sqlite")

output_directory = "./data_collection/sample_output"

def execute_sql_script(path: str):
    with sqlite3.connect(sqlite_db_path) as conn:
        cur = conn.cursor()
        with open(path) as f:
            sql = f.read()
            cur.executescript(sql)
        conn.commit()

def insert_wrk_tournaments():
    tournament_data = []
    for file in os.listdir(output_directory):
        with open(os.path.join(output_directory, file)) as f:
            tournament = json.load(f)
            # Convertir la date au format ISO
            date_str = datetime.strptime(tournament['date'], '%Y-%m-%dT%H:%M:%S.000Z').isoformat()
            tournament_data.append((
                tournament['id'], 
                tournament['name'], 
                date_str,
                tournament['organizer'], 
                tournament['format'], 
                int(tournament['nb_players'])
            ))
    
    print(tournament_data)
    with sqlite3.connect(sqlite_db_path) as conn:
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO wrk_tournaments VALUES (?, ?, ?, ?, ?, ?)", 
            tournament_data
        )
        conn.commit()

def insert_wrk_decklists():
    decklist_data = []
    for file in os.listdir(output_directory):
        with open(os.path.join(output_directory, file)) as f:
            tournament = json.load(f)
            print(tournament.keys())
            tournament_id = tournament['id']
            for player in tournament['players']:
                player_id = player['id']
                for card in player['decklist']:
                    decklist_data.append((
                        tournament_id,
                        player_id,
                        card['type'],
                        card['name'],
                        card['url'],
                        int(card['count']),
                    ))
                   
    with sqlite3.connect(sqlite_db_path) as conn:
        
        cur = conn.cursor()
        cur.executemany(
            "INSERT INTO wrk_decklists VALUES (?, ?, ?, ?, ?, ?)", 
            decklist_data
        )
        conn.commit()

print("creating work tables")
execute_sql_script(sql_file_path)

print("insert raw tournament data")
insert_wrk_tournaments()

print("insert raw decklist data")
insert_wrk_decklists()


print("construct card database")
execute_sql_script(sql_file_path)
