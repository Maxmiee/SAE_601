import sqlite3
import pandas as pd
from bs4 import BeautifulSoup
import requests

DB_PATH = "./data_transformation/database.sqlite"
BASE_URL =  "https://play.limitlesstcg.com"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    tournaments = pd.read_sql_query("SELECT DISTINCT tournament_id FROM wrk_tournaments;", conn)
    conn.close()
    return tournaments["tournament_id"].tolist()

def construct_pairings_url(tournament_id: str, round_number: int):
    return f"{BASE_URL}/tournament/{tournament_id}/pairings?round={round_number}"

def create_table(conn):
    conn.execute('DROP TABLE IF EXISTS players')
    conn.execute('''
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT UNIQUE,
            tournament_id TEXT,
            round_number INTEGER,
            name TEXT,
            wins INTEGER,
            losses INTEGER,
            ties INTEGER
        )
    ''')
    conn.commit()

def insert_or_update_player(conn, player):
    
    sql = '''
    INSERT INTO players (player_id, tournament_id, round_number, name, wins, losses, ties)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(player_id) DO UPDATE SET
        tournament_id=excluded.tournament_id,
        round_number=excluded.round_number,
        name=excluded.name,
        wins=excluded.wins,
        losses=excluded.losses,
        ties=excluded.ties
    WHERE excluded.round_number > players.round_number
    '''
    conn.execute(sql, (
        player['player_id'],
        player['tournament_id'],
        player['round_number'],
        player['name'],
        player['wins'],
        player['losses'],
        player['ties']
    ))
    conn.commit()

def parse_players(html, tournament_id, round_number):
    soup = BeautifulSoup(html, 'html.parser')
    players = []

    for td in soup.find_all('td', class_='player'):
        player_id = td['data-id']
        wins = int(td['data-wins'])
        losses = int(td['data-losses'])
        ties = int(td['data-ties'])
        name = td.find('div', class_='name').text.strip()

        players.append({
            'player_id': player_id,
            'tournament_id': tournament_id,
            'round_number': round_number,
            'name': name,
            'wins': wins,
            'losses': losses,
            'ties': ties
        })
    return players

def main():
    tournament_ids = load_data()
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    for tournament_id in tournament_ids:
        round_number = 1
        while True:
            url = construct_pairings_url(tournament_id, round_number)
            print(f"Récupération des données depuis : {url}")
            response = requests.get(url)
            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code} pour {url}, arrêt du scraping pour ce tournoi.")
                break

            players = parse_players(response.text, tournament_id, round_number)
            if not players:
                print(f"Aucun joueur trouvé au round {round_number} du tournoi {tournament_id}, fin des rounds.")
                break

            for player in players:
                insert_or_update_player(conn, player)
                print(f"Inséré/MAJ joueur : {player['name']} (Round {round_number}) W:{player['wins']} L:{player['losses']} T:{player['ties']})")

            round_number += 1

    conn.close()

if __name__ == "__main__":
    main()
