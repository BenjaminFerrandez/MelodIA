import streamlit as st
import pandas as pd
import os
from config import DATA_DIR
from spotify_auth import SpotifyAuth


def login():
    """Fonction pour gérer la connexion à Spotify"""
    with st.spinner("Connexion à Spotify en cours..."):
        try:
            auth = SpotifyAuth.get_instance(force_new_auth=True)
            sp = auth.get_spotify_client()
            user_info = sp.current_user()

            # Stocker les informations d'authentification dans la session
            st.session_state.authenticated = True
            st.session_state.username = user_info.get('display_name', user_info['id'])

            st.success(f"Connecté à Spotify en tant que {st.session_state.username}")
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur lors de la connexion: {str(e)}")


def show():
    if not st.session_state.authenticated:
        # Si non authentifié, afficher la page d'accueil avec connexion
        st.title("🎵 MelodIA - Analyseur de Playlists Spotify")

        st.markdown("""
        ### Bienvenue sur MelodIA

        Cette application vous permet d'analyser vos playlists Spotify et de générer des recommandations personnalisées.

        #### Fonctionnalités principales:

        - 📊 Analyse complète de votre bibliothèque musicale
        - 🔍 Visualisations interactives de vos préférences musicales
        - 💫 Recommandations personnalisées basées sur vos goûts
        - 🎧 Création de playlists thématiques
        - 🌟 Découverte de votre profil d'écoute unique

        #### Pour commencer, connectez-vous à votre compte Spotify:
        """)

        # Bouton de connexion
        st.button("Connexion avec Spotify", type="primary", on_click=login, key="login_button")

    else:
        # Si authentifié, afficher le tableau de bord
        st.title(f"Bienvenue, {st.session_state.username} 👋")

        # Vérifier si des données existent et afficher un message approprié
        tracks_path = os.path.join(DATA_DIR, "tracks.csv")

        if os.path.exists(tracks_path):
            st.success("Vos données Spotify ont été extraites avec succès!")
        else:
            st.warning("Aucune donnée n'a encore été extraite de Spotify.")
            st.markdown("""
            ### Pour commencer, suivez ces étapes:

            1. Allez à la page **Extraction** dans le menu de gauche
            2. Cliquez sur le bouton d'extraction pour récupérer vos playlists
            3. Une fois l'extraction terminée, explorez les analyses et recommandations
            """)