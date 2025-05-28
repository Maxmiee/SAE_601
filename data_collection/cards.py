import requests
from bs4 import BeautifulSoup
import re
import sqlite3
import pandas as pd

DB_PATH = "./data_transformation/database.sqlite"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    liens = pd.read_sql_query("SELECT DISTINCT card_url, card_type FROM wrk_decklists;", conn)
    conn.close()
    filtered = liens[liens['card_type'].str.lower() == 'pokémon']
    return filtered["card_url"].tolist()  # liste des URLs

def create_table(conn):
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
            url TEXT UNIQUE
        )
    ''')
    conn.commit()

def insert_card(conn, card_data):
    conn.execute('''
        INSERT OR IGNORE INTO pokemon_cards 
        (name, type, hp, stage, evolves_from, weakness, retreat, url) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        card_data["name"],
        card_data["type"],
        int(card_data["hp"]) if card_data["hp"] and card_data["hp"].isdigit() else None,
        card_data["stage"],
        card_data["evolves_from"],
        card_data["weakness"],
        card_data["retreat"],
        card_data["url"]
    ))
    conn.commit()

def main():
    urls = load_data()
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    for url in urls:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            title_block = soup.find("p", class_="card-text-title")
            stage_block = soup.find("p", class_="card-text-type")
            wrr_block = soup.find("p", class_="card-text-wrr")

            if title_block:
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

                card_data = {
                    "name": name,
                    "type": type_,
                    "hp": hp,
                    "stage": stage,
                    "evolves_from": evolves_from,
                    "weakness": weakness,
                    "retreat": retreat,
                    "url": url
                }

                insert_card(conn, card_data)
                print(f"Inséré : {name}")

    conn.close()

if __name__ == "__main__":
    main()