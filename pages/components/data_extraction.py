import streamlit as st
import pandas as pd
import os
import time
import traceback
from config import DATA_DIR
from spotify_api import extract_spotify_data
from data_processing import process_data


def show_data_preview(df, title, n=5):
    """Affiche un aperçu du DataFrame avec un titre"""
    if df is None or df.empty:
        st.warning(f"Aucune donnée disponible pour: {title}")
        return

    st.subheader(title)
    st.dataframe(df.head(n))
    st.caption(f"Affichage de {n} lignes sur {len(df)}")


def extract_data(with_retries=True):
    """Fonction pour gérer l'extraction des données avec gestion d'erreurs améliorée"""
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    error_placeholder = st.empty()

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
            progress_placeholder.empty()
            status_placeholder.error("Échec de l'extraction des données.")
            error_placeholder.error(
                "Impossible de récupérer les playlists. Vérifiez votre connexion et vos autorisations.")

            # Proposer une nouvelle authentification
            if with_retries and st.button("Essayer avec une nouvelle authentification", key="retry_auth"):
                status_placeholder.info("Tentative avec une nouvelle authentification...")
                tracks, features = extract_spotify_data(force_new_auth=True)

                if tracks is None:
                    progress_placeholder.empty()
                    status_placeholder.error("Échec persistant de l'extraction. Veuillez vérifier les points suivants:")
                    error_placeholder.markdown("""
                    1. Votre connexion Internet fonctionne
                    2. Vos identifiants API Spotify sont corrects
                    3. Votre compte Spotify possède au moins une playlist
                    4. L'URI de redirection est correctement configuré dans le tableau de bord Spotify
                    """)
                    return False
            else:
                return False

        progress_bar.progress(60)
        status_placeholder.info(f"Extraction réussie: {len(tracks)} titres récupérés. Traitement des données...")

        # Étape 2: Traitement des données
        progress_bar.progress(80)
        try:
            cleaned_data = process_data()

            if cleaned_data is None or cleaned_data.empty:
                status_placeholder.warning("Attention: Le traitement des données a retourné un résultat vide.")
                # Continuer quand même, ce n'est pas une erreur fatale

            progress_bar.progress(100)
            status_placeholder.success("✅ Extraction et traitement terminés avec succès!")
            time.sleep(2)

            # Nettoyer les placeholders
            progress_placeholder.empty()
            status_placeholder.empty()
            error_placeholder.empty()

            return True

        except Exception as e:
            progress_bar.progress(90)
            status_placeholder.warning(f"L'extraction a réussi mais le traitement a rencontré un problème: {str(e)}")
            error_placeholder.error(f"Détails: {traceback.format_exc()}")

            # Proposer de continuer quand même
            if st.button("Continuer sans traitement complet", key="skip_processing"):
                progress_placeholder.empty()
                status_placeholder.empty()
                error_placeholder.empty()
                return True
            return False

    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.error(f"Une erreur s'est produite pendant l'extraction:")
        error_details = f"{str(e)}\n\n{traceback.format_exc()}"
        error_placeholder.code(error_details)

        # Suggestions de résolution
        st.markdown("""
        ### Suggestions pour résoudre le problème:

        1. **Vérifiez votre connexion Internet**
        2. **Vérifiez vos identifiants API dans le fichier `.env`**
        3. **Essayez une nouvelle authentification**
        4. **Assurez-vous que votre compte Spotify possède des playlists accessibles**
        """)

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

    # Afficher l'état actuel des données dans une carte stylisée
    st.markdown("""
    <div style="background-color: #282828; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
        <h3 style="margin-top: 0; color: white;">État des données</h3>
    """, unsafe_allow_html=True)

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

    st.markdown("</div>", unsafe_allow_html=True)

    # Options d'extraction
    st.subheader("Options d'extraction")

    if has_tracks:
        st.warning(
            "Des données ont déjà été extraites. L'extraction de nouvelles données remplacera les données existantes.")

    # Boutons d'extraction avec style amélioré
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Extraire les données", type="primary", use_container_width=True):
            success = extract_data()
            if success:
                st.success("Extraction terminée! Rafraîchissement de la page...")
                time.sleep(2)
                st.experimental_rerun()

    with col2:
        if st.button("Forcer nouvelle authentification", type="secondary", use_container_width=True):
            with st.spinner("Réinitialisation de l'authentification..."):
                try:
                    from spotify_auth import SpotifyAuth
                    auth = SpotifyAuth.get_instance(force_new_auth=True)
                    st.success("Authentification réinitialisée")
                except Exception as e:
                    st.error(f"Erreur lors de la réinitialisation de l'authentification: {e}")

    # Afficher des aperçus des données si disponibles
    if has_cleaned or has_tracks:
        st.markdown("---")
        st.subheader("Aperçu des données")

        # Création d'onglets pour différents aperçus
        tab1, tab2, tab3 = st.tabs(["Titres", "Caractéristiques Audio", "Par Playlist"])

        try:
            # On privilégie les données nettoyées, sinon on utilise les données brutes
            if has_cleaned:
                df = pd.read_csv(cleaned_path, low_memory=False)
            elif has_tracks:
                df = pd.read_csv(tracks_path, low_memory=False)
            else:
                df = None

            if df is not None:
                with tab1:
                    cols_to_show = ['track_name', 'artist_name', 'album_name']
                    available_cols = [col for col in cols_to_show if col in df.columns]
                    if available_cols:
                        show_data_preview(df[available_cols], "Aperçu des titres")
                    else:
                        st.warning("Structure de données inattendue. Colonnes manquantes.")

                with tab2:
                    audio_cols = [col for col in df.columns if col in
                                  ['track_name', 'danceability', 'energy', 'valence', 'acousticness', 'tempo']]
                    if 'danceability' in audio_cols:
                        show_data_preview(df[audio_cols], "Aperçu des caractéristiques audio")
                    else:
                        st.warning("Caractéristiques audio non disponibles")

                with tab3:
                    if 'playlist_name' in df.columns:
                        try:
                            playlist_summary = df.groupby('playlist_name').agg(
                                titres=('track_name', 'count'),
                                artistes_uniques=('artist_name', 'nunique')
                            ).reset_index()
                            st.dataframe(playlist_summary)
                        except Exception as e:
                            st.error(f"Erreur lors de l'agrégation des données par playlist: {e}")
                    else:
                        st.warning("Informations de playlist non disponibles")
        except Exception as e:
            st.error(f"Erreur lors du chargement des aperçus: {e}")
            st.code(traceback.format_exc())

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

        # Ajouter une carte d'aide pour l'installation
        with st.expander("Besoin d'aide pour configurer l'application?"):
            st.markdown("""
            ### Configuration de l'application

            1. **Créez une application Spotify**:
               - Rendez-vous sur [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
               - Créez une nouvelle application
               - Dans les paramètres, ajoutez exactement `http://127.0.0.1:8080` comme URI de redirection

            2. **Configurez les identifiants**:
               - Créez un fichier `.env` à la racine du projet avec ce contenu:
               ```
               SPOTIFY_CLIENT_ID=votre_client_id
               SPOTIFY_CLIENT_SECRET=votre_client_secret
               SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080
               ```

            3. **Installez les dépendances**:
               ```
               pip install -r requirements.txt
               ```

            4. **Lancez l'application**:
               ```
               streamlit run app.py
               ```
            """)