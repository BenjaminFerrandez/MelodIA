import sys
import os

import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fix_circular_imports import resolve_circular_imports
resolve_circular_imports()

from streamlit_option_menu import option_menu
from pages.components import data_analysis, data_extraction, recommendations, settings, top_artists, home

# Configuration de la page
st.set_page_config(
    page_title="MelodIA - Analyseur de Playlists Spotify",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Charger le custom CSS
def load_css():
    css_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "custom.css")
    if os.path.exists(css_file):
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Style CSS intégré directement si le fichier n'existe pas
        st.markdown("""
        <style>
        body {
            color: #FFFFFF;
            background-color: #121212;
        }
        .stApp {
            background-color: #121212;
        }
        h1, h2 {
            color: #1DB954;
        }
        a {
            color: #1DB954;
        }
        </style>
        """, unsafe_allow_html=True)


load_css()


# Fonction pour vérifier l'état d'authentification
def check_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "page" not in st.session_state:
        st.session_state.page = "home"


# Fonction de déconnexion
def logout():
    st.session_state.authenticated = False
    st.session_state.username = None
    from spotify_auth import SpotifyAuth
    auth = SpotifyAuth.get_instance()
    auth.logout()
    st.experimental_rerun()


# Vérifier l'authentification
check_auth_state()

# Sidebar avec menu
with st.sidebar:
    # Logo avec icône et texte dans un conteneur flex
    st.markdown("""
    <div class="logo-container">
        <span class="logo-icon">🎵</span>
        <span class="logo-text">MelodIA</span>
    </div>
    """, unsafe_allow_html=True)

    st.write("Analyseur de Playlists Spotify")

    # Menu de navigation (uniquement si authentifié)
    if st.session_state.authenticated:
        # Afficher l'utilisateur connecté
        st.write(f"Connecté en tant que: **{st.session_state.username}**")

        # Menu principal avec icônes améliorées
        selected = option_menu(
            "Navigation",
            ["Accueil", "Extraction", "Analyse", "Recommandations", "Top Artistes", "Paramètres"],
            icons=["house-fill", "cloud-download-fill", "graph-up-arrow", "music-note-list", "person-badge-fill",
                   "gear-fill"],
            menu_icon="list",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1E1E1E"},
                "icon": {"color": "#1DB954", "font-size": "16px"},
                "nav-link": {"color": "#FFFFFF", "font-size": "15px", "text-align": "left", "margin": "0px",
                             "--hover-color": "#363636", "font-weight": "500"},
                "nav-link-selected": {"background-color": "#1DB954", "font-weight": "600"},
            }
        )

        # Mettre à jour la page sélectionnée dans l'état de session
        st.session_state.page = selected.lower()

        # Bouton de déconnexion avec message de confirmation
        if st.button("Déconnexion", type="primary", use_container_width=True):
            logout_confirmation = st.empty()
            if logout_confirmation.button("Confirmer la déconnexion?", key="confirm_logout"):
                logout()
                logout_confirmation.empty()
            else:
                pass
    else:
        # Si non authentifié, afficher uniquement le message de connexion
        st.info("Veuillez vous connecter pour accéder à l'application")
        st.session_state.page = "home"

# Corps principal de l'application
if not st.session_state.authenticated:
    # Page d'accueil avec connexion
    home.show()
else:
    # Afficher la page sélectionnée selon st.session_state.page
    if st.session_state.page == "accueil":
        home.show()
    elif st.session_state.page == "extraction":
        data_extraction.show()
    elif st.session_state.page == "analyse":
        data_analysis.show()
    elif st.session_state.page == "recommandations":
        recommendations.show()
    elif st.session_state.page == "top artistes":
        top_artists.show()
    elif st.session_state.page == "paramètres":
        settings.show()
    else:
        home.show()

# Ajouter un footer
st.markdown("""
<div class="footer">
    MelodIA - Analyseur de Playlists Spotify © 2023-2025
</div>
""", unsafe_allow_html=True)