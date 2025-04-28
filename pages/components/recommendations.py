import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from config import DATA_DIR

# Importer uniquement get_recommendations, PAS export_playlist_to_csv
from recommendation import get_recommendations


def show():
    st.title("Recommandations Personnalisées")

    # Vérifier si des données catégorisées sont disponibles
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

    if not os.path.exists(categorized_path):
        st.warning(
            "Aucune donnée n'est disponible pour les recommandations. Veuillez d'abord extraire et analyser vos données Spotify.")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Aller à l'extraction", type="primary"):
                st.session_state.page = "extraction"
                st.experimental_rerun()

        with col2:
            if st.button("Aller à l'analyse", type="secondary"):
                st.session_state.page = "analysis"
                st.experimental_rerun()

        return

    try:
        # Charger les données catégorisées
        df = pd.read_csv(categorized_path, low_memory=False)

        if df.empty:
            st.error("Le fichier de données existe mais ne contient aucune donnée valide.")
            return

        # Créer des onglets pour différents types de recommandations
        tab1, tab2, tab3 = st.tabs(["Par titre", "Par ambiance", "Découvertes"])

        with tab1:
            show_similar_tracks_recommendations(df)

        with tab2:
            show_mood_based_recommendations(df)

        with tab3:
            show_discovery_recommendations(df)

    except Exception as e:
        st.error(f"Erreur lors du chargement des recommandations: {str(e)}")


def show_similar_tracks_recommendations(df):
    """Affiche les recommandations basées sur la similarité des titres"""
    st.header("Titres similaires")
    st.markdown("Obtenez des recommandations basées sur un titre que vous aimez")

    # Créer une liste de titres pour la sélection
    # Ajouter l'artiste pour faciliter la recherche
    track_options = [f"{row['track_name']} - {row['artist_name']}" for _, row in
                     df.sample(min(1000, len(df))).iterrows()]

    # Ajouter une option de recherche
    search_query = st.text_input("Rechercher un titre ou un artiste")

    if search_query:
        # Filtrer les options en fonction de la recherche
        filtered_options = [opt for opt in track_options if search_query.lower() in opt.lower()]

        if filtered_options:
            track_options = filtered_options
        else:
            st.info(f"Aucun titre ne correspond à '{search_query}'")

    # Sélectionner un titre
    selected_track = st.selectbox("Choisissez un titre", options=track_options)

    if selected_track:
        # Extraire le nom du titre et de l'artiste
        track_name, artist_name = selected_track.split(" - ", 1)

        # Trouver l'ID du titre
        track_row = df[(df['track_name'] == track_name) & (df['artist_name'] == artist_name)]

        if not track_row.empty:
            track_id = track_row.iloc[0]['track_id']

            # Afficher les caractéristiques du titre sélectionné
            audio_features = ['danceability', 'energy', 'valence', 'acousticness']
            missing_features = [f for f in audio_features if f not in track_row.columns]

            if not missing_features:
                st.subheader("Caractéristiques du titre sélectionné")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Dansabilité", f"{track_row.iloc[0]['danceability']:.2f}")

                with col2:
                    st.metric("Énergie", f"{track_row.iloc[0]['energy']:.2f}")

                with col3:
                    st.metric("Positivité", f"{track_row.iloc[0]['valence']:.2f}")

                with col4:
                    st.metric("Acoustique", f"{track_row.iloc[0]['acousticness']:.2f}")

            # Obtenir les recommandations
            if st.button("Obtenir des recommandations", type="primary"):
                with st.spinner("Recherche de titres similaires..."):
                    similar_tracks = get_recommendations(track_id=track_id, size=10)

                    if similar_tracks is not None and not similar_tracks.empty:
                        st.success(f"Voici des titres similaires à {track_name} par {artist_name}")

                        # Créer un tableau pour afficher les résultats
                        results_df = similar_tracks[['track_name', 'artist_name', 'similarity_score']]
                        results_df['similarity_score'] = results_df['similarity_score'].apply(lambda x: f"{x:.2f}")
                        results_df.columns = ['Titre', 'Artiste', 'Score de similarité']

                        st.dataframe(results_df, use_container_width=True)

                        # Visualisation de la similarité
                        if 'similarity_score' in similar_tracks.columns:
                            st.subheader("Scores de similarité")

                            fig = px.bar(
                                similar_tracks,
                                x='similarity_score',
                                y='track_name',
                                orientation='h',
                                labels={'similarity_score': 'Score de similarité', 'track_name': 'Titre'},
                                title="Classement par similarité",
                                color='similarity_score',
                                color_continuous_scale=px.colors.sequential.Viridis
                            )

                            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                            st.plotly_chart(fig, use_container_width=True)

                            # Option pour créer une playlist Spotify
                            if st.button("Créer une playlist Spotify avec ces titres", type="secondary"):
                                st.warning("Fonctionnalité de création de playlist en cours de développement")

                            # Option pour exporter en CSV avec importation différée
                            if st.button("Exporter en CSV", type="secondary"):
                                try:
                                    # Importation différée de export_playlist_to_csv
                                    from spotify_playlist_export import export_playlist_to_csv
                                    export_path = export_playlist_to_csv(
                                        similar_tracks,
                                        f"similar_to_{track_name.replace(' ', '_')}"
                                    )
                                    if export_path:
                                        st.success(f"Playlist exportée: {os.path.basename(export_path)}")
                                except Exception as e:
                                    st.error(f"Erreur lors de l'exportation: {str(e)}")
                    else:
                        st.error("Aucune recommandation n'a pu être générée. Veuillez essayer un autre titre.")


def show_mood_based_recommendations(df):
    """Affiche les recommandations basées sur l'ambiance"""
    st.header("Playlists par ambiance")
    st.markdown("Générez une playlist basée sur une ambiance spécifique")

    # Options d'ambiance
    moods = {
        'happy': 'Joyeuse',
        'energetic': 'Énergique',
        'calm': 'Calme',
        'melancholic': 'Mélancolique'
    }

    col1, col2 = st.columns(2)

    with col1:
        selected_mood = st.selectbox(
            "Choisissez une ambiance",
            options=list(moods.keys()),
            format_func=lambda x: moods[x]
        )

    with col2:
        playlist_size = st.slider("Nombre de titres", min_value=5, max_value=30, value=15, step=5)

    # Ajout d'options avancées pour personnaliser la playlist
    with st.expander("Options avancées"):
        st.markdown("Ajustez les paramètres pour personnaliser votre playlist")

        col1, col2 = st.columns(2)

        with col1:
            min_energy = st.slider("Énergie minimale", min_value=0.0, max_value=1.0, value=0.4, step=0.1)
            min_danceability = st.slider("Dansabilité minimale", min_value=0.0, max_value=1.0, value=0.4, step=0.1)

        with col2:
            min_valence = st.slider("Positivité minimale", min_value=0.0, max_value=1.0, value=0.4, step=0.1)
            max_acousticness = st.slider("Acoustique maximale", min_value=0.0, max_value=1.0, value=0.6, step=0.1)

    if st.button(f"Générer une playlist {moods[selected_mood]}", type="primary"):
        with st.spinner(f"Création d'une playlist {moods[selected_mood]}..."):
            # Obtenir les recommandations
            mood_playlist = get_recommendations(
                mood=selected_mood,
                size=playlist_size,
                min_energy=min_energy,
                min_danceability=min_danceability,
                min_valence=min_valence,
                max_acousticness=max_acousticness
            )

            if mood_playlist is not None and not mood_playlist.empty:
                st.success(f"Voici votre playlist {moods[selected_mood]} avec {len(mood_playlist)} titres")

                # Afficher les résultats
                results_df = mood_playlist[['track_name', 'artist_name']]
                results_df.columns = ['Titre', 'Artiste']

                st.dataframe(results_df, use_container_width=True)

                # Visualisation des caractéristiques de la playlist
                audio_features = ['danceability', 'energy', 'valence', 'acousticness']

                if all(feature in mood_playlist.columns for feature in audio_features):
                    st.subheader("Profil audio de la playlist")

                    # Graphique radar des moyennes des caractéristiques
                    feature_means = mood_playlist[audio_features].mean().reset_index()
                    feature_means.columns = ['Caractéristique', 'Valeur']

                    fig = px.line_polar(
                        feature_means,
                        r='Valeur',
                        theta='Caractéristique',
                        line_close=True,
                        range_r=[0, 1],
                        title=f"Profil audio moyen de la playlist {moods[selected_mood]}"
                    )
                    fig.update_traces(fill='toself')

                    st.plotly_chart(fig, use_container_width=True)

                # Option pour créer une playlist Spotify
                if st.button("Créer cette playlist sur Spotify", type="secondary"):
                    st.warning("Fonctionnalité de création de playlist en cours de développement")

                # Option pour exporter en CSV avec importation différée
                if st.button("Exporter en CSV", type="secondary"):
                    try:
                        # Importation différée de export_playlist_to_csv
                        from spotify_playlist_export import export_playlist_to_csv
                        export_path = export_playlist_to_csv(
                            mood_playlist,
                            f"playlist_{selected_mood}"
                        )
                        if export_path:
                            st.success(f"Playlist exportée: {os.path.basename(export_path)}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'exportation: {str(e)}")
            else:
                st.error("Aucune recommandation n'a pu être générée. Veuillez ajuster les paramètres et réessayer.")


def show_discovery_recommendations(df):
    """Affiche les recommandations pour découvrir de nouveaux titres"""
    st.header("Découvertes musicales")
    st.markdown("Découvrez des titres que vous pourriez aimer mais que vous écoutez peu")

    # Options de découverte
    st.subheader("Options de découverte")

    col1, col2 = st.columns(2)

    with col1:
        discovery_size = st.slider("Nombre de découvertes", min_value=5, max_value=20, value=10, step=5)

    with col2:
        discovery_type = st.radio(
            "Type de découverte",
            options=["Artistes peu écoutés", "Titres populaires que vous ne connaissez pas", "Mélange varié"]
        )

    if st.button("Découvrir de nouveaux titres", type="primary"):
        with st.spinner("Recherche de découvertes musicales..."):
            # Convertir le type de découverte en valeur pour la fonction
            discovery_type_map = {
                "Artistes peu écoutés": "artists",
                "Titres populaires que vous ne connaissez pas": "popular",
                "Mélange varié": "mixed"
            }
            discovery_type_value = discovery_type_map.get(discovery_type, "mixed")

            # Obtenir les recommandations de découvertes
            discoveries = get_recommendations(discover=True, size=discovery_size, discovery_type=discovery_type_value)

            if discoveries is not None and not discoveries.empty:
                st.success(f"Voici {len(discoveries)} découvertes musicales pour vous")

                # Afficher les résultats
                results_df = discoveries[['track_name', 'artist_name']]

                # Ajouter popularité si disponible
                if 'popularity' in discoveries.columns:
                    results_df['popularity'] = discoveries['popularity']
                    results_df.columns = ['Titre', 'Artiste', 'Popularité']
                else:
                    results_df.columns = ['Titre', 'Artiste']

                st.dataframe(results_df, use_container_width=True)

                # Option pour écouter un titre (lien Spotify)
                st.subheader("Écouter ces découvertes")
                st.info(
                    "Pour écouter ces titres, vous pouvez les rechercher directement sur Spotify ou créer une playlist.")

                # Option pour créer une playlist Spotify
                if st.button("Créer une playlist de découvertes sur Spotify", type="secondary"):
                    st.warning("Fonctionnalité de création de playlist en cours de développement")

                # Option pour exporter en CSV avec importation différée
                if st.button("Exporter en CSV", type="secondary"):
                    try:
                        # Importation différée de export_playlist_to_csv
                        from spotify_playlist_export import export_playlist_to_csv
                        export_path = export_playlist_to_csv(
                            discoveries,
                            f"decouvertes_{discovery_type_value}"
                        )
                        if export_path:
                            st.success(f"Playlist exportée: {os.path.basename(export_path)}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'exportation: {str(e)}")
            else:
                st.error("Aucune découverte n'a pu être générée. Veuillez réessayer.")