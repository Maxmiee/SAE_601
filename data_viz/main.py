#python -m streamlit run data_viz\main.py
#mdp git : MathisRomain69
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

DB_PATH = "./data_transformation/database.sqlite"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    decklists = pd.read_sql("SELECT * FROM wrk_decklists", conn)
    pokemon = pd.read_sql("SELECT * FROM pokemon_cards", conn)
    matchs = pd.read_sql("SELECT * FROM matchs", conn)
    result_tournoi = pd.read_sql("SELECT * FROM resultats_tournoi", conn)
    conn.close()
    
    return decklists, pokemon, matchs, result_tournoi

decklists, pokemon, matchs, result_tournoi = load_data()


extensions = pokemon['extension'].dropna().unique()


tensions = pokemon['extension'].dropna().unique()

def main():
    
    

    st.set_page_config(page_title="Pokémon", layout="wide")

    st.title("Analyse des decks pokémon")
    st.header("Analyse")

    st.title("Scatter plot des decks par extension et winrate")

    
    df_deck = result_tournoi.dropna(subset=['winrate', 'extension', 'deck'])

    col_filters, col_graph  = st.columns([1, 3])
    with col_filters:
        extensions = sorted(df_deck['extension'].unique())
        extensions_choisies = st.multiselect(
        "Sélectionner une ou plusieurs extensions :",
        options=extensions,
        default=extensions
        
        )
        min_matchs = st.slider("Nombre minimum de matchs pour un deck", 0, 50, 5)
    
    df_filtré = df_deck[df_deck['extension'].isin(extensions_choisies)]
    df_filtré = df_filtré[df_filtré['nb_match'] >= min_matchs]

    df_grouped = df_filtré.groupby(['deck', 'extension']).agg({
        'winrate': 'mean',
        'nb_match': 'sum', 
    }).reset_index()

    palette = [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
        "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
    ]
    color_map = {ext: palette[i % len(palette)] for i, ext in enumerate(df_grouped['extension'].unique())}
    df_grouped['color'] = df_grouped['extension'].map(color_map)

    
    sizes = np.log10(df_grouped['nb_match'] + 1)
    max_size = 30
    sizeref = 2.*sizes.max()/(max_size**1.8)

   
    fig = go.Figure()
   
    extensions_choisies = sorted(df_grouped['extension'].unique())
    for deck_name, group in df_grouped.groupby('deck'):
       
        group = group.sort_values(
            by='extension',
            key=lambda x: x.map({ext: i for i, ext in enumerate(extensions_choisies)})
        )
        if len(group) > 1:
            fig.add_trace(go.Scatter(
                x=group['extension'],
                y=group['winrate'],
                mode='lines',
                line=dict(width=1),
                showlegend=False,
                hoverinfo='skip'
            ))

   
    fig.add_trace(go.Scatter(
        x=df_grouped['extension'],
        y=df_grouped['winrate'],
        mode='markers',
        marker=dict(
            size=sizes,
            color=df_grouped['color'],
            line=dict(width=1, color='DarkSlateGrey'),
            sizemode='area',
            sizeref=sizeref,
            sizemin=4
        ),
        text=df_grouped['deck'],
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Extension: %{x}<br>" +
            "Winrate: %{y:.2%}<br>" +
            "Nb matchs: %{customdata}<extra></extra>"
        ),
        customdata=df_grouped['nb_match']
    ))

    
    fig.update_layout(
        title="Winrate des decks par extension",
        xaxis_title="Extension",
        yaxis_title="Win Rate",
        yaxis=dict(range=[0, 1]),
        xaxis=dict(categoryorder='array', categoryarray=extensions_choisies),
        showlegend=False
    )
    with col_graph:
        st.plotly_chart(fig, use_container_width=True)
    
    
    
    ########################################################################################################################################

    col_filters_1, col_graph_1  = st.columns([1, 3])
    with col_filters_1:
        top_n = st.slider("Top ? ", 0, 50, 5)
    
    df_cartes = decklists.merge(
        pokemon[['url', 'extension', 'name']],
        left_on='card_url',
        right_on='url',
        how='left'
    )

    df_cartes_filtré = df_cartes[df_cartes['extension'].isin(extensions_choisies)]

    
    df_cartes_agg = df_cartes_filtré.groupby(['extension', 'name'], as_index=False)['card_count'].sum()

    
    total_par_extension = df_cartes_agg.groupby('extension')['card_count'].transform('sum')

    
    df_cartes_agg['pct_usage'] = df_cartes_agg['card_count'] / total_par_extension
    df_cartes_agg['pct_usage'] = df_cartes_agg['pct_usage'].round(3)
    

    # 1. Grouper par extension et carte, sommer card_count
    grouped = df_cartes_agg.groupby(['extension', 'name'])['pct_usage'].sum().reset_index()

    # 2. Pour chaque extension, récupérer les top N cartes les plus jouées
    top_per_extension = (
        grouped.sort_values(['extension', 'pct_usage'], ascending=[True, False])
        .groupby('extension')
        .head(top_n)
    )
    print(grouped)
    # 3. Utiliser ce DataFrame filtré pour tracer le graphique
    fig2 = px.bar(
        top_per_extension,
        x='extension',
        y='pct_usage',  # ou 'pct_usage' si tu préfères
        color='name',
        labels={
            'extension': 'Extension',
            'pct_usage': '% usage',
        },
        title=f"Top {top_n} cartes les plus jouées par extension"
    )
   

    fig2.update_layout(
        yaxis_tickformat='%',
        xaxis={'categoryorder': 'category ascending'},
        showlegend=False
    )
    with col_graph_1:
        st.plotly_chart(fig2, use_container_width=True)

if __name__ == "__main__":
    main()
