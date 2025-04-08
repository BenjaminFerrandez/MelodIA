import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

# Identifiants Spotify API
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

# Étendue des permissions Spotify requises
SPOTIFY_SCOPE = "user-library-read user-top-read playlist-read-private"

# Dossier pour sauvegarder les données
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Vérification de la configuration
if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET]):
    print("ATTENTION: Les identifiants Spotify API ne sont pas configurés!")
    print("Créez un fichier .env avec SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET")