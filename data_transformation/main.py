import os
import json
import sqlite3
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

# === Path Configuration ===

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(script_dir)

# Files SQL
sql_file_path_00 = os.path.join(script_dir, "data_transformation/00_create_wrk_tables.sql")
sql_file_path_01 = os.path.join(script_dir, "data_transformation/01_dwh_cards.sql")

# Base SQLite 
sqlite_db_path = os.path.join(script_dir, "data_transformation/database.sqlite")

# Directory containing tournament JSON files
output_directory = os.path.join(script_dir, "data_collection", "output")


# === Functions for creating and inserting raw data ===

def execute_sql_script(path: str):
    with sqlite3.connect(sqlite_db_path) as conn:
        cur = conn.cursor()
        with open(path, encoding='utf-8') as f:
            sql = f.read()
            cur.executescript(sql)
        conn.commit()


def insert_wrk_tournaments():
    tournament_data = []
    for file in os.listdir(output_directory):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(output_directory, file), encoding='utf-8') as f:
            tournament = json.load(f)
            date_str = datetime.strptime(tournament['date'], '%Y-%m-%dT%H:%M:%S.000Z').isoformat()
            tournament_data.append((
                tournament['id'], 
                tournament['name'], 
                date_str,
                tournament['organizer'], 
                tournament['format'], 
                int(tournament['nb_players'])
            ))

    with sqlite3.connect(sqlite_db_path) as conn:
        cur = conn.cursor()
        for record in tournament_data:
            print(f"Inserting tournament: {record}")
            cur.execute(
                '''INSERT INTO wrk_tournaments
                (tournament_id, tournament_name, tournament_date, tournament_organizer, tournament_format, tournament_nb_players)
                VALUES (?, ?, ?, ?, ?, ?);''', 
                record   
            )
        conn.commit()


def insert_wrk_decklists():
    decklist_data = []
    for file in os.listdir(output_directory):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(output_directory, file), encoding='utf-8') as f:
            tournament = json.load(f)
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
            '''INSERT INTO wrk_decklists
            (tournament_id, player_id, card_type, card_name, card_url, card_count)
            VALUES (?, ?, ?, ?, ?, ?)''',
            decklist_data
        )
        conn.commit()


# === Functions for retrieving and inserting Pokémon cards ===

def load_pokemon_card_urls():
    """
    Loads distinct Pokémon card URLs from the wrk_decklists table.
    """
    conn = sqlite3.connect(sqlite_db_path)
    liens = pd.read_sql_query("SELECT DISTINCT card_url, card_type FROM wrk_decklists;", conn)
    conn.close()
    filtered = liens[liens['card_type'].str.lower() == 'pokémon']
    return filtered["card_url"].tolist()


def create_pokemon_cards_table(conn):
    conn.execute('DROP TABLE IF EXISTS pokemon_cards')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS pokemon_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT,
            hp INTEGER,
            stage TEXT,
            evolves_from TEXT,
            weakness TEXT,
            retreat TEXT,
            url TEXT UNIQUE,
            extension TEXT
        )
    ''')
    conn.commit()


def insert_pokemon_card(conn, card_data):
    conn.execute('''
        INSERT OR IGNORE INTO pokemon_cards 
        (name, type, hp, stage, evolves_from, weakness, retreat, url, extension) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        card_data["name"],
        card_data["type"],
        int(card_data["hp"]) if card_data["hp"] and card_data["hp"].isdigit() else None,
        card_data["stage"],
        card_data["evolves_from"],
        card_data["weakness"],
        card_data["retreat"],
        card_data["url"],
        card_data["extension"]
    ))
    conn.commit()


def fetch_and_insert_pokemon_cards():
    urls = load_pokemon_card_urls()
    conn = sqlite3.connect(sqlite_db_path)
    create_pokemon_cards_table(conn)

    for url in urls:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                title_block = soup.find("p", class_="card-text-title")
                stage_block = soup.find("p", class_="card-text-type")
                wrr_block = soup.find("p", class_="card-text-wrr")

                if not title_block:
                    print(f"Skipping URL (no title block): {url}")
                    continue

                name_tag = title_block.find("a")
                name = name_tag.text.strip() if name_tag else None

                full_text = title_block.get_text(strip=True)
                match = re.search(r"-\s*(\w+)\s*-\s*(\d+)\s*HP", full_text)
                type_ = match.group(1) if match else None
                hp = match.group(2) if match else None

                stage = None
                evolves_from = None
                if stage_block:
                    stage_text = stage_block.get_text(strip=True)
                    if "Basic" in stage_text:
                        stage = "Basic"
                    elif "Stage 1" in stage_text:
                        stage = "Stage 1"
                    elif "Stage 2" in stage_text:
                        stage = "Stage 2"

                    evolve_link = stage_block.find("a")
                    if evolve_link:
                        evolves_from = evolve_link.text.strip()

                weakness = None
                retreat = None
                if wrr_block:
                    wrr_text = wrr_block.get_text(separator="\n").strip()
                    for line in wrr_text.split("\n"):
                        if "Weakness:" in line:
                            weakness = line.split("Weakness:")[1].strip()
                        elif "Retreat:" in line:
                            retreat = line.split("Retreat:")[1].strip()
                
                ext_info  = re.search(r'/cards/([^/]+)/', url)
                card_data = {
                    "name": name,
                    "type": type_,
                    "hp": hp,
                    "stage": stage,
                    "evolves_from": evolves_from,
                    "weakness": weakness,
                    "retreat": retreat,
                    "url": url,
                    "extension" : ext_info.group(1) if ext_info else None

                }

                insert_pokemon_card(conn, card_data)

            else:
                print(f"Error HTTP {response.status_code} pour l'URL : {url}")
        except Exception as e:
            print(f"Error processing URL {url}: {e}")

    conn.close()

def create_matchs_table(conn):
    conn.execute('DROP TABLE IF EXISTS matchs')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS matchs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player1 TEXT,
            score_p1 INTEGER,
            player2 TEXT,
            score_p2 INTEGER,
            winner TEXT,
            tournament_id TEXT
        )
    ''')
    conn.commit()

def insert_match():
    conn = sqlite3.connect(sqlite_db_path)
    create_matchs_table(conn)
    for file in os.listdir(output_directory):
        if not file.endswith(".json"):
            continue
        with open(os.path.join(output_directory, file), encoding='utf-8') as f:
            tournament = json.load(f)
            tournament_id = tournament['id']
            matches = tournament.get("matches", [])
            for match in matches:
                match_results = match.get("match_results", [])
                if len(match_results) >= 2:
                    player1 = match_results[0]
                    player2 = match_results[1]
                    player1_id = player1.get("player_id")
                    player1_score = player1.get("score")
                    player2_id = player2.get("player_id")
                    player2_score = player2.get("score")
                    if player1_score > player2_score :
                        winner = player1_id
                    elif player2_score == player1_score:
                        winner = None 
                    else :
                        winner = player2_id

                    conn.execute('''
                    INSERT OR IGNORE INTO matchs 
                    (player1, score_p1, player2, score_p2, winner, tournament_id) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    player1_id,
                    player1_score,
                    player2_id,
                    player2_score,
                    winner, 
                    tournament_id
                ))
    conn.commit()


# === Create "resultat_tournoi" ===

def create_resultats_tournois():
    conn = sqlite3.connect(sqlite_db_path)
    conn.execute('DROP TABLE IF EXISTS resultats_tournoi')


    sql_query = """
    
    CREATE TABLE resultats_tournoi (
    deck TEXT,
    tournament_id VARCHAR(100),
    nb_match INT,
    nb_victoire INT,
    winrate DECIMAL(5,2),
    ext INT,
    extension VARCHAR(10),
    nb_joueurs INT
);

    INSERT INTO resultats_tournoi
    (deck, tournament_id, nb_match, nb_victoire, winrate, ext, extension, nb_joueurs)
    SELECT 
        r.deck, 
        r.tournament_id, 
        r.nb_match, 
        r.nb_victoire, 
        r.winrate, 
        t.ext, 
        t.extension, 
        r.nb_joueurs
    FROM (
        SELECT 
            a.deck, 
            a.tournament_id, 
            a.nb_match, 
            a.nb_victoire, 
            ROUND((a.nb_victoire * 1.0) / (a.nb_match * 1.0), 2) AS winrate, 
            a.nb_joueurs
        FROM (
            SELECT 
                decks.deck, 
                decks.tournament_id,
                SUM(stats.nb_matchs) AS nb_match,
                SUM(stats.nb_victoires) AS nb_victoire,
                COUNT(*) AS nb_joueurs
            FROM (
                -- Sous-requête : deck par joueur et tournoi, triée manuellement
                SELECT 
                    player_id, 
                    tournament_id,
                    GROUP_CONCAT(card_desc, ', ') AS deck
                FROM (
                    SELECT 
                        d.player_id, 
                        d.tournament_id,
                        d.card_name || ' x' || d.card_count AS card_desc
                    FROM wrk_decklists d
                    ORDER BY d.player_id, d.tournament_id, d.card_name
                ) AS ordered_cards
                GROUP BY player_id, tournament_id
            ) AS decks
            LEFT JOIN (
                -- Statistiques de matchs
                SELECT 
                    joueur, 
                    tournament_id,
                    COUNT(*) AS nb_matchs,
                    SUM(CASE WHEN joueur = winner THEN 1 ELSE 0 END) AS nb_victoires
                FROM (
                    SELECT player1 AS joueur, tournament_id, winner FROM matchs
                    UNION ALL
                    SELECT player2 AS joueur, tournament_id, winner FROM matchs
                ) AS all_players
                GROUP BY joueur, tournament_id
            ) AS stats
            ON decks.player_id = stats.joueur AND decks.tournament_id = stats.tournament_id
            GROUP BY decks.deck, decks.tournament_id
        ) AS a
    ) AS r
    LEFT JOIN (
        -- Extension et niveau de tournoi
        SELECT 
            dk.tournament_id,
            c.extension,
            MAX(
                CASE 
                    WHEN c.extension = 'P-A' THEN 1
                    WHEN c.extension = 'A1' THEN 2
                    WHEN c.extension = 'A1a' THEN 3
                    WHEN c.extension = 'A2' THEN 4
                    WHEN c.extension = 'A2a' THEN 5
                    WHEN c.extension = 'A2b' THEN 6
                    WHEN c.extension = 'A3' THEN 7
                END
            ) AS ext
        FROM wrk_tournaments wt
        LEFT JOIN wrk_decklists dk ON wt.tournament_id = dk.tournament_id
        LEFT JOIN pokemon_cards c ON dk.card_url = c.url
        GROUP BY dk.tournament_id
    ) AS t
    ON r.tournament_id = t.tournament_id;

    """

    # --- Exécution de la requête SQL
    conn.executescript(sql_query)
                        


# === Main ===

def main():
    print("Creation of work tables (wrk)...")
    execute_sql_script(sql_file_path_00)

    print("Inserting raw tournament data...")
    insert_wrk_tournaments()

    print("Inserting raw decklist data...")
    insert_wrk_decklists()

    print("Building the map database (dwh)...")
    execute_sql_script(sql_file_path_01)

    print("Retrieving and inserting Pokémon card data from URLs...")
    fetch_and_insert_pokemon_cards()

    print("Inserting scores")
    insert_match()

    print("Final Table")
    create_resultats_tournois()


if __name__ == "__main__":
    main()
