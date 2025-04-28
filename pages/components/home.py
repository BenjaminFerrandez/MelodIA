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
            st.balloons()  # Effet de célébration
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur lors de la connexion: {str(e)}")
            if "redirect_uri_mismatch" in str(e).lower():
                st.info(
                    "Conseil: Vérifiez que l'URI de redirection dans votre tableau de bord Spotify Developer correspond exactement à 'http://127.0.0.1:8080'")


def show():
    if not st.session_state.authenticated:
        # Si non authentifié, afficher la page d'accueil avec connexion
        # En-tête avec animation CSS
        st.markdown("""
        <style>
        .title-container {
            display: flex;
            align-items: center;
            animation: fadeInUp 1s ease-out;
            margin-bottom: 2rem;
        }
        .spotify-icon {
            font-size: 4rem;
            margin-right: 1rem;
            color: #1DB954;
        }
        .welcome-title {
            font-size: 3rem;
            font-weight: 700;
            color: #1DB954;
            margin: 0;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .feature-card {
            background-color: #282828;
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            animation: fadeIn 1.2s ease-out;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 4px solid #1DB954;
        }

        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }

        .feature-icon {
            font-size: 2rem;
            color: #1DB954;
            margin-bottom: 1rem;
        }

        .feature-title {
            font-size: 1.3rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #FFFFFF;
        }

        .feature-desc {
            color: #B3B3B3;
            font-size: 1rem;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .login-container {
            margin-top: 2rem;
            animation: fadeIn 1.5s ease-out;
            padding: 2rem;
            border-radius: 8px;
            background-color: #1E1E1E;
            border: 1px solid rgba(255,255,255,0.1);
        }

        .login-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: #FFFFFF;
        }
        </style>

        <div class="title-container">
            <div class="spotify-icon">🎵</div>
            <h1 class="welcome-title">MelodIA</h1>
        </div>
        """, unsafe_allow_html=True)

        st.subheader("Analyseur et Générateur de Playlists")

        # Présentation des fonctionnalités en cards
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <div class="feature-title">Analyse complète de votre bibliothèque</div>
            <div class="feature-desc">Découvrez des insights sur vos habitudes d'écoute, artistes préférés et genres dominants.</div>
        </div>

        <div class="feature-card">
            <div class="feature-icon">💫</div>
            <div class="feature-title">Recommandations personnalisées</div>
            <div class="feature-desc">Recevez des suggestions de titres basées sur vos goûts et découvrez de nouveaux artistes.</div>
        </div>

        <div class="feature-card">
            <div class="feature-icon">🎧</div>
            <div class="feature-title">Création de playlists thématiques</div>
            <div class="feature-desc">Générez des playlists adaptées à chaque ambiance, activité ou humeur.</div>
        </div>

        <div class="feature-card">
            <div class="feature-icon">🔍</div>
            <div class="feature-title">Visualisations interactives</div>
            <div class="feature-desc">Explorez vos données musicales à travers des graphiques clairs et interactifs.</div>
        </div>
        """, unsafe_allow_html=True)

        # Conteneur de connexion
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Commencez l\'exploration</div>', unsafe_allow_html=True)
        st.write("Connectez-vous avec votre compte Spotify pour découvrir votre profil musical unique.")

        # Bouton de connexion
        st.button("Connexion avec Spotify", type="primary", on_click=login, key="login_button")

        # Informations complémentaires
        with st.expander("Comment ça fonctionne ?"):
            st.markdown("""
            1. **Connexion sécurisée** : MelodIA se connecte à votre compte Spotify via l'API officielle.
            2. **Extraction des données** : L'application récupère vos playlists et les caractéristiques audio de vos titres.
            3. **Analyse personnalisée** : Vos habitudes d'écoute sont analysées pour créer votre profil musical unique.
            4. **Recommandations** : Sur la base de cette analyse, des recommandations personnalisées vous sont proposées.

            Toutes les données restent confidentielles et sont stockées localement sur votre appareil.
            """)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        # Si authentifié, afficher le tableau de bord personnel
        st.title(f"Bienvenue, {st.session_state.username} 👋")

        # Vérifier si des données existent
        tracks_path = os.path.join(DATA_DIR, "tracks.csv")
        categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

        # Afficher des métriques et statut
        col1, col2, col3 = st.columns(3)

        with col1:
            if os.path.exists(tracks_path):
                df = pd.read_csv(tracks_path)
                st.metric("Titres extraits", f"{len(df)}")
            else:
                st.metric("Titres extraits", "0")

        with col2:
            if os.path.exists(categorized_path):
                df = pd.read_csv(categorized_path)
                st.metric("Titres analysés", f"{len(df)}")
            else:
                st.metric("Titres analysés", "0")

        with col3:
            # Vérifier si l'utilisateur a des playlists
            if os.path.exists(tracks_path):
                df = pd.read_csv(tracks_path)
                if 'playlist_name' in df.columns:
                    st.metric("Playlists", f"{df['playlist_name'].nunique()}")
                else:
                    st.metric("Playlists", "0")
            else:
                st.metric("Playlists", "0")

        # Proposer des actions selon l'état des données
        if not os.path.exists(tracks_path):
            st.warning("Aucune donnée n'a encore été extraite de Spotify.")

            # Carte d'action pour l'extraction
            st.markdown("""
            <div style="background-color: #282828; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #1DB954;">
                <h3 style="color: #FFFFFF; margin-top: 0;">Commencer l'extraction</h3>
                <p style="color: #B3B3B3;">Récupérez vos playlists et titres depuis Spotify pour commencer l'analyse.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Aller à l'extraction", type="primary"):
                st.session_state.page = "extraction"
                st.experimental_rerun()

        elif not os.path.exists(categorized_path):
            st.info("Vos données ont été extraites, mais l'analyse n'est pas encore terminée.")

            # Carte d'action pour l'analyse
            st.markdown("""
            <div style="background-color: #282828; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #1DB954;">
                <h3 style="color: #FFFFFF; margin-top: 0;">Analyser vos données</h3>
                <p style="color: #B3B3B3;">Découvrez des insights sur vos goûts musicaux et obtenez des recommandations personnalisées.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Aller à l'analyse", type="primary"):
                st.session_state.page = "analyse"
                st.experimental_rerun()

        else:
            st.success("Votre bibliothèque musicale a été entièrement analysée. Explorez les différentes sections !")

            # Afficher des actions rapides
            st.subheader("Actions rapides")

            col1, col2 = st.columns(2)

            with col1:
                # Carte pour les recommandations
                st.markdown("""
                <div style="background-color: #282828; padding: 1.5rem; border-radius: 8px; height: 200px; border-left: 4px solid #1DB954;">
                    <h3 style="color: #FFFFFF; margin-top: 0;">Recommandations</h3>
                    <p style="color: #B3B3B3;">Découvrez des titres similaires à vos favoris ou explorez de nouvelles playlists thématiques.</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Voir les recommandations", key="rec_button"):
                    st.session_state.page = "recommandations"
                    st.experimental_rerun()

            with col2:
                # Carte pour les artistes
                st.markdown("""
                <div style="background-color: #282828; padding: 1.5rem; border-radius: 8px; height: 200px; border-left: 4px solid #1DB954;">
                    <h3 style="color: #FFFFFF; margin-top: 0;">Top Artistes</h3>
                    <p style="color: #B3B3B3;">Découvrez vos artistes les plus écoutés et créez des playlists avec leurs meilleurs titres.</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("Voir vos artistes préférés", key="artists_button"):
                    st.session_state.page = "top artistes"
                    st.experimental_rerun()

            # Conseils d'utilisation
            with st.expander("Conseils d'utilisation"):
                st.markdown("""
                - **Analyse** : Explorez des graphiques qui révèlent vos préférences musicales
                - **Recommandations** : Obtenez des suggestions basées sur un titre spécifique ou une ambiance
                - **Top Artistes** : Découvrez vos artistes les plus écoutés sur différentes périodes
                - **Extraction** : Vous pouvez actualiser vos données à tout moment
                """)