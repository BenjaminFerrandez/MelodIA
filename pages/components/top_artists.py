import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from top_artists import analyze_top_artists, TopArtistsAnalyzer


def show():
    st.title("Vos Artistes les Plus Écoutés")

    # Vérifier si l'analyse a déjà été effectuée
    if 'top_artists_data' not in st.session_state:
        st.session_state.top_artists_data = None

    # Bouton pour effectuer l'analyse
    if st.session_state.top_artists_data is None:
        st.info(
            "Cette analyse se connecte à Spotify pour récupérer vos artistes les plus écoutés. Ces données ne sont pas incluses dans l'extraction initiale des playlists.")

        if st.button("Analyser mes artistes les plus écoutés", type="primary"):
            with st.spinner("Connexion à Spotify et analyse de vos habitudes d'écoute..."):
                try:
                    results = analyze_top_artists()

                    if results:
                        st.session_state.top_artists_data = results
                        st.success("Analyse terminée avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Erreur lors de l'analyse. Veuillez réessayer.")
                except Exception as e:
                    st.error(f"Une erreur s'est produite: {str(e)}")

        # Expliquer ce que fait cette fonctionnalité
        st.markdown("""
        ### À propos de cette fonctionnalité

        Cette analyse vous permet de voir:

        - Vos artistes les plus écoutés sur différentes périodes
        - L'évolution de vos goûts musicaux
        - Les genres dominants dans votre écoute
        - Créer des playlists personnalisées basées sur vos artistes préférés

        Les données sont récupérées directement depuis Spotify et représentent vos véritables habitudes d'écoute, indépendamment des playlists que vous avez créées.
        """)

        return

    # Si l'analyse a été effectuée, afficher les résultats
    data = st.session_state.top_artists_data

    # Créer des onglets pour différentes périodes
    tab1, tab2, tab3 = st.tabs(["4 dernières semaines", "6 derniers mois", "Tous les temps"])

    with tab1:
        show_period_artists(data['short_term'], "des 4 dernières semaines")

    with tab2:
        show_period_artists(data['medium_term'], "des 6 derniers mois")

    with tab3:
        show_period_artists(data['long_term'], "de tous les temps")

    # Analyse des genres
    st.markdown("---")
    show_genre_analysis(data)

    # Option pour créer une playlist
    st.markdown("---")
    st.header("Créer une playlist de vos artistes préférés")

    col1, col2 = st.columns(2)

    with col1:
        time_range = st.selectbox(
            "Période",
            options=["short_term", "medium_term", "long_term"],
            format_func=lambda x: {
                "short_term": "4 dernières semaines",
                "medium_term": "6 derniers mois",
                "long_term": "Tous les temps"
            }.get(x)
        )

    with col2:
        tracks_per_artist = st.slider("Titres par artiste", min_value=1, max_value=5, value=2)
        total_limit = st.slider("Nombre total de titres", min_value=10, max_value=50, value=30)

    if st.button("Créer une playlist", type="primary"):
        with st.spinner("Création de la playlist en cours..."):
            try:
                analyzer = TopArtistsAnalyzer()
                playlist = analyzer.create_top_artists_playlist(
                    time_range=time_range,
                    tracks_per_artist=tracks_per_artist,
                    total_limit=total_limit
                )

                if playlist:
                    st.success(f"Playlist '{playlist['name']}' créée avec succès!")

                    # Afficher les détails de la playlist
                    st.markdown(f"""
                    ### Détails de la playlist

                    - **Nom**: {playlist['name']}
                    - **Nombre de titres**: {playlist['tracks_count']}
                    """)

                    # Bouton pour ouvrir la playlist dans Spotify
                    st.markdown(f"[Ouvrir dans Spotify]({playlist['url']})")
                else:
                    st.error("Erreur lors de la création de la playlist.")
            except Exception as e:
                st.error(f"Une erreur s'est produite: {str(e)}")

    # Bouton pour réinitialiser l'analyse
    st.markdown("---")
    if st.button("Actualiser l'analyse des artistes", type="secondary"):
        st.session_state.top_artists_data = None
        st.experimental_rerun()


def show_period_artists(artists_data, period_name):
    """Affiche les artistes les plus écoutés pour une période donnée"""
    st.header(f"Top artistes {period_name}")

    if not artists_data:
        st.warning(f"Aucune donnée disponible pour cette période")
        return

    # Créer un DataFrame pour faciliter la visualisation
    artists_df = pd.DataFrame(artists_data)

    # Ajuster pour l'affichage
    artists_df = artists_df[['position', 'name', 'popularity', 'genres']]

    # Transformer la liste des genres en chaîne de caractères
    artists_df['genres'] = artists_df['genres'].apply(
        lambda x: ", ".join(x[:3]) if x else "Non spécifié"
    )

    # Créer un graphique pour les artistes
    fig = px.bar(
        artists_df,
        x='popularity',
        y='name',
        color='popularity',
        orientation='h',
        color_continuous_scale=px.colors.sequential.Viridis,
        labels={'popularity': 'Popularité', 'name': 'Artiste'},
        title=f"Top artistes {period_name}"
    )

    fig.update_layout(yaxis={'categoryorder': 'trace'})
    st.plotly_chart(fig, use_container_width=True)

    # Afficher le tableau des artistes
    artists_df.columns = ['Position', 'Artiste', 'Popularité', 'Genres principaux']
    st.dataframe(artists_df, use_container_width=True)


def show_genre_analysis(data):
    """Affiche l'analyse des genres musicaux"""
    st.header("Analyse des genres musicaux")

    # Extraction et comptage des genres
    all_genres = {}

    for period, artists in data.items():
        period_genres = {}

        for artist in artists:
            for genre in artist.get('genres', []):
                if genre:
                    if genre in period_genres:
                        period_genres[genre] += 1
                    else:
                        period_genres[genre] = 1

        # Garder les 20 genres les plus populaires pour chaque période
        all_genres[period] = {k: v for k, v in sorted(
            period_genres.items(), key=lambda item: item[1], reverse=True
        )[:20]}

    # Créer un sélecteur de période pour les genres
    period_names = {
        "short_term": "4 dernières semaines",
        "medium_term": "6 derniers mois",
        "long_term": "Tous les temps"
    }

    selected_period = st.selectbox(
        "Choisissez une période pour l'analyse des genres",
        options=list(period_names.keys()),
        format_func=lambda x: period_names[x]
    )

    if selected_period in all_genres and all_genres[selected_period]:
        genres = all_genres[selected_period]

        # Créer un DataFrame pour la visualisation
        genres_df = pd.DataFrame({'Genre': list(genres.keys()), 'Nombre': list(genres.values())})

        # Créer un graphique pour les genres
        fig = px.bar(
            genres_df,
            x='Nombre',
            y='Genre',
            color='Nombre',
            orientation='h',
            color_continuous_scale=px.colors.sequential.Viridis,
            title=f"Genres musicaux dominants ({period_names[selected_period]})"
        )

        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

        # Nuage de mots pour les genres (si la bibliothèque est installée)
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            st.subheader(f"Nuage de genres ({period_names[selected_period]})")

            # Génération du nuage de mots
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='black',
                colormap='viridis',
                max_words=100
            ).generate_from_frequencies(genres)

            # Affichage
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        except ImportError:
            st.info("La bibliothèque WordCloud n'est pas installée. Le nuage de genres n'est pas disponible.")
    else:
        st.warning(f"Aucun genre musical trouvé pour la période sélectionnée")