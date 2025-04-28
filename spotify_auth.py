import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, DATA_DIR

# Scope complet pour toutes les fonctionnalités
SPOTIFY_FULL_SCOPE = "user-library-read user-top-read playlist-read-private playlist-modify-private user-read-recently-played"

class SpotifyAuth:
    _instance = None

    @classmethod
    def get_instance(cls, force_new_auth=False):
        """Implémentation du pattern Singleton pour assurer une seule instance de connexion"""
        if cls._instance is None:
            cls._instance = cls(force_new_auth)
        elif force_new_auth:
            cls._instance = cls(force_new_auth)
        return cls._instance

    def __init__(self, force_new_auth=False):
        """Initialise la connexion à l'API Spotify"""
        self.cache_path = os.path.join(DATA_DIR, ".spotify_cache")

        # Si on force une nouvelle authentification, supprimer le cache existant
        if force_new_auth and os.path.exists(self.cache_path):
            try:
                os.remove(self.cache_path)
                print("Cache d'authentification précédent supprimé.")
            except Exception as e:
                print(f"Impossible de supprimer le cache: {e}")

        # Utiliser exactement l'URI configuré dans le tableau de bord Spotify
        redirect_uri = SPOTIFY_REDIRECT_URI
        print(f"Utilisation de l'URI de redirection: {redirect_uri}")

        # Création du gestionnaire d'authentification
        self.auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=redirect_uri,
            scope=SPOTIFY_FULL_SCOPE,
            cache_path=self.cache_path,
            show_dialog=force_new_auth,
            open_browser=True
        )

        self.sp = spotipy.Spotify(auth_manager=self.auth_manager)

        # Récupérer les informations de l'utilisateur pour confirmer l'authentification
        try:
            user_info = self.sp.current_user()
            self.user_id = user_info['id']
            self.user_name = user_info.get('display_name', self.user_id)
            print(f"Connecté à Spotify en tant que: {self.user_name} ({self.user_id})")
        except Exception as e:
            print(f"Erreur lors de la récupération des informations utilisateur: {e}")
            raise

    def get_spotify_client(self):
        """Retourne le client Spotify connecté"""
        return self.sp

    def logout(self):
        """Déconnecte l'utilisateur en supprimant le fichier cache et l'instance"""
        try:
            if os.path.exists(self.cache_path):
                os.remove(self.cache_path)
                print(f"Fichier cache supprimé: {os.path.basename(self.cache_path)}")

            # Réinitialiser l'instance Singleton
            SpotifyAuth._instance = None

            return True
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {e}")
            return False