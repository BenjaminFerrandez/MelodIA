import pandas as pd
import time
import os
from config import DATA_DIR
from spotify_auth import SpotifyAuth

class SpotifyConnector:
    def __init__(self, force_new_auth=False):
        """Initialise la connexion à l'API Spotify"""
        auth = SpotifyAuth.get_instance(force_new_auth)
        self.sp = auth.get_spotify_client()
        self.user_id = auth.user_id
        self.user_name = auth.user_name

    def get_playlists(self):
        """Récupère toutes les playlists de l'utilisateur"""
        results = self.sp.current_user_playlists()
        playlists = []

        while results:
            playlists.extend(results['items'])
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None

        return pd.DataFrame([
            {
                'playlist_id': playlist['id'],
                'playlist_name': playlist['name'],
                'playlist_tracks': playlist['tracks']['total'],
                'playlist_owner': playlist['owner']['display_name']
            }
            for playlist in playlists
        ])

    def get_playlist_tracks(self, playlist_id, playlist_name):
        """Récupère tous les titres d'une playlist spécifique"""
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []

        while results:
            for item in results['items']:
                # Vérifier si l'élément contient un track (pour éviter les podcasts)
                if item['track'] and item['track']['id']:
                    track = item['track']

                    # Récupérer les artistes (il peut y en avoir plusieurs)
                    artists = ', '.join([artist['name'] for artist in track['artists']])

                    # Récupérer la date de sortie
                    album = track['album']
                    release_date = album['release_date'] if 'release_date' in album else None

                    tracks.append({
                        'track_id': track['id'],
                        'track_name': track['name'],
                        'artist_name': artists,
                        'album_name': album['name'],
                        'release_date': release_date,
                        'popularity': track['popularity'],
                        'playlist_id': playlist_id,
                        'playlist_name': playlist_name
                    })

            if results['next']:
                results = self.sp.next(results)
            else:
                results = None

        return pd.DataFrame(tracks)

    def get_all_playlist_tracks(self):
        """Récupère les titres de toutes les playlists de l'utilisateur"""
        playlists_df = self.get_playlists()
        all_tracks = []

        print(f"Récupération des titres pour {len(playlists_df)} playlists...")

        for index, playlist in playlists_df.iterrows():
            print(f"Traitement de la playlist: {playlist['playlist_name']} ({playlist['playlist_tracks']} titres)")
            tracks = self.get_playlist_tracks(playlist['playlist_id'], playlist['playlist_name'])
            all_tracks.append(tracks)

            # Respecter les limites d'API en pause entre les requêtes volumineuses
            if playlist['playlist_tracks'] > 50:
                time.sleep(1)

        # Combiner tous les titres en un seul DataFrame
        if all_tracks:
            return pd.concat(all_tracks, ignore_index=True)
        else:
            return pd.DataFrame()

    def get_audio_features(self, tracks_df, batch_size=50):
        """Récupère les caractéristiques audio pour une liste de titres"""
        if tracks_df.empty:
            return tracks_df

        # Récupérer uniquement les IDs uniques pour éviter de traiter les doublons
        unique_track_ids = tracks_df['track_id'].unique().tolist()

        features = []

        print(f"Récupération des caractéristiques audio pour {len(unique_track_ids)} titres uniques...")

        # Traitement par lots plus petits (50 au lieu de 100) pour respecter les limites de l'API Spotify
        for i in range(0, len(unique_track_ids), batch_size):
            batch_ids = unique_track_ids[i:i + batch_size]

            try:
                batch_features = self.sp.audio_features(batch_ids)

                if batch_features:
                    features.extend([f for f in batch_features if f])  # Filtrer les valeurs None

                # Pause plus longue entre les requêtes pour éviter les limitations
                time.sleep(1)

            except Exception as e:
                print(f"Erreur lors de la récupération des caractéristiques pour le lot {i // batch_size + 1}: {e}")
                # Réduire davantage la taille du lot en cas d'erreur
                if batch_size > 10:
                    smaller_batch_size = 10
                    print(f"Tentative avec une taille de lot réduite ({smaller_batch_size})...")
                    # Traiter le lot problématique avec une taille réduite
                    for j in range(0, len(batch_ids), smaller_batch_size):
                        smaller_batch = batch_ids[j:j + smaller_batch_size]
                        try:
                            smaller_features = self.sp.audio_features(smaller_batch)
                            if smaller_features:
                                features.extend([f for f in smaller_features if f])
                            time.sleep(1.5)  # Pause plus longue pour les lots réduits
                        except Exception as inner_e:
                            print(f"Échec également avec une taille réduite: {inner_e}")
                            # Continuer avec le prochain lot, nous avons fait de notre mieux

        # Convertir en DataFrame
        features_df = pd.DataFrame(features)

        # Simplifier le DataFrame en gardant seulement les colonnes pertinentes
        if not features_df.empty:
            features_df = features_df[[
                'id', 'danceability', 'energy', 'key', 'loudness',
                'mode', 'speechiness', 'acousticness', 'instrumentalness',
                'liveness', 'valence', 'tempo'
            ]]

            # Renommer la colonne 'id' pour faciliter la fusion
            features_df = features_df.rename(columns={'id': 'track_id'})

        return features_df

    def save_data(self, tracks_df, features_df=None):
        """Sauvegarde les données extraites"""
        # Sauvegarder les titres
        tracks_path = os.path.join(DATA_DIR, "tracks.csv")
        tracks_df.to_csv(tracks_path, index=False)
        print(f"Titres sauvegardés dans: {tracks_path}")

        # Sauvegarder les caractéristiques audio si disponibles
        if features_df is not None and not features_df.empty:
            features_path = os.path.join(DATA_DIR, "audio_features.csv")
            features_df.to_csv(features_path, index=False)
            print(f"Caractéristiques audio sauvegardées dans: {features_path}")

            # Fusionner et sauvegarder un dataset complet
            merged_df = pd.merge(tracks_df, features_df, on='track_id', how='left')
            merged_path = os.path.join(DATA_DIR, "tracks_with_features.csv")
            merged_df.to_csv(merged_path, index=False)
            print(f"Dataset complet sauvegardé dans: {merged_path}")

        return True


def extract_spotify_data(force_new_auth=False):
    """
    Fonction principale pour extraire les données depuis Spotify

    Parameters:
        force_new_auth (bool): Si True, force une nouvelle authentification
    """
    try:
        connector = SpotifyConnector(force_new_auth=force_new_auth)

        # Récupérer toutes les playlists et leurs titres
        tracks_df = connector.get_all_playlist_tracks()

        if not tracks_df.empty:
            print(f"Récupéré {len(tracks_df)} titres au total.")

            # Sauvegarder les titres même si nous n'avons pas encore les caractéristiques audio
            # Cela nous permettra de continuer même si l'extraction des caractéristiques échoue
            tracks_path = os.path.join(DATA_DIR, "tracks.csv")
            tracks_df.to_csv(tracks_path, index=False)
            print(f"Titres sauvegardés dans: {tracks_path}")

            try:
                # Récupérer les caractéristiques audio
                features_df = connector.get_audio_features(tracks_df)

                # Sauvegarder les caractéristiques audio et le dataset complet
                if features_df is not None and not features_df.empty:
                    features_path = os.path.join(DATA_DIR, "audio_features.csv")
                    features_df.to_csv(features_path, index=False)
                    print(f"Caractéristiques audio sauvegardées dans: {features_path}")

                    # Fusionner et sauvegarder un dataset complet
                    merged_df = pd.merge(tracks_df, features_df, on='track_id', how='left')
                    merged_path = os.path.join(DATA_DIR, "tracks_with_features.csv")
                    merged_df.to_csv(merged_path, index=False)
                    print(f"Dataset complet sauvegardé dans: {merged_path}")
                else:
                    print(
                        "Avertissement: Caractéristiques audio non récupérées. Seules les informations de base des titres sont disponibles.")

                return tracks_df, features_df

            except Exception as audio_error:
                print(f"Erreur lors de la récupération des caractéristiques audio: {audio_error}")
                print("Continuation avec uniquement les informations de base des titres.")
                return tracks_df, None
        else:
            print("Aucun titre trouvé. Vérifiez vos playlists.")
            return None, None

    except Exception as e:
        print(f"Erreur lors de l'extraction des données Spotify: {e}")
        return None, None


if __name__ == "__main__":
    # Test du module
    tracks, features = extract_spotify_data()
    if tracks is not None:
        print(
            f"Extraction réussie: {len(tracks)} titres avec {len(features) if features is not None else 0} caractéristiques audio.")