import streamlit as st
import os
import traceback
import logging
import datetime
from config import DATA_DIR

# Configuration du logging
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"melodia_{datetime.datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("MelodIA")


def log_error(error, context="general"):
    """
    Enregistre une erreur dans le fichier de log

    Parameters:
        error (Exception): L'erreur à logger
        context (str): Le contexte dans lequel l'erreur s'est produite
    """
    error_message = f"ERREUR [{context}]: {str(error)}"
    error_traceback = traceback.format_exc()

    logger.error(error_message)
    logger.error(error_traceback)

    return error_message, error_traceback


def handle_error(error, context="general", show_traceback=True):
    """
    Gère une erreur en l'enregistrant et en affichant un message à l'utilisateur

    Parameters:
        error (Exception): L'erreur à gérer
        context (str): Le contexte dans lequel l'erreur s'est produite
        show_traceback (bool): Afficher la trace complète à l'utilisateur

    Returns:
        bool: False (pour indiquer l'échec de l'opération)
    """
    error_message, error_traceback = log_error(error, context)

    # Afficher l'erreur à l'utilisateur avec Streamlit
    error_container = st.error(f"Une erreur s'est produite: {error_message}")

    if show_traceback:
        with st.expander("Détails techniques"):
            st.code(error_traceback)

    # Afficher des suggestions de résolution selon le type d'erreur
    suggest_solutions(error, context)

    return False


def suggest_solutions(error, context):
    """
    Suggère des solutions en fonction du type d'erreur

    Parameters:
        error (Exception): L'erreur rencontrée
        context (str): Le contexte dans lequel l'erreur s'est produite
    """
    error_str = str(error).lower()

    # Erreurs d'authentification Spotify
    if "authentication" in error_str or "unauthorized" in error_str or "token" in error_str:
        st.info("""
        ### Suggestions pour résoudre ce problème d'authentification:

        1. **Essayez de vous reconnecter** en cliquant sur "Forcer nouvelle authentification"
        2. **Vérifiez que vos identifiants API Spotify sont corrects** dans le fichier `.env`
        3. **Assurez-vous que l'URI de redirection** dans le tableau de bord Spotify Developer est exactement `http://127.0.0.1:8080`
        """)

    # Erreurs de connexion réseau
    elif "connection" in error_str or "timeout" in error_str or "network" in error_str:
        st.info("""
        ### Suggestions pour résoudre ce problème de connexion:

        1. **Vérifiez votre connexion Internet**
        2. **Réessayez dans quelques minutes** (les serveurs Spotify peuvent être temporairement indisponibles)
        3. **Vérifiez que votre pare-feu** n'empêche pas l'application de se connecter à Internet
        """)

    # Erreurs de récursion
    elif "recursion" in error_str:
        st.info("""
        ### Suggestions pour résoudre cette erreur de récursion:

        1. **Supprimez les fichiers de données existants** dans la section Paramètres
        2. **Redémarrez l'application**
        3. **Réextrayez vos données** avec une quantité plus limitée de playlists
        """)

    # Erreurs de mémoire
    elif "memory" in error_str or "memoryerror" in error_str:
        st.info("""
        ### Suggestions pour résoudre ce problème de mémoire:

        1. **Fermez d'autres applications** pour libérer de la mémoire
        2. **Redémarrez l'application**
        3. **Limitez la quantité de données à analyser** en sélectionnant moins de playlists
        """)

    # Erreurs générales
    else:
        st.info("""
        ### Suggestions générales:

        1. **Redémarrez l'application**
        2. **Vérifiez que vos fichiers de configuration sont corrects**
        3. **Assurez-vous d'avoir installé toutes les dépendances** avec `pip install -r requirements.txt`
        4. **Si le problème persiste**, consultez les logs dans le dossier `data/logs`
        """)

    # Bouton pour retourner à la page d'accueil
    if st.button("Retourner à l'accueil"):
        st.session_state.page = "accueil"
        st.experimental_rerun()


def display_maintenance_message():
    """
    Affiche un message de maintenance pour les fonctionnalités en développement
    """
    st.info("""
    ### Fonctionnalité en cours de développement

    Cette fonctionnalité est actuellement en cours de développement et sera disponible prochainement.

    Merci de votre patience !
    """)

    if st.button("Retourner à l'accueil", key="back_home_maintenance"):
        st.session_state.page = "accueil"
        st.experimental_rerun()


def is_development_mode():
    """
    Vérifie si l'application est en mode développement

    Returns:
        bool: True si l'application est en mode développement
    """
    return os.environ.get("MELODIA_DEV_MODE", "false").lower() == "true"


def show_debug_info():
    """
    Affiche des informations de débogage si l'application est en mode développement
    """
    if not is_development_mode():
        return

    with st.expander("Informations de débogage (Mode DEV)"):
        st.write("### État de la session")
        st.write(dict(st.session_state))

        st.write("### Environnement")
        import sys
        st.write(f"Python: {sys.version}")
        st.write(f"Streamlit: {st.__version__}")

        st.write("### Fichiers de données")
        for file in os.listdir(DATA_DIR):
            file_path = os.path.join(DATA_DIR, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path)
                size_str = f"{size} octets"
                if size > 1024:
                    size_str = f"{size / 1024:.2f} Ko"
                if size > 1024 * 1024:
                    size_str = f"{size / (1024 * 1024):.2f} Mo"
                st.write(f"- {file}: {size_str}")


def try_catch_decorator(context="general"):
    """
    Décorateur pour gérer les exceptions dans les fonctions

    Parameters:
        context (str): Le contexte dans lequel la fonction s'exécute

    Returns:
        function: Fonction décorée avec gestion d'erreurs
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handle_error(e, context)

        return wrapper

    return decorator