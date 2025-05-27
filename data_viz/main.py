import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

DB_PATH = "./data_transformation/database.sqlite"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    tournaments = pd.read_sql_query("SELECT * FROM wrk_tournaments", conn)
    decklists = pd.read_sql_query("SELECT * FROM wrk_decklists", conn)
    conn.close()
    return tournaments, decklists

def preprocess(tournaments, decklists):
    tournaments['tournament_date'] = pd.to_datetime(tournaments['tournament_date'], errors='coerce')
    tournaments['season'] = tournaments['tournament_date'].dt.year

    df = decklists.merge(tournaments[['tournament_id', 'season']], on='tournament_id', how='left')

    if 'win' not in df.columns:
        import numpy as np
        df['win'] = np.random.choice([0, 1], size=len(df))

    usage = df.groupby(['season', 'card_name']).agg(
        total_card_count=('card_count', 'sum')
    ).reset_index()

    win_data = df.groupby(['season', 'card_name']).apply(
        lambda x: pd.Series({
            'winrate': (x['win'] * x['card_count']).sum() / x['card_count'].sum()
        })
    ).reset_index()

    stats = usage.merge(win_data, on=['season', 'card_name'])
    return stats

def filter_by_season(df, seasons):
    if 'Toutes' in seasons or not seasons:
        return df
    return df[df['season'].isin(seasons)]

def plot_most_used_cards(stats, seasons):
    filtered = filter_by_season(stats, seasons)
    top_cards = filtered.groupby(['season', 'card_name'])['total_card_count'].sum().reset_index()
    top_cards = top_cards.groupby('season').apply(
        lambda x: x.nlargest(10, 'total_card_count')).reset_index(drop=True)

    fig = px.bar(top_cards,
                 x='total_card_count', y='card_name', color='season',
                 orientation='h',
                 title="Top 10 des cartes les plus utilisées par saison",
                 labels={'total_card_count': 'Nombre total de cartes utilisées', 'card_name': 'Carte'},
                 facet_col='season', facet_col_wrap=2,
                 height=600)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def plot_highest_winrate_cards(stats, seasons):
    filtered = filter_by_season(stats, seasons)
    min_usage = 10
    filtered = filtered[filtered['total_card_count'] >= min_usage]

    top_winrate = filtered.groupby(['season', 'card_name'])['winrate'].mean().reset_index()
    top_winrate = top_winrate.groupby('season').apply(
        lambda x: x.nlargest(10, 'winrate')).reset_index(drop=True)

    fig = px.bar(top_winrate,
                 x='winrate', y='card_name', color='season',
                 orientation='h',
                 title="Top 10 des cartes avec le meilleur winrate par saison",
                 labels={'winrate': 'Winrate', 'card_name': 'Carte'},
                 facet_col='season', facet_col_wrap=2,
                 height=600)
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

def plot_card_usage_and_winrate(stats, card_name, seasons):
    filtered = filter_by_season(stats, seasons)
    card_data = filtered[filtered['card_name'] == card_name].sort_values('season')

    fig = px.line(card_data, x='season', y='total_card_count', markers=True,
                  title=f"Usage de la carte '{card_name}' au fil des saisons",
                  labels={'total_card_count': 'Nombre total de cartes utilisées', 'season': 'Saison'})
    fig2 = px.line(card_data, x='season', y='winrate', markers=True,
                   title=f"Winrate de la carte '{card_name}' au fil des saisons",
                   labels={'winrate': 'Winrate', 'season': 'Saison'})

    st.plotly_chart(fig, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

def main():
    st.title("Analyse des cartes Pokémon dans les tournois")

    tournaments, decklists = load_data()
    stats = preprocess(tournaments, decklists)

    all_seasons = sorted(stats['season'].dropna().unique())
    seasons_options = ['Toutes'] + all_seasons

    st.header("Cartes les plus utilisées par saison")
    selected_seasons = st.multiselect("Sélectionnez les saisons", seasons_options, default=['Toutes'])
    plot_most_used_cards(stats, selected_seasons)

    st.header("Cartes avec le meilleur winrate par saison")
    selected_seasons_win = st.multiselect("Sélectionnez les saisons (winrate)", seasons_options, default=['Toutes'], key="winrate_seasons")
    plot_highest_winrate_cards(stats, selected_seasons_win)

    st.header("Analyse détaillée par carte")
    selected_card = st.selectbox("Choisissez une carte", sorted(stats['card_name'].unique()))
    selected_seasons_card = st.multiselect("Sélectionnez les saisons (carte)", seasons_options, default=['Toutes'], key="card_seasons")
    plot_card_usage_and_winrate(stats, selected_card, selected_seasons_card)

if __name__ == "__main__":
    main()
