import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px

DB_PATH = "./data_transformation/database.sqlite"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    tournaments = pd.read_sql_query("SELECT * FROM wrk_tournaments", conn)
    decklists = pd.read_sql_query("SELECT * FROM wrk_decklists", conn)
    pokemon_cards = pd.read_sql_query("SELECT * FROM pokemon_cards", conn)
    print(pokemon_cards["extension"])
    matchs = pd.read_sql_query("SELECT * FROM matchs", conn)
    conn.close()
    return tournaments, decklists, pokemon_cards, matchs

load_data()
