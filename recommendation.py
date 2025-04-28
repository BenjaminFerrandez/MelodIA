import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from config import DATA_DIR


def load_categorized_data():
    """Charge les données catégorisées pour les recommandations"""
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

    try:
        if os.path.exists(categorized_path):
            return pd.read_csv(categorized_path, low_memory=False)
        else:
            # Si les données catégorisées ne sont pas disponibles, exécuter l'analyse
            print("Données catégorisées non trouvées, exécution de l'analyse...")
            # Importation différée pour éviter les importations circulaires
            from data_analysis import analyze_data
            _, _, df = analyze_data(max_recursion_depth=2000)
            return df
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")
        # Tentative de récupération avec un ancien fichier de sauvegarde
        backup_path = os.path.join(DATA_DIR, "tracks.csv")
        if os.path.exists(backup_path):
            print("Tentative de chargement depuis les données brutes...")
            try:
                return pd.read_csv(backup_path, low_memory=False)
            except Exception as e2:
                print(f"Échec de la récupération depuis les données brutes: {e2}")
        return None


def get_similar_tracks(track_id, df, n=5):
    """
    Recommande des titres similaires basés sur les caractéristiques audio

    Parameters:
        track_id (str): ID du titre pour lequel trouver des recommandations
        df (DataFrame): DataFrame contenant les données des titres
        n (int): Nombre de recommandations à retourner

    Returns:
        DataFrame: DataFrame contenant les titres recommandés
    """
    if df is None or df.empty:
        print("Données non disponibles")
        return None

    try:
        if track_id not in df['track_id'].values:
            print(f"Titre avec ID {track_id} non trouvé dans les données.")
            return None

        # Caractéristiques audio à utiliser pour la similarité
        audio_features = ['danceability', 'energy', 'valence', 'acousticness',
                          'instrumentalness', 'liveness', 'speechiness']

        # Vérifier quelles caractéristiques sont disponibles
        available_features = [f for f in audio_features if f in df.columns]

        if len(available_features) < 2:
            print("Pas assez de caractéristiques audio disponibles pour les recommandations.")
            return None

        # Extraire les caractéristiques et s'assurer qu'elles sont numériques
        features_df = df[available_features].copy()
        for feature in available_features:
            features_df[feature] = pd.to_numeric(features_df[feature], errors='coerce')
            features_df[feature].fillna(features_df[feature].mean(), inplace=True)

        features_matrix = features_df.values

        # Normaliser les caractéristiques
        scaler = MinMaxScaler()
        features_matrix_scaled = scaler.fit_transform(features_matrix)

        # Trouver l'index du titre cible
        track_index = df[df['track_id'] == track_id].index[0]

        # Calculer la similarité cosinus
        similarities = cosine_similarity([features_matrix_scaled[track_index]], features_matrix_scaled)[0]

        # Obtenir les indices des titres les plus similaires (sauf le titre lui-même)
        similar_indices = similarities.argsort()[::-1][1:n + 1]

        # Créer un DataFrame avec les recommandations
        recommendations = df.iloc[similar_indices].copy()

        # Ajouter un score de similarité
        recommendations['similarity_score'] = similarities[similar_indices]

        # Trier par score de similarité décroissant
        recommendations = recommendations.sort_values('similarity_score', ascending=False)

        # Sélectionner les colonnes à retourner
        result_columns = ['track_id', 'track_name', 'artist_name', 'album_name',
                          'similarity_score'] + available_features

        # Ajouter la playlist si disponible
        if 'playlist_name' in recommendations.columns:
            result_columns.insert(4, 'playlist_name')

        # S'assurer que toutes les colonnes existent
        result_columns = [col for col in result_columns if col in recommendations.columns]

        return recommendations[result_columns]
    except Exception as e:
        print(f"Erreur lors de la recherche de titres similaires: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def generate_playlist_by_mood(mood, df, size=15, min_energy=None, min_danceability=None,
                              min_valence=None, max_acousticness=None):
    """
    Génère une playlist basée sur l'ambiance souhaitée avec paramètres personnalisables

    Parameters:
        mood (str): Ambiance souhaitée ('happy', 'energetic', 'calm', 'melancholic')
        df (DataFrame): DataFrame contenant les données des titres
        size (int): Nombre de titres dans la playlist
        min_energy (float): Énergie minimale (0-1)
        min_danceability (float): Dansabilité minimale (0-1)
        min_valence (float): Positivité minimale (0-1)
        max_acousticness (float): Acoustique maximale (0-1)

    Returns:
        DataFrame: DataFrame contenant les titres de la playlist
    """
    if df is None or df.empty:
        return None

    try:
        # Vérifier si les caractéristiques nécessaires sont disponibles
        required_features = ['danceability', 'energy', 'valence', 'acousticness']
        available_features = [f for f in required_features if f in df.columns]

        if len(available_features) < 2:
            print("Caractéristiques insuffisantes pour la génération de playlist.")
            return None

        # S'assurer que les caractéristiques sont numériques
        numeric_df = df.copy()
        for feature in available_features:
            numeric_df[feature] = pd.to_numeric(numeric_df[feature], errors='coerce')
            numeric_df[feature].fillna(numeric_df[feature].mean(), inplace=True)

        # Définir les critères par défaut pour chaque ambiance
        mood_criteria = {
            'happy': {'valence': 0.7, 'energy': 0.6, 'danceability': 0.5},
            'energetic': {'energy': 0.8, 'danceability': 0.7, 'valence': 0.5},
            'calm': {'energy': 0.4, 'acousticness': 0.7, 'valence': 0.5},
            'melancholic': {'valence': 0.4, 'energy': 0.4, 'acousticness': 0.6}
        }

        if mood.lower() not in mood_criteria:
            print(f"Ambiance {mood} non reconnue. Options disponibles: {list(mood_criteria.keys())}")
            return None

        # Appliquer les critères de filtre selon l'ambiance choisie, modifiés par les paramètres utilisateur
        criteria = mood_criteria[mood.lower()].copy()

        # Remplacer par les paramètres personnalisés si fournis
        if min_energy is not None and 'energy' in available_features:
            criteria['energy'] = min_energy
        if min_danceability is not None and 'danceability' in available_features:
            criteria['danceability'] = min_danceability
        if min_valence is not None and 'valence' in available_features:
            criteria['valence'] = min_valence
        if max_acousticness is not None and 'acousticness' in available_features:
            # Pour acousticness, c'est un max, pas un min
            criteria['acousticness'] = max_acousticness

        # Filtrer les titres selon les critères
        filtered_df = numeric_df.copy()

        for feature, threshold in criteria.items():
            if feature in available_features:
                if feature == 'acousticness':
                    # Pour acousticness, on veut généralement un maximum (sauf pour 'calm')
                    if mood.lower() == 'calm':
                        filtered_df = filtered_df[filtered_df[feature] >= threshold]
                    else:
                        filtered_df = filtered_df[filtered_df[feature] <= threshold]
                else:
                    filtered_df = filtered_df[filtered_df[feature] >= threshold]

        # Si pas assez de titres après filtrage, assouplir les critères
        if len(filtered_df) < size:
            print(f"Seulement {len(filtered_df)} titres correspondent aux critères stricts. Assouplissement...")

            # Réduire tous les seuils de 20%
            filtered_df = numeric_df.copy()
            for feature, threshold in criteria.items():
                if feature in available_features:
                    if feature == 'acousticness' and mood.lower() != 'calm':
                        filtered_df = filtered_df[filtered_df[feature] <= threshold * 1.2]
                    else:
                        filtered_df = filtered_df[filtered_df[feature] >= threshold * 0.8]

        # Si toujours pas assez, utiliser une approche basée sur un score
        if len(filtered_df) < size:
            print(f"Après assouplissement: {len(filtered_df)} titres trouvés. Utilisation d'une approche par score...")

            # Calculer un score pour chaque titre basé sur les critères
            numeric_df['mood_score'] = 0

            for feature, threshold in criteria.items():
                if feature in available_features:
                    if feature == 'acousticness' and mood.lower() != 'calm':
                        # Pour acousticness (sauf 'calm'), plus la valeur est proche de 0, mieux c'est
                        numeric_df['mood_score'] += (1 - numeric_df[feature]).clip(lower=0)
                    else:
                        # Pour les autres, plus la valeur est élevée, mieux c'est
                        numeric_df['mood_score'] += numeric_df[feature]

            # Trier par score décroissant et prendre les meilleurs
            filtered_df = numeric_df.sort_values('mood_score', ascending=False).head(size)

        # Sélection des titres pour la playlist
        if len(filtered_df) > size:
            playlist = filtered_df.sample(size)
        else:
            playlist = filtered_df

        # Sélectionner les colonnes à retourner
        result_columns = ['track_id', 'track_name', 'artist_name', 'album_name']

        # Ajouter playlist_name si disponible
        if 'playlist_name' in playlist.columns:
            result_columns.append('playlist_name')

        # Ajouter les caractéristiques disponibles
        result_columns.extend([f for f in available_features if f in playlist.columns])

        # S'assurer que toutes les colonnes existent
        result_columns = [col for col in result_columns if col in playlist.columns]

        return playlist[result_columns]
    except Exception as e:
        print(f"Erreur lors de la génération de la playlist par ambiance: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def discover_new_music(df, n=10, discovery_type='mixed'):
    """
    Recommande des titres peu connus ou récemment ajoutés à la bibliothèque

    Parameters:
        df (DataFrame): DataFrame contenant les données des titres
        n (int): Nombre de titres à recommander
        discovery_type (str): Type de découverte ('artists', 'popular', 'mixed')

    Returns:
        DataFrame: DataFrame contenant les découvertes recommandées
    """
    if df is None or df.empty:
        return None

    try:
        # Définir ce qu'est un titre "peu connu" dans la bibliothèque selon le type de découverte
        has_popularity = 'popularity' in df.columns
        has_playlists = 'playlist_name' in df.columns

        if not (has_popularity or has_playlists):
            print("Données insuffisantes pour proposer des découvertes.")
            return None

        # Traitement selon le type de découverte
        if discovery_type == 'artists':
            # Découvrir des artistes moins écoutés
            artist_counts = df['artist_name'].value_counts()
            less_listened_artists = artist_counts[artist_counts < 3].index.tolist()

            if len(less_listened_artists) > 0:
                # Limiter à 50 artistes pour éviter les problèmes de mémoire
                if len(less_listened_artists) > 50:
                    less_listened_artists = less_listened_artists[:50]

                # Filtrer les titres de ces artistes
                discoveries = df[df['artist_name'].isin(less_listened_artists)]

                # Ajouter une priorité pour les artistes avec popularité
                if has_popularity:
                    # Ordonner par popularité décroissante
                    discoveries = discoveries.sort_values('popularity', ascending=False)
            else:
                print("Pas assez d'artistes peu écoutés pour proposer des découvertes.")
                return None

        elif discovery_type == 'popular' and has_popularity:
            # Titres populaires que l'utilisateur écoute peu
            # Filtrer les titres avec une popularité moyenne à élevée
            discoveries = df[(df['popularity'] >= 50) & (df['popularity'] <= 90)]

            if has_playlists:
                # Donner priorité aux titres qui apparaissent dans peu de playlists
                track_playlist_counts = df.groupby('track_id')['playlist_name'].nunique().reset_index()
                track_playlist_counts.columns = ['track_id', 'playlist_count']

                # Fusionner avec les données principales
                discoveries = pd.merge(discoveries, track_playlist_counts, on='track_id', how='left')
                discoveries = discoveries[discoveries['playlist_count'] <= 1]
        else:
            # Approche mixte (par défaut)
            if has_popularity:
                # Utiliser la popularité Spotify pour identifier les titres moins connus
                # mais pas trop impopulaires (entre 20 et 60 sur 100)
                discoveries = df[(df['popularity'] >= 20) & (df['popularity'] <= 60)]

                if len(discoveries) > n * 2:
                    # Diversifier les artistes
                    artist_counts = discoveries['artist_name'].value_counts()
                    discoveries = discoveries[~discoveries['artist_name'].isin(artist_counts[artist_counts > 2].index)]

            elif has_playlists:
                # Compter combien de fois chaque titre apparaît dans différentes playlists
                track_playlist_counts = df.groupby('track_id')['playlist_name'].nunique().reset_index()
                track_playlist_counts.columns = ['track_id', 'playlist_count']

                # Fusionner avec les données principales
                merged_df = pd.merge(df, track_playlist_counts, on='track_id', how='left')

                # Sélectionner les titres qui apparaissent dans peu de playlists (1 ou 2)
                discoveries = merged_df[merged_df['playlist_count'] <= 1]
            else:
                # Fallback: sélection aléatoire
                discoveries = df.sample(min(n * 2, len(df)))

        # Si toujours trop de titres, sélectionner les plus diversifiés
        if len(discoveries) > n:
            # Diversifier par artiste (pas plus de 2 titres par artiste)
            artist_counts = discoveries['artist_name'].value_counts()

            # Filtrer les artistes avec plus de 2 titres
            artists_to_limit = artist_counts[artist_counts > 2].index
            for artist in artists_to_limit:
                # Garder seulement 2 titres par artiste
                artist_tracks = discoveries[discoveries['artist_name'] == artist]
                if has_popularity:
                    # Garder les plus populaires
                    tracks_to_keep = artist_tracks.nlargest(2, 'popularity').index
                else:
                    # Ou sélection aléatoire
                    tracks_to_keep = artist_tracks.sample(min(2, len(artist_tracks))).index

                # Filtrer les titres en trop
                tracks_to_remove = artist_tracks.index.difference(tracks_to_keep)
                discoveries = discoveries.drop(tracks_to_remove)

            # Si encore trop, sélection aléatoire
            if len(discoveries) > n:
                discoveries = discoveries.sample(n)

        elif len(discoveries) == 0:
            print("Aucune découverte trouvée avec les critères actuels.")
            # Fallback: sélection aléatoire
            discoveries = df.sample(min(n, len(df)))

        # Colonnes à inclure dans le résultat
        result_columns = ['track_id', 'track_name', 'artist_name', 'album_name']

        if has_popularity:
            result_columns.append('popularity')

        if has_playlists:
            result_columns.append('playlist_name')

        # S'assurer que toutes les colonnes existent
        result_columns = [col for col in result_columns if col in discoveries.columns]

        return discoveries[result_columns].drop_duplicates('track_id')
    except Exception as e:
        print(f"Erreur lors de la découverte de nouveaux titres: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def get_recommendations(track_id=None, mood=None, discover=False, size=10,
                        discovery_type='mixed', min_energy=None, min_danceability=None,
                        min_valence=None, max_acousticness=None):
    """
    Fonction principale pour obtenir des recommandations

    Parameters:
        track_id (str, optional): ID du titre pour obtenir des titres similaires
        mood (str, optional): Ambiance pour générer une playlist thématique
        discover (bool): Option pour découvrir de nouveaux titres
        size (int): Nombre de recommandations à retourner
        discovery_type (str): Type de découverte ('artists', 'popular', 'mixed')
        min_energy (float): Énergie minimale pour les playlists par ambiance
        min_danceability (float): Dansabilité minimale pour les playlists par ambiance
        min_valence (float): Positivité minimale pour les playlists par ambiance
        max_acousticness (float): Acoustique maximale pour les playlists par ambiance

    Returns:
        DataFrame: DataFrame contenant les recommandations
    """
    # Charger les données
    df = load_categorized_data()

    if df is None:
        print("Impossible de charger les données pour les recommandations.")
        return None

    # Selon les paramètres fournis, utiliser différentes fonctions de recommandation
    if track_id:
        return get_similar_tracks(track_id, df, n=size)
    elif mood:
        return generate_playlist_by_mood(mood, df, size=size, min_energy=min_energy,
                                         min_danceability=min_danceability,
                                         min_valence=min_valence,
                                         max_acousticness=max_acousticness)
    elif discover:
        return discover_new_music(df, n=size, discovery_type=discovery_type)
    else:
        print("Aucun critère de recommandation spécifié.")
        return None


if __name__ == "__main__":
    # Test du module avec un exemple de chaque type de recommandation
    df = load_categorized_data()

    if df is not None:
        # Test de recommandation par titre similaire
        sample_track_id = df.iloc[0]['track_id']
        print(f"\nTest de recommandation pour le titre: {df.iloc[0]['track_name']} par {df.iloc[0]['artist_name']}")
        similar_tracks = get_similar_tracks(sample_track_id, df, n=3)
        if similar_tracks is not None:
            print("Titres similaires:")
            for _, track in similar_tracks.iterrows():
                print(f" - {track['track_name']} par {track['artist_name']} (Score: {track['similarity_score']:.2f})")

        # Test de génération de playlist par ambiance
        print("\nTest de génération de playlist 'happy':")
        happy_playlist = generate_playlist_by_mood('happy', df, size=3)
        if happy_playlist is not None:
            print("Playlist joyeuse:")
            for _, track in happy_playlist.iterrows():
                print(f" - {track['track_name']} par {track['artist_name']}")