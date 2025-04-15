import pandas as pd
import os
from config import DATA_DIR
from spotify_auth import SpotifyAuth

class TopArtistsAnalyzer:
    def __init__(self, force_new_auth=False):
        """Initialise l'analyseur des artistes les plus écoutés"""
        auth = SpotifyAuth.get_instance(force_new_auth)
        self.sp = auth.get_spotify_client()
        self.user_id = auth.user_id
        self.user_name = auth.user_name

    def get_top_artists(self, time_range='medium_term', limit=10):
        """
        Récupère les artistes les plus écoutés

        Parameters:
            time_range (str): Période d'analyse ('short_term': 4 semaines, 'medium_term': 6 mois, 'long_term': plusieurs années)
            limit (int): Nombre d'artistes à récupérer

        Returns:
            list: Liste des artistes les plus écoutés
        """
        try:
            results = self.sp.current_user_top_artists(time_range=time_range, limit=limit)

            # Créer une liste d'artistes
            artists = []
            for i, item in enumerate(results['items']):
                artist = {
                    'position': i + 1,
                    'id': item['id'],
                    'name': item['name'],
                    'popularity': item['popularity'],
                    'genres': item['genres'],
                    'image_url': item['images'][0]['url'] if item['images'] else None,
                    'uri': item['uri']
                }
                artists.append(artist)

            return artists
        except Exception as e:
            print(f"Erreur lors de la récupération des artistes les plus écoutés: {e}")
            return []

    def get_top_tracks(self, time_range='medium_term', limit=50):
        """
        Récupère les titres les plus écoutés

        Parameters:
            time_range (str): Période d'analyse
            limit (int): Nombre de titres à récupérer

        Returns:
            list: Liste des titres les plus écoutés
        """
        try:
            results = self.sp.current_user_top_tracks(time_range=time_range, limit=limit)

            # Créer une liste de titres
            tracks = []
            for i, item in enumerate(results['items']):
                track = {
                    'position': i + 1,
                    'id': item['id'],
                    'name': item['name'],
                    'artist': item['artists'][0]['name'],
                    'artist_id': item['artists'][0]['id'],
                    'album': item['album']['name'],
                    'popularity': item['popularity'],
                    'uri': item['uri']
                }
                tracks.append(track)

            return tracks
        except Exception as e:
            print(f"Erreur lors de la récupération des titres les plus écoutés: {e}")
            return []

    def create_top_artists_playlist(self, time_range='medium_term', tracks_per_artist=2, total_limit=30):
        """
        Crée une playlist avec les titres des artistes les plus écoutés

        Parameters:
            time_range (str): Période d'analyse
            tracks_per_artist (int): Nombre de titres à inclure par artiste
            total_limit (int): Limite totale de titres dans la playlist

        Returns:
            dict: Informations sur la playlist créée
        """
        try:
            # Obtenir les artistes les plus écoutés
            top_artists = self.get_top_artists(time_range=time_range, limit=min(15, total_limit // tracks_per_artist))

            if not top_artists:
                return None

            # Pour chaque artiste, récupérer ses meilleurs titres
            track_uris = []
            for artist in top_artists:
                artist_tracks = self.sp.artist_top_tracks(artist['id'], country='FR')['tracks']
                # Prendre les N meilleurs titres de chaque artiste
                for track in artist_tracks[:tracks_per_artist]:
                    track_uris.append(track['uri'])
                    if len(track_uris) >= total_limit:
                        break
                if len(track_uris) >= total_limit:
                    break

            # Créer un nom de playlist basé sur la période
            time_range_names = {
                'short_term': 'dernières semaines',
                'medium_term': '6 derniers mois',
                'long_term': 'de tous les temps'
            }
            playlist_name = f"Top Artistes des {time_range_names.get(time_range, time_range)}"

            # Créer la playlist
            playlist = self.sp.user_playlist_create(
                user=self.user_id,
                name=playlist_name,
                public=False,
                description=f"Artistes les plus écoutés des {time_range_names.get(time_range, time_range)} - Créé par Music Analyzer"
            )

            # Ajouter les titres à la playlist
            if track_uris:
                # Ajouter par lots de 100 maximum (limite de l'API)
                for i in range(0, len(track_uris), 100):
                    batch = track_uris[i:i + 100]
                    self.sp.playlist_add_items(playlist['id'], batch)

            return {
                'id': playlist['id'],
                'name': playlist['name'],
                'url': playlist['external_urls']['spotify'],
                'tracks_count': len(track_uris)
            }
        except Exception as e:
            print(f"Erreur lors de la création de la playlist: {e}")
            return None

    def get_recently_played_tracks(self, limit=50):
        """
        Récupère les titres récemment écoutés

        Parameters:
            limit (int): Nombre de titres à récupérer

        Returns:
            list: Liste des titres récemment écoutés
        """
        try:
            results = self.sp.current_user_recently_played(limit=limit)

            # Créer une liste de titres
            tracks = []
            for i, item in enumerate(results['items']):
                track = item['track']
                played_at = item['played_at']
                track_info = {
                    'position': i + 1,
                    'id': track['id'],
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'played_at': played_at,
                    'uri': track['uri']
                }
                tracks.append(track_info)

            return tracks
        except Exception as e:
            print(f"Erreur lors de la récupération des titres récemment écoutés: {e}")
            return []

    def save_top_artists_data(self, time_range='medium_term'):
        """
        Sauvegarde les données des artistes et titres les plus écoutés

        Parameters:
            time_range (str): Période d'analyse

        Returns:
            tuple: Chemins vers les fichiers sauvegardés
        """
        try:
            # Récupérer les données
            top_artists = self.get_top_artists(time_range=time_range, limit=50)
            top_tracks = self.get_top_tracks(time_range=time_range, limit=50)
            recently_played = self.get_recently_played_tracks(limit=50)

            # Convertir en DataFrames
            artists_df = pd.DataFrame(top_artists)
            tracks_df = pd.DataFrame(top_tracks)
            recent_df = pd.DataFrame(recently_played)

            # Créer un sous-répertoire pour ces données
            top_dir = os.path.join(DATA_DIR, "top_data")
            os.makedirs(top_dir, exist_ok=True)

            # Sauvegarder les DataFrames
            time_suffix = f"_{time_range}"
            artists_path = os.path.join(top_dir, f"top_artists{time_suffix}.csv")
            tracks_path = os.path.join(top_dir, f"top_tracks{time_suffix}.csv")
            recent_path = os.path.join(top_dir, "recently_played.csv")

            if not artists_df.empty:
                artists_df.to_csv(artists_path, index=False)
                print(f"Top artistes sauvegardés dans: {artists_path}")

            if not tracks_df.empty:
                tracks_df.to_csv(tracks_path, index=False)
                print(f"Top titres sauvegardés dans: {tracks_path}")

            if not recent_df.empty:
                recent_df.to_csv(recent_path, index=False)
                print(f"Titres récemment écoutés sauvegardés dans: {recent_path}")

            return artists_path, tracks_path, recent_path
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des données: {e}")
            return None, None, None


def analyze_top_artists(force_new_auth=False):
    """
    Fonction principale pour analyser les artistes les plus écoutés

    Parameters:
        force_new_auth (bool): Si True, force une nouvelle authentification

    Returns:
        dict: Résultats de l'analyse
    """
    try:
        analyzer = TopArtistsAnalyzer(force_new_auth=force_new_auth)

        # Récupérer les artistes les plus écoutés pour différentes périodes
        short_term = analyzer.get_top_artists(time_range='short_term', limit=10)
        medium_term = analyzer.get_top_artists(time_range='medium_term', limit=10)
        long_term = analyzer.get_top_artists(time_range='long_term', limit=10)

        # Sauvegarder les données
        analyzer.save_top_artists_data(time_range='medium_term')

        return {
            'short_term': short_term,
            'medium_term': medium_term,
            'long_term': long_term
        }
    except Exception as e:
        print(f"Erreur lors de l'analyse des artistes les plus écoutés: {e}")
        return None


if __name__ == "__main__":
    # Test du module
    results = analyze_top_artists()

    if results:
        print("\nVos artistes les plus écoutés:")

        print("\nDernières semaines:")
        for artist in results['short_term']:
            print(f"{artist['position']}. {artist['name']} (Popularité: {artist['popularity']})")

        print("\n6 derniers mois:")
        for artist in results['medium_term']:
            print(f"{artist['position']}. {artist['name']} (Popularité: {artist['popularity']})")

        print("\nDe tous les temps:")
        for artist in results['long_term']:
            print(f"{artist['position']}. {artist['name']} (Popularité: {artist['popularity']})")

        # Créer une playlist
        analyzer = TopArtistsAnalyzer()
        playlist = analyzer.create_top_artists_playlist(time_range='medium_term')

        if playlist:
            print(f"\nPlaylist créée: {playlist['name']}")
            print(f"URL: {playlist['url']}")
            print(f"Nombre de titres: {playlist['tracks_count']}")