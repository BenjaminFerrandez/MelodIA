import streamlit as st
import os
import shutil
from config import DATA_DIR, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI


def clear_data():
    """Supprime toutes les données extraites"""
    try:
        # Supprimer tous les fichiers dans le répertoire de données
        for file in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)

        # Réinitialiser les données de session qui dépendent des fichiers
        if 'top_artists_data' in st.session_state:
            del st.session_state.top_artists_data

        return True
    except Exception as e:
        st.error(f"Erreur lors de la suppression des données: {str(e)}")
        return False


def show():
    st.title("Paramètres")

    # Section Compte Spotify
    st.header("Compte Spotify")

    # Afficher l'utilisateur connecté
    if st.session_state.authenticated:
        st.success(f"Connecté en tant que: {st.session_state.username}")

        if st.button("Se déconnecter", type="secondary"):
            from spotify_auth import SpotifyAuth
            auth = SpotifyAuth.get_instance()

            if auth.logout():
                st.session_state.authenticated = False
                st.session_state.username = None
                st.success("Déconnexion réussie")
                st.experimental_rerun()
            else:
                st.error("Erreur lors de la déconnexion")
    else:
        st.warning("Non connecté")

        if st.button("Se connecter"):
            st.session_state.page = "home"
            st.experimental_rerun()

    # Section Configuration API
    st.header("Configuration API Spotify")

    # Afficher la configuration actuelle
    st.code(f"""
    SPOTIFY_CLIENT_ID = {'*' * (len(SPOTIFY_CLIENT_ID) - 4) + SPOTIFY_CLIENT_ID[-4:] if SPOTIFY_CLIENT_ID else 'Non configuré'}
    SPOTIFY_CLIENT_SECRET = {'*' * (len(SPOTIFY_CLIENT_SECRET) - 4) + SPOTIFY_CLIENT_SECRET[-4:] if SPOTIFY_CLIENT_SECRET else 'Non configuré'}
    SPOTIFY_REDIRECT_URI = {SPOTIFY_REDIRECT_URI if SPOTIFY_REDIRECT_URI else 'Non configuré'}
    """)

    with st.expander("Comment obtenir vos identifiants API"):
        st.markdown("""
        Pour obtenir vos propres identifiants API Spotify:

        1. Rendez-vous sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
        2. Connectez-vous avec votre compte Spotify
        3. Créez une nouvelle application
        4. Récupérez votre Client ID et Client Secret
        5. Ajoutez http://127.0.0.1:8080 comme URI de redirection
        6. Modifiez le fichier `.env` à la racine du projet avec vos identifiants
        """)

    # Section Gestion des données
    st.header("Gestion des données")

    # Informations sur l'emplacement des données
    st.info(f"Emplacement des données: {DATA_DIR}")

    col1, col2 = st.columns(2)

    with col1:
        # Vérifier si des données existent
        if os.path.exists(os.path.join(DATA_DIR, "tracks.csv")):
            # Calculer la taille des données
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(DATA_DIR):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    total_size += os.path.getsize(fp)

            # Convertir en format lisible
            if total_size < 1024:
                size_str = f"{total_size} octets"
            elif total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.2f} Ko"
            else:
                size_str = f"{total_size / (1024 * 1024):.2f} Mo"

            st.metric("Taille des données", size_str)
        else:
            st.metric("Taille des données", "0 octet")

    with col2:
        if os.path.exists(os.path.join(DATA_DIR, "tracks.csv")):
            # Compter les fichiers
            file_count = sum(len(files) for _, _, files in os.walk(DATA_DIR))
            st.metric("Nombre de fichiers", str(file_count))
        else:
            st.metric("Nombre de fichiers", "0")

    # Option pour supprimer toutes les données
    st.warning("La suppression des données est irréversible. Vous devrez extraire à nouveau vos données Spotify.")
    if st.button("Supprimer toutes les données", type="primary"):
        confirmation = st.text_input("Tapez 'SUPPRIMER' pour confirmer")

        if confirmation == "SUPPRIMER":
            with st.spinner("Suppression des données en cours..."):
                if clear_data():
                    st.success("Toutes les données ont été supprimées")
                    st.info("Vous pouvez maintenant extraire de nouvelles données")
                else:
                    st.error("Erreur lors de la suppression des données")

    # Section À propos
    st.header("À propos de MelodIA")

    st.markdown("""
    **MelodIA** est un analyseur et générateur de playlists musicales qui utilise l'API Spotify pour extraire des données sur vos habitudes d'écoute et vous proposer des recommandations personnalisées.

    - Version: 1.0.0
    - Développé avec Python et Streamlit
    - Utilise l'API Spotify via la bibliothèque spotipy

    #### Bibliothèques principales:
    - pandas: Manipulation des données
    - matplotlib/seaborn/plotly: Visualisation des données
    - scikit-learn: Algorithmes de recommandation
    - streamlit: Interface utilisateur

    #### Crédits:
    - [Spotify API](https://developer.spotify.com/documentation/web-api/)
    - [Spotipy](https://spotipy.readthedocs.io/)
    - [Streamlit](https://streamlit.io/)
    """)