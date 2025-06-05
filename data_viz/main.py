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
    #KPI : number of decks played, number of cards
    
    number_of_decks_played = result_tournoi['deck'].nunique()
    number_of_cards = pokemon['name'].nunique()
    number_of_tournaments = decklists['tournament_id'].nunique()
    st.markdown("### KPIs")
    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2, col3,col4,col5 = st.columns(5)
    col1.metric(label="Number of Decks Played", value=number_of_decks_played)
    col2.metric(label="Number of Cards", value=number_of_cards)
    col3.metric(label="Number of Tournaments", value=number_of_tournaments)
    st.markdown("<hr>", unsafe_allow_html=True)

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
        df_filtered_ext = df_deck[df_deck['extension'].isin(extensions_choisies)]
        df_filtered = df_filtered_ext[df_filtered_ext['nb_match'] >= min_matchs]

        df_grouped = df_filtered.groupby(['deck', 'extension']).agg({
            'winrate': 'mean',
            'nb_match': 'sum', 
        }).reset_index()

        df_grouped_ext = df_filtered_ext.groupby(['deck', 'extension']).agg({
            'winrate': 'mean',
            'nb_match': 'sum', 
        }).reset_index()

        total_matches = df_filtered_ext['nb_match'].sum()
        df_filtered_ext = df_grouped_ext[df_grouped_ext['nb_match'] > 0.001 * total_matches]
        df_top_decks = df_filtered_ext.sort_values(by='winrate', ascending=False).head(10)
                

        # TABLE WITH THE BEST DECKS
        df_top_decks = df_top_decks[['deck', 'winrate', 'nb_match', 'extension']]
        fig_table = go.Figure(data=[go.Table(
            columnwidth=[20, 200, 20, 20, 20],
            header=dict(values=['Position', 'Deck', 'Extension', 'Winrate', 'Nb Matchs'],
                        fill_color='lightblue',
                        align='left'),
            cells=dict(values=[
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                df_top_decks['deck'],
                df_top_decks['extension'],  
                (df_top_decks['winrate'] * 100).round(2).astype(str) + '%',  
                df_top_decks['nb_match']
            ],
            fill_color='white',
            align='left'))
        ])
        fig_table.update_layout(
            title={
                'text': "Top 10 Winrate for each most used decks",
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {'size': 20}
            }
        )
    st.plotly_chart(fig_table, use_container_width=True)


    
    color_map = {ext: palette[i % len(palette)] for i, ext in enumerate(df_grouped['extension'].unique())}
    df_grouped['color'] = df_grouped['extension'].map(color_map)

    # Define the size of the dot
    sizes = np.log10(df_grouped['nb_match'] + 1) ** 1.75
    max_size = 30
    sizeref = 2.*sizes.max()/(max_size**1.95)

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
