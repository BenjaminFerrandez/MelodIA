import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import plotly.express as px
import plotly.graph_objects as go
import sys
from config import DATA_DIR


# Ne PAS importer directement analyze_data depuis data_analysis ici
# Nous utiliserons une importation différée pour éviter la circularité


def show():
    st.title("Analyse de votre Bibliothèque Musicale")

    # Vérifier si des données nettoyées sont disponibles
    cleaned_path = os.path.join(DATA_DIR, "cleaned_tracks.csv")

    if not os.path.exists(cleaned_path):
        st.warning("Aucune donnée n'est disponible pour l'analyse. Veuillez d'abord extraire vos données Spotify.")

        if st.button("Aller à la page d'extraction", type="primary"):
            st.session_state.page = "extraction"
            st.experimental_rerun()
        return

    try:
        # Charger les données nettoyées avec une gestion d'erreur améliorée
        try:
            df = pd.read_csv(cleaned_path, low_memory=False)
            if df.empty:
                st.error("Le fichier de données existe mais ne contient aucune donnée valide.")
                if st.button("Retourner à l'extraction", type="primary"):
                    st.session_state.page = "extraction"
                    st.experimental_rerun()
                return
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {str(e)}")
            st.info("Tentative de réparation du fichier de données...")

            # Tenter de réparer en forçant une nouvelle analyse
            if st.button("Réparer les données", type="primary"):
                # Limiter la récursion pour éviter l'erreur
                current_limit = sys.getrecursionlimit()
                sys.setrecursionlimit(2000)  # Valeur sécuritaire

                with st.spinner("Réparation en cours..."):
                    try:
                        # Renommer l'ancien fichier s'il existe
                        if os.path.exists(cleaned_path):
                            os.rename(cleaned_path, cleaned_path + ".bak")

                        # Forcer une nouvelle analyse - IMPORTATION DIFFÉRÉE
                        from data_analysis import analyze_data
                        stats, audio_analysis, categorized_df = analyze_data(max_recursion_depth=2000)

                        # Restaurer la limite de récursion
                        sys.setrecursionlimit(current_limit)

                        if categorized_df is not None:
                            st.success("Réparation réussie!")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la réparation. Essayez de réextraire vos données.")
                    except Exception as repair_error:
                        sys.setrecursionlimit(current_limit)
                        st.error(f"Erreur pendant la réparation: {str(repair_error)}")
            return

        # Vérifier si une analyse a déjà été effectuée
        categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

        if not os.path.exists(categorized_path):
            st.info("Analyse des données en cours...")

            with st.spinner("Analyse en cours..."):
                try:
                    # Limiter la récursion pour éviter l'erreur
                    current_limit = sys.getrecursionlimit()
                    sys.setrecursionlimit(2000)  # Valeur sécuritaire

                    # Exécuter l'analyse avec une limite de récursion - IMPORTATION DIFFÉRÉE
                    from data_analysis import analyze_data
                    stats, audio_analysis, categorized_df = analyze_data(max_recursion_depth=2000)

                    # Restaurer la limite de récursion
                    sys.setrecursionlimit(current_limit)

                    if stats and categorized_df is not None:
                        st.success("Analyse terminée avec succès!")
                        st.experimental_rerun()
                    else:
                        st.error("Erreur lors de l'analyse des données.")
                        st.info("Tentative de simplification de l'analyse...")

                        # Tentative simplifiée
                        if st.button("Essayer une analyse simplifiée", type="primary"):
                            with st.spinner("Analyse simplifiée en cours..."):
                                try:
                                    # Approche alternative sans catégorisation complète
                                    from data_processing import clean_data
                                    df_simplified = clean_data(df, deep_clean=True)

                                    # Sauvegarder directement
                                    if df_simplified is not None:
                                        df_simplified.to_csv(categorized_path, index=False)
                                        st.success("Analyse simplifiée terminée!")
                                        st.experimental_rerun()
                                except Exception as simple_error:
                                    st.error(f"Échec de l'analyse simplifiée: {str(simple_error)}")
                except Exception as e:
                    # Restaurer la limite de récursion en cas d'erreur
                    sys.setrecursionlimit(current_limit)
                    st.error(f"Erreur lors de l'analyse: {str(e)}")
                    if "recursion" in str(e).lower():
                        st.info("Erreur de récursion détectée. Essayez une analyse simplifiée.")
                        # Proposer une solution
                        if st.button("Essayer une analyse simplifiée", type="primary", key="simple_analysis"):
                            st.session_state.simplified_analysis = True
                            st.experimental_rerun()
                return
        else:
            # Charger les données catégorisées
            try:
                df = pd.read_csv(categorized_path, low_memory=False)
            except Exception as e:
                st.error(f"Erreur lors du chargement des données catégorisées: {str(e)}")
                # Proposer de réanalyser
                if st.button("Réanalyser les données", type="primary"):
                    # Supprimer le fichier problématique
                    os.remove(categorized_path)
                    st.experimental_rerun()
                return

        # Analyser si les visualisations existent
        viz_dir = os.path.join(DATA_DIR, "visualizations")

        if not os.path.exists(viz_dir) or len(os.listdir(viz_dir)) == 0:
            st.info("Génération des visualisations...")

            with st.spinner("Création des graphiques..."):
                try:
                    # Importation différée
                    from visualization import create_visualizations
                    viz_paths = create_visualizations()

                    if viz_paths:
                        st.success("Visualisations créées avec succès!")
                        st.experimental_rerun()
                    else:
                        st.warning("Certaines visualisations n'ont pas pu être créées.")
                        # Continuer quand même
                except Exception as e:
                    st.error(f"Erreur lors de la création des visualisations: {str(e)}")
                    st.info("Nous allons continuer sans visualisations complètes.")

        # Afficher l'analyse avec des onglets pour différentes sections
        tab1, tab2, tab3, tab4 = st.tabs(["Vue d'ensemble", "Artistes & Genres", "Caractéristiques Audio", "Playlists"])

        with tab1:
            show_overview(df)

        with tab2:
            show_artists_analysis(df)

        with tab3:
            show_audio_features_analysis(df)

        with tab4:
            show_playlists_analysis(df)

    except Exception as e:
        st.error(f"Erreur lors de l'analyse des données: {str(e)}")

        # Proposer de recharger la page
        if st.button("Recharger la page", type="primary"):
            st.experimental_rerun()


# Garder le reste des fonctions telles quelles
def show_overview(df):
    """Affiche une vue d'ensemble de la bibliothèque musicale"""
    try:
        st.header("Vue d'ensemble de votre bibliothèque")

        # Statistiques de base
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Titres", f"{len(df)}")

        with col2:
            st.metric("Artistes", f"{df['artist_name'].nunique()}")

        with col3:
            if 'playlist_name' in df.columns:
                st.metric("Playlists", f"{df['playlist_name'].nunique()}")
            else:
                st.metric("Playlists", "N/A")

        # Timeline de sortie d'albums si disponible
        if 'release_year' in df.columns:
            st.subheader("Distribution temporelle")

            # Regrouper par année
            year_counts = df['release_year'].value_counts().sort_index()
            year_df = pd.DataFrame({
                'Année': year_counts.index,
                'Titres': year_counts.values
            })

            # Créer un graphique avec Plotly
            fig = px.bar(year_df, x='Année', y='Titres', title="Distribution des titres par année de sortie")
            fig.update_layout(
                xaxis_title="Année",
                yaxis_title="Nombre de titres",
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    tickmode='linear',
                    tick0=year_df['Année'].min(),
                    dtick=5
                )
            )
            st.plotly_chart(fig, use_container_width=True)

        # Afficher les catégories si disponibles
        if 'energy_dance_category' in df.columns:
            st.subheader("Catégories musicales")

            col1, col2 = st.columns(2)

            with col1:
                # Créer un graphique avec Plotly pour energy_dance_category
                energy_dance_counts = df['energy_dance_category'].value_counts()
                fig = px.pie(
                    names=energy_dance_counts.index,
                    values=energy_dance_counts.values,
                    title="Répartition par style Énergie/Danse",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Créer un graphique avec Plotly pour acoustic_mood_category
                acoustic_mood_counts = df['acoustic_mood_category'].value_counts()
                fig = px.pie(
                    names=acoustic_mood_counts.index,
                    values=acoustic_mood_counts.values,
                    title="Répartition par style Acoustique/Ambiance",
                    color_discrete_sequence=px.colors.sequential.Plasma
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de la vue d'ensemble: {str(e)}")


def show_artists_analysis(df):
    """Affiche l'analyse des artistes"""
    try:
        st.header("Analyse des artistes")

        # Top artistes
        st.subheader("Vos artistes les plus écoutés")

        top_artists = df['artist_name'].value_counts().head(15)
        fig = px.bar(
            x=top_artists.values,
            y=top_artists.index,
            orientation='h',
            title="Top 15 artistes les plus présents dans votre bibliothèque",
            labels={'x': 'Nombre de titres', 'y': 'Artiste'},
            color=top_artists.values,
            color_continuous_scale=px.colors.sequential.Viridis
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

        # Nuage de mots des artistes (si la bibliothèque est installée)
        try:
            from wordcloud import WordCloud

            st.subheader("Nuage d'artistes")

            artist_counts = df['artist_name'].value_counts().to_dict()

            # Génération du nuage de mots
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='black',
                colormap='viridis',
                max_words=100
            ).generate_from_frequencies(artist_counts)

            # Affichage
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)
        except ImportError:
            st.info("La bibliothèque WordCloud n'est pas installée. Le nuage d'artistes n'est pas disponible.")
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'analyse des artistes: {str(e)}")


def show_audio_features_analysis(df):
    """Affiche l'analyse des caractéristiques audio"""
    try:
        st.header("Analyse des caractéristiques audio")

        # Vérifier si les caractéristiques audio sont disponibles
        audio_features = ['danceability', 'energy', 'valence', 'acousticness']
        missing_features = [f for f in audio_features if f not in df.columns]

        if missing_features:
            st.warning(f"Certaines caractéristiques audio ne sont pas disponibles: {', '.join(missing_features)}")
            return

        # Distribution des caractéristiques
        st.subheader("Distribution des caractéristiques audio")

        # Créer un sélecteur de caractéristiques
        feature = st.selectbox(
            "Choisissez une caractéristique à afficher:",
            options=audio_features,
            format_func=lambda x: {
                'danceability': 'Dansabilité',
                'energy': 'Énergie',
                'valence': 'Positivité',
                'acousticness': 'Acoustique'
            }.get(x, x)
        )

        # Afficher un histogramme de la caractéristique sélectionnée
        fig = px.histogram(
            df,
            x=feature,
            nbins=20,
            title=f"Distribution de la {feature}",
            labels={feature: feature.capitalize()},
            color_discrete_sequence=['#1DB954']
        )

        # Ajouter une ligne de densité
        fig.update_traces(opacity=0.7)
        fig.update_layout(bargap=0.1)

        st.plotly_chart(fig, use_container_width=True)

        # Nuage de points Énergie vs Valence
        st.subheader("Relation entre Énergie et Positivité")

        # Créer une figure
        fig = px.scatter(
            df,
            x='energy',
            y='valence',
            color='acousticness',
            size='popularity' if 'popularity' in df.columns else None,
            hover_name='track_name',
            hover_data=['artist_name'],
            color_continuous_scale=px.colors.sequential.Viridis,
            title="Relation entre Énergie et Positivité (Valence)"
        )

        # Ajouter des lignes pour diviser en quadrants
        fig.add_shape(
            type="line", line=dict(dash="dash", width=1, color="gray"),
            x0=0, y0=0.5, x1=1, y1=0.5
        )
        fig.add_shape(
            type="line", line=dict(dash="dash", width=1, color="gray"),
            x0=0.5, y0=0, x1=0.5, y1=1
        )

        # Ajouter des annotations pour les quadrants
        fig.add_annotation(x=0.25, y=0.75, text="Calme & Positif", showarrow=False)
        fig.add_annotation(x=0.75, y=0.75, text="Énergique & Positif", showarrow=False)
        fig.add_annotation(x=0.25, y=0.25, text="Calme & Sombre", showarrow=False)
        fig.add_annotation(x=0.75, y=0.25, text="Énergique & Sombre", showarrow=False)

        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'analyse des caractéristiques audio: {str(e)}")


def show_playlists_analysis(df):
    """Affiche l'analyse des playlists"""
    try:
        st.header("Analyse des playlists")

        if 'playlist_name' not in df.columns:
            st.warning("Aucune information de playlist n'est disponible dans les données.")
            return

        # Liste des playlists
        playlists = df['playlist_name'].unique()

        # Taille des playlists
        playlist_sizes = df['playlist_name'].value_counts()

        # Graphique de la taille des playlists
        fig = px.bar(
            x=playlist_sizes.index,
            y=playlist_sizes.values,
            title="Taille des playlists",
            labels={'x': 'Playlist', 'y': 'Nombre de titres'},
            color=playlist_sizes.values,
            color_continuous_scale=px.colors.sequential.Viridis
        )

        fig.update_layout(
            xaxis={'categoryorder': 'total descending'}
        )

        st.plotly_chart(fig, use_container_width=True)

        # Caractéristiques par playlist
        st.subheader("Profil audio des playlists")

        # Vérifier si les caractéristiques audio sont disponibles
        audio_features = ['danceability', 'energy', 'valence', 'acousticness']
        missing_features = [f for f in audio_features if f not in df.columns]

        if missing_features:
            st.warning(f"Certaines caractéristiques audio ne sont pas disponibles pour le profil des playlists.")
            return

        # Créer un graphique radar pour chaque playlist
        # Limiter aux 10 plus grandes playlists pour la lisibilité
        top_playlists = playlist_sizes.head(10).index.tolist()

        # Sélecteur de playlist
        selected_playlist = st.selectbox(
            "Choisissez une playlist à analyser:",
            options=top_playlists
        )

        # Calculer les moyennes des caractéristiques pour la playlist sélectionnée
        playlist_data = df[df['playlist_name'] == selected_playlist]
        feature_means = playlist_data[audio_features].mean()

        # Créer un graphique radar avec plotly
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=feature_means.values,
            theta=feature_means.index,
            fill='toself',
            name=selected_playlist,
            line_color='#1DB954'
        ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            title=f"Profil audio de la playlist: {selected_playlist}"
        )

        st.plotly_chart(fig, use_container_width=True)

        # Top artistes dans la playlist
        top_artists_in_playlist = playlist_data['artist_name'].value_counts().head(10)

        fig = px.bar(
            x=top_artists_in_playlist.values,
            y=top_artists_in_playlist.index,
            orientation='h',
            title=f"Top 10 artistes dans la playlist: {selected_playlist}",
            labels={'x': 'Nombre de titres', 'y': 'Artiste'},
            color=top_artists_in_playlist.values,
            color_continuous_scale=px.colors.sequential.Viridis
        )

        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Erreur lors de l'affichage de l'analyse des playlists: {str(e)}")