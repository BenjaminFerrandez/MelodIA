import streamlit as st
import os
import sys
from streamlit_option_menu import option_menu

# Ajouter le répertoire courant au PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pages.components import data_analysis, data_extraction, recommendations, settings, top_artists, home

# Configuration de la page
st.set_page_config(
    page_title="MelodIA - Analyseur de Playlists Spotify",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS intégré directement dans le code plutôt que chargé depuis un fichier
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


# Fonction pour vérifier l'état d'authentification
def check_auth_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "username" not in st.session_state:
        st.session_state.username = None


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
    # Logo simple en texte
    st.title("🎵 MelodIA")
    st.write("Analyseur de Playlists Spotify")

    # Menu de navigation (uniquement si authentifié)
    if st.session_state.authenticated:
        # Afficher l'utilisateur connecté
        st.write(f"Connecté en tant que: **{st.session_state.username}**")

        # Menu principal
        selected = option_menu(
            "Navigation",
            ["Accueil", "Extraction", "Analyse", "Recommandations", "Top Artistes", "Paramètres"],
            icons=["house", "cloud-download", "graph-up", "music-note-list", "person-badge", "gear"],
            menu_icon="list",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#1E1E1E"},
                "icon": {"color": "#1DB954", "font-size": "14px"},
                "nav-link": {"color": "#FFFFFF", "font-size": "14px", "text-align": "left", "margin": "0px",
                             "--hover-color": "#363636"},
                "nav-link-selected": {"background-color": "#1DB954"},
            }
        )

        # Bouton de déconnexion
        if st.button("Déconnexion", type="primary", use_container_width=True):
            logout()
    else:
        # Si non authentifié, afficher uniquement le message de connexion
        st.info("Veuillez vous connecter pour accéder à l'application")
        selected = "Accueil"

# Corps principal de l'application
if not st.session_state.authenticated:
    # Page d'accueil avec connexion
    home.show()
else:
    # Afficher la page sélectionnée
    if selected == "Accueil":
        home.show()
    elif selected == "Extraction":
        data_extraction.show()
    elif selected == "Analyse":
        data_analysis.show()
    elif selected == "Recommandations":
        recommendations.show()
    elif selected == "Top Artistes":
        top_artists.show()
    elif selected == "Paramètres":
        settings.show()