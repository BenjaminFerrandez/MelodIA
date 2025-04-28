import pandas as pd
import os
import time
from config import DATA_DIR
from spotify_auth import SpotifyAuth


def export_playlist_to_csv(playlist_df, name="custom_playlist"):
    """
    Exporte une playlist en CSV pour pouvoir l'importer ailleurs

    Parameters:
        playlist_df (DataFrame): DataFrame contenant les titres de la playlist
        name (str): Nom de la playlist pour le fichier d'export

    Returns:
        str: Chemin vers le fichier CSV exporté
    """
    if playlist_df is None or playlist_df.empty:
        print("Aucune donnée à exporter.")
        return None

    try:
        # Créer un sous-répertoire pour les playlists exportées
        export_dir = os.path.join(DATA_DIR, "exported_playlists")
        os.makedirs(export_dir, exist_ok=True)

        # Sanitize le nom de fichier
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')

        # Générer le nom de fichier avec timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.csv"

        export_path = os.path.join(export_dir, filename)

        # Exporter au format CSV
        playlist_df.to_csv(export_path, index=False)
        print(f"Playlist exportée: {export_path}")

        return export_path
    except Exception as e:
        print(f"Erreur lors de l'exportation de la playlist: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def create_spotify_playlist(playlist_name, playlist_description, track_ids, is_public=False):
    """
    Crée une nouvelle playlist Spotify et y ajoute les titres spécifiés

    Parameters:
        playlist_name (str): Nom de la playlist
        playlist_description (str): Description de la playlist
        track_ids (list): Liste des IDs de titres Spotify à ajouter
        is_public (bool): Si la playlist doit être publique (False par défaut)

    Returns:
        dict: Informations sur la playlist créée (id, name, url, tracks_count)
    """
    try:
        # Obtenir une instance du client Spotify
        auth = SpotifyAuth.get_instance()
        sp = auth.get_spotify_client()
        user_id = auth.user_id

        # Créer la playlist
        playlist = sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=is_public,
            description=f"{playlist_description} - Créé par MelodIA"
        )

        # Ajouter les titres à la playlist
        if track_ids:
            # Ajouter par lots de 100 maximum (limite de l'API)
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i:i + 100]
                sp.playlist_add_items(playlist['id'], batch)

                # Pause pour respecter les limites de l'API
                time.sleep(1)

        return {
            'id': playlist['id'],
            'name': playlist['name'],
            'url': playlist['external_urls']['spotify'],
            'tracks_count': len(track_ids)
        }
    except Exception as e:
        print(f"Erreur lors de la création de la playlist Spotify: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def export_dataframe_to_spotify(df, playlist_name, playlist_description=""):
    """
    Exporte un DataFrame de titres vers une playlist Spotify

    Parameters:
        df (DataFrame): DataFrame contenant les titres à exporter (doit avoir une colonne 'track_id')
        playlist_name (str): Nom de la playlist
        playlist_description (str): Description de la playlist

    Returns:
        dict: Informations sur la playlist créée
    """
    try:
        if df is None or df.empty:
            print("DataFrame vide, impossible de créer une playlist.")
            return None

        if 'track_id' not in df.columns:
            print("La colonne 'track_id' est requise dans le DataFrame.")
            return None

        # Extraire les IDs de titres
        track_ids = df['track_id'].unique().tolist()

        if not track_ids:
            print("Aucun ID de titre valide trouvé dans le DataFrame.")
            return None

        # Créer la playlist
        return create_spotify_playlist(playlist_name, playlist_description, track_ids)
    except Exception as e:
        print(f"Erreur lors de l'exportation vers Spotify: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def export_recommended_tracks_to_spotify(recommendation_type, data, custom_name=None):
    """
    Exporte des titres recommandés vers une playlist Spotify

    Parameters:
        recommendation_type (str): Type de recommandation ('similar', 'mood', 'discover')
        data (dict): Données de la recommandation
        custom_name (str): Nom personnalisé pour la playlist

    Returns:
        dict: Informations sur la playlist créée
    """
    try:
        if not data or 'tracks' not in data or not data['tracks']:
            print("Données de recommandation invalides.")
            return None

        # Préparer le nom et la description de la playlist
        current_date = time.strftime("%d/%m/%Y")

        if recommendation_type == 'similar':
            source_track = data.get('source_track', {})
            name = custom_name or f"MelodIA - Similaire à {source_track.get('name', 'Unknown')}"
            description = f"Titres similaires à {source_track.get('name', 'Unknown')} de {source_track.get('artist', 'Unknown')} | Créé le {current_date}"
        elif recommendation_type == 'mood':
            mood = data.get('mood', 'unknown')
            mood_names = {
                'happy': 'Joyeuse',
                'energetic': 'Énergique',
                'calm': 'Calme',
                'melancholic': 'Mélancolique'
            }
            mood_name = mood_names.get(mood, mood)
            name = custom_name or f"MelodIA - Playlist {mood_name}"
            description = f"Playlist {mood_name} générée automatiquement | Créé le {current_date}"
        elif recommendation_type == 'discover':
            name = custom_name or f"MelodIA - Découvertes"
            description = f"Découvertes musicales basées sur vos goûts | Créé le {current_date}"
        else:
            name = custom_name or "MelodIA - Playlist personnalisée"
            description = f"Playlist personnalisée | Créé le {current_date}"

        # Extraire les IDs des titres
        track_ids = [track['id'] for track in data['tracks'] if 'id' in track]

        if not track_ids:
            print("Aucun ID de titre trouvé dans les données de recommandation.")
            return None

        # Créer la playlist
        return create_spotify_playlist(name, description, track_ids)
    except Exception as e:
        print(f"Erreur lors de l'exportation des recommandations vers Spotify: {e}")
        import traceback
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    # Test de la fonction d'exportation CSV
    test_df = pd.DataFrame({
        'track_id': ['1', '2', '3'],
        'track_name': ['Song 1', 'Song 2', 'Song 3'],
        'artist_name': ['Artist 1', 'Artist 2', 'Artist 3']
    })

    export_path = export_playlist_to_csv(test_df, "test_playlist")
    if export_path:
        print(f"Test d'exportation CSV réussi: {export_path}")
    else:
        print("Échec du test d'exportation CSV")