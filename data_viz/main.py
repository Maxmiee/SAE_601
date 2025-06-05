#python -m streamlit run data_viz\main.py
import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

DB_PATH = "./data_transformation/database.sqlite"

# Data loading
def load_data():
    conn = sqlite3.connect(DB_PATH)
    decklists = pd.read_sql("SELECT * FROM wrk_decklists", conn)
    pokemon = pd.read_sql("SELECT * FROM pokemon_cards", conn)
    matchs = pd.read_sql("SELECT * FROM matchs", conn)
    result_tournoi = pd.read_sql("SELECT * FROM resultats_tournoi", conn)
    conn.close()
    
    return decklists, pokemon, matchs, result_tournoi

decklists, pokemon, matchs, result_tournoi = load_data()
# Get the extensions
extensions = pokemon['extension'].dropna().unique()

# Define colors
palette = [
        "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
        "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"
    ]


### APPLICATION ###
def main(palette = palette):
    st.set_page_config(page_title="Pokémon", layout="wide")

    st.title("Pokemon decks analysis")

    # SCATTER PLOT : x = Extension, y = Win rate, Size = Match player
    st.subheader("Winrate for each decks for various extension")

    # Clean data 
    df_deck = result_tournoi.dropna(subset=['winrate', 'extension', 'deck'])

    # Create columns
    col_filters, col_graph  = st.columns([1, 3])

    # FILTER : Extension, minimun numbers of matchs
    with col_filters:
        extensions = sorted(df_deck['extension'].unique())
        extensions_choisies = st.multiselect(
        "Select one or more extensions :",
        options=extensions,
        default=extensions
        
        )
        min_matchs = st.slider("Minimal number of match for a deck", 1, 50, 10)
    
    # Filter the dataset
    df_filtered = df_deck[df_deck['extension'].isin(extensions_choisies)]
    df_filtered = df_filtered[df_filtered['nb_match'] >= min_matchs]

    df_grouped = df_filtered.groupby(['deck', 'extension']).agg({
        'winrate': 'mean',
        'nb_match': 'sum', 
    }).reset_index()

    
    color_map = {ext: palette[i % len(palette)] for i, ext in enumerate(df_grouped['extension'].unique())}
    df_grouped['color'] = df_grouped['extension'].map(color_map)

    # Define the size of the dot
    sizes = np.log10(df_grouped['nb_match'] + 1)
    max_size = 30
    sizeref = 2.*sizes.max()/(max_size**1.8)

    # CREATE THE FIGURE
    fig = go.Figure()
   
    extensions_choisies = sorted(df_grouped['extension'].unique())
    for deck_name, group in df_grouped.groupby('deck'):
       
        group = group.sort_values(
            by='extension',
            key=lambda x: x.map({ext: i for i, ext in enumerate(extensions_choisies)})
        )
        if len(group) > 1:
            # Add the lines
            fig.add_trace(go.Scatter(
                x=group['extension'],
                y=group['winrate'],
                mode='lines',
                line=dict(width=1),
                showlegend=False,
                hoverinfo='skip'
            ))

    # Add the dots
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

    # Add title...
    fig.update_layout(
        xaxis_title="Extension",
        yaxis_title="Win Rate",
        yaxis=dict(range=[0, 1]),
        xaxis=dict(categoryorder='array', categoryarray=extensions_choisies),
        showlegend=False
    )

    # ADD THE GRAPHIC ON THE APPLICATION 
    with col_graph:
        st.plotly_chart(fig, use_container_width=True)
    
    
    
    ########################################################################################################################################

    # SCATTER PLOT : x = Extension, y = % usage
    st.subheader("Most played cards by extension")
    
    col_filters_1, col_graph_1  = st.columns([1, 3])

    # FILTER : Choose the number of cards
    with col_filters_1:
        top_n = st.slider("Top de 0 à 20 ", 1, 20, 5)
    
    # Create the dataframe
    df_cartes = decklists.merge(
        pokemon[['url', 'extension', 'name']],
        left_on='card_url',
        right_on='url',
        how='left'
    )

    df__card_filtered = df_cartes[df_cartes['extension'].isin(extensions_choisies)]
    df_cartes_agg = df__card_filtered.groupby(['extension', 'name'], as_index=False)['card_count'].sum()

    
    total_by_extension = df_cartes_agg.groupby('extension')['card_count'].transform('sum')
    df_cartes_agg['pct_usage'] = df_cartes_agg['card_count'] / total_by_extension
    df_cartes_agg['pct_usage'] = df_cartes_agg['pct_usage'].round(3)
    grouped = df_cartes_agg.groupby(['extension', 'name'])['pct_usage'].sum().reset_index()

    top_per_extension = (
        grouped.sort_values(['extension', 'pct_usage'], ascending=[True, False])
        .groupby('extension')
        .head(top_n)
    )
   

    # Add bar
    fig2 = px.bar(
        top_per_extension,
        x='extension',
        y='pct_usage',
        color='name',
        labels={
            'extension': 'Extension',
            'pct_usage': '% usage',
        },
        title=f"Top {top_n} most played cards by extension"
    )
   
    # Add title
    fig2.update_layout(
        yaxis_tickformat='%',
        xaxis={'categoryorder': 'category ascending'},
        showlegend=False
    )
    # ADD THE GRAPHIC ON THE APPLICATION 
    with col_graph_1:
        st.plotly_chart(fig2, use_container_width=True)


### RUN THE APPLICATION
if __name__ == "__main__":
    main()
