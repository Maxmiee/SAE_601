#python -m streamlit run data_viz\main.py
#mdp git : MathisRomain69
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px


DB_PATH = "./data_transformation/database.sqlite"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    decklists = pd.read_sql("SELECT * FROM wrk_decklists", conn)
    pokemon = pd.read_sql("SELECT name, extension FROM pokemon_cards", conn)
    matchs = pd.read_sql("SELECT player1, player2, winner FROM matchs", conn)
    conn.close()
    
    return decklists, pokemon, matchs




def main():
    # Configuration de la page
    st.set_page_config(page_title="Pokémon", layout="wide")

    # En-tête principal
    st.title("🎈 Analyse des decks pokémon")
    

    # Barre latérale
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Aller à", ["Accueil", "Analyse"])

    # Corps principal
    if page == "Accueil":
        st.header("🏠 Accueil")
        st.write("Voici la page d'accueil. Ajoutez ici un résumé ou des statistiques clés.")
        
    elif page == "Analyse":
        st.header("📊 Analyse")
    
            
    

    # Pied de page
    st.markdown("---")
    st.markdown("© 2025 - Votre Nom")

# Exécution du main
if __name__ == "__main__":
    main()

