import streamlit as st
import pandas as pd
import os
import time
from config import DATA_DIR
from spotify_api import extract_spotify_data
from data_processing import process_data


def show_data_preview(df, title, n=5):
    """Affiche un aperçu du DataFrame avec un titre"""
    st.subheader(title)
    st.dataframe(df.head(n))
    st.caption(f"Affichage de {n} lignes sur {len(df)}")


def extract_data():
    """Fonction pour gérer l'extraction des données"""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    progress_bar = progress_placeholder.progress(0)
    status_placeholder.info("Initialisation de l'extraction des données...")

    try:
        # Étape 1: Connexion et extraction
        progress_bar.progress(10)
        status_placeholder.info("Connexion à l'API Spotify...")
        time.sleep(1)

        progress_bar.progress(20)
        status_placeholder.info("Récupération des playlists en cours...")
        tracks, features = extract_spotify_data()

        if tracks is None:
            status_placeholder.error("Échec de l'extraction des données. Veuillez réessayer.")
            progress_placeholder.empty()
            return False

        progress_bar.progress(60)
        status_placeholder.info(f"Extraction réussie: {len(tracks)} titres récupérés. Traitement des données...")

        # Étape 2: Traitement des données
        progress_bar.progress(80)
        cleaned_data = process_data()

        progress_bar.progress(100)
        status_placeholder.success("✅ Extraction et traitement terminés avec succès!")
        time.sleep(2)

        # Nettoyer les placeholders
        progress_placeholder.empty()
        status_placeholder.empty()

        return True

    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.error(f"Une erreur s'est produite: {str(e)}")
        return False


def show():
    st.title("Extraction des Données Spotify")

    # Vérifier si des données existent déjà
    tracks_path = os.path.join(DATA_DIR, "tracks.csv")
    features_path = os.path.join(DATA_DIR, "audio_features.csv")
    cleaned_path = os.path.join(DATA_DIR, "cleaned_tracks.csv")

    has_tracks = os.path.exists(tracks_path)
    has_features = os.path.exists(features_path)
    has_cleaned = os.path.exists(cleaned_path)

    # Afficher l'état actuel des données
    col1, col2, col3 = st.columns(3)

    with col1:
        if has_tracks:
            tracks_df = pd.read_csv(tracks_path)
            st.metric("Titres", f"{len(tracks_df)}", help="Nombre total de titres extraits")
        else:
            st.metric("Titres", "0", help="Aucun titre extrait")

    with col2:
        if has_features:
            features_df = pd.read_csv(features_path)
            st.metric("Caractéristiques Audio", f"{len(features_df)}",
                      help="Nombre de titres avec caractéristiques audio")
        else:
            st.metric("Caractéristiques Audio", "0", help="Aucune caractéristique audio extraite")

    with col3:
        if has_cleaned:
            cleaned_df = pd.read_csv(cleaned_path)
            st.metric("Titres Traités", f"{len(cleaned_df)}", help="Nombre de titres après nettoyage")
        else:
            st.metric("Titres Traités", "0", help="Aucun titre traité")

    # Options d'extraction
    st.subheader("Options d'extraction")

    if has_tracks:
        st.warning(
            "Des données ont déjà été extraites. L'extraction de nouvelles données remplacera les données existantes.")

    # Boutons d'extraction
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Extraire les données", type="primary", use_container_width=True):
            success = extract_data()
            if success:
                st.experimental_rerun()

    with col2:
        if st.button("Forcer nouvelle authentification", type="secondary", use_container_width=True):
            with st.spinner("Réinitialisation de l'authentification..."):
                from spotify_auth import SpotifyAuth
                auth = SpotifyAuth.get_instance(force_new_auth=True)
                st.success("Authentification réinitialisée")

    # Afficher des aperçus des données si disponibles
    if has_cleaned:
        st.markdown("---")
        st.subheader("Aperçu des données")

        # Charger les données nettoyées
        cleaned_df = pd.read_csv(cleaned_path)

        # Créer onglets pour différents aperçus
        tab1, tab2, tab3 = st.tabs(["Titres", "Caractéristiques Audio", "Par Playlist"])

        with tab1:
            show_data_preview(cleaned_df[['track_name', 'artist_name', 'album_name']], "Aperçu des titres")

        with tab2:
            if 'danceability' in cleaned_df.columns:
                audio_cols = [col for col in cleaned_df.columns if col in
                              ['track_name', 'danceability', 'energy', 'valence', 'acousticness', 'tempo']]
                show_data_preview(cleaned_df[audio_cols], "Aperçu des caractéristiques audio")
            else:
                st.warning("Caractéristiques audio non disponibles")

        with tab3:
            if 'playlist_name' in cleaned_df.columns:
                playlist_summary = cleaned_df.groupby('playlist_name').agg(
                    titres=('track_name', 'count'),
                    artistes_uniques=('artist_name', 'nunique')
                ).reset_index()
                st.dataframe(playlist_summary)
            else:
                st.warning("Informations de playlist non disponibles")

    # Instructions si aucune donnée n'est disponible
    elif not has_tracks:
        st.info("""
        ### Comment fonctionne l'extraction des données:

        1. L'application se connecte à votre compte Spotify via l'API officielle
        2. Vos playlists et leurs titres sont récupérés
        3. Les caractéristiques audio (danceability, energy, etc.) sont extraites
        4. Les données sont nettoyées et préparées pour l'analyse

        Aucune donnée n'est partagée avec des tiers. Toutes les données sont stockées localement.
        """)