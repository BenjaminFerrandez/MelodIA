import pandas as pd
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from config import DATA_DIR
from data_analysis import analyze_data


def load_categorized_data():
    """Charge les données catégorisées pour les recommandations"""
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

    if os.path.exists(categorized_path):
        return pd.read_csv(categorized_path)
    else:
        # Si les données catégorisées ne sont pas disponibles, exécuter l'analyse
        _, _, df = analyze_data()
        return df


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
    if df is None or df.empty or track_id not in df['track_id'].values:
        print(f"Titre avec ID {track_id} non trouvé ou données insuffisantes.")
        return None

    # Caractéristiques audio à utiliser pour la similarité
    audio_features = ['danceability', 'energy', 'valence', 'acousticness',
                      'instrumentalness', 'liveness', 'speechiness']

    # Vérifier si toutes les caractéristiques sont disponibles
    available_features = [f for f in audio_features if f in df.columns]

    if len(available_features) < 3:
        print("Pas assez de caractéristiques audio disponibles pour les recommandations.")
        return None

    # Extraire les caractéristiques
    features_matrix = df[available_features].values

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

    return recommendations[['track_id', 'track_name', 'artist_name', 'album_name',
                            'playlist_name', 'similarity_score'] + available_features]


def generate_playlist_by_mood(mood, df, size=15):
    """
    Génère une playlist basée sur l'ambiance souhaitée

    Parameters:
        mood (str): Ambiance souhaitée ('happy', 'energetic', 'calm', 'melancholic')
        df (DataFrame): DataFrame contenant les données des titres
        size (int): Nombre de titres dans la playlist

    Returns:
        DataFrame: DataFrame contenant les titres de la playlist
    """
    if df is None or df.empty:
        return None

    # Vérifier si les caractéristiques nécessaires sont disponibles
    required_features = ['danceability', 'energy', 'valence', 'acousticness']
    if not all(feature in df.columns for feature in required_features):
        print("Caractéristiques manquantes pour la génération de playlist.")
        return None

    # Définir les critères pour chaque ambiance
    mood_criteria = {
        'happy': {'valence': 0.7, 'energy': 0.6},
        'energetic': {'energy': 0.8, 'danceability': 0.7},
        'calm': {'energy': 0.4, 'acousticness': 0.7, 'valence': 0.5},
        'melancholic': {'valence': 0.4, 'energy': 0.4, 'acousticness': 0.6}
    }

    if mood.lower() not in mood_criteria:
        print(f"Ambiance {mood} non reconnue. Options disponibles: {list(mood_criteria.keys())}")
        return None

    # Appliquer les critères de filtre selon l'ambiance choisie
    criteria = mood_criteria[mood.lower()]

    # Filtrer les titres selon les critères
    filtered_df = df.copy()

    for feature, threshold in criteria.items():
        filtered_df = filtered_df[filtered_df[feature] >= threshold]

    # Si pas assez de titres après filtrage, assouplir les critères
    if len(filtered_df) < size:
        print(f"Seulement {len(filtered_df)} titres correspondent aux critères stricts. Assouplissement...")

        # Réduire tous les seuils de 20%
        filtered_df = df.copy()
        for feature, threshold in criteria.items():
            filtered_df = filtered_df[filtered_df[feature] >= threshold * 0.8]

    # Si toujours pas assez, prendre les titres qui se rapprochent le plus des critères
    if len(filtered_df) < size:
        print(f"Après assouplissement: {len(filtered_df)} titres trouvés. Utilisation d'une approche par score...")

        # Calculer un score pour chaque titre basé sur les critères
        df['mood_score'] = 0

        for feature, threshold in criteria.items():
            # Plus la valeur est supérieure au seuil, plus le score augmente
            df['mood_score'] += (df[feature] - threshold * 0.8).clip(lower=0)

        # Trier par score décroissant et prendre les meilleurs
        filtered_df = df.sort_values('mood_score', ascending=False).head(size)

    # Sélection des titres pour la playlist
    if len(filtered_df) > size:
        playlist = filtered_df.sample(size)
    else:
        playlist = filtered_df

    return playlist[['track_id', 'track_name', 'artist_name', 'album_name',
                     'playlist_name'] + required_features]


def discover_new_music(df, n=10):
    """
    Recommande des titres peu connus ou récemment ajoutés à la bibliothèque

    Parameters:
        df (DataFrame): DataFrame contenant les données des titres
        n (int): Nombre de titres à recommander

    Returns:
        DataFrame: DataFrame contenant les découvertes recommandées
    """
    if df is None or df.empty:
        return None

    # Définir ce qu'est un titre "peu connu" dans la bibliothèque
    # - Popularité plus faible (si disponible)
    # - Moins de présence dans les playlists

    # Vérifier si les caractéristiques utiles sont disponibles
    has_popularity = 'popularity' in df.columns
    has_playlists = 'playlist_name' in df.columns

    if not (has_popularity or has_playlists):
        print("Données insuffisantes pour proposer des découvertes.")
        return None

    # Approche différente selon les données disponibles
    if has_popularity:
        # Utiliser la popularité Spotify pour identifier les titres moins connus
        # mais pas trop impopulaires (entre 20 et 60 sur 100)
        discoveries = df[(df['popularity'] >= 20) & (df['popularity'] <= 60)]

        if len(discoveries) > n:
            # Diversifier les artistes
            artist_counts = discoveries['artist_name'].value_counts()
            discoveries = discoveries[~discoveries['artist_name'].isin(artist_counts[artist_counts > 3].index)]

    elif has_playlists:
        # Compter combien de fois chaque titre apparaît dans différentes playlists
        track_playlist_counts = df.groupby('track_id')['playlist_name'].nunique().reset_index()
        track_playlist_counts.columns = ['track_id', 'playlist_count']

        # Fusionner avec les données principales
        merged_df = pd.merge(df, track_playlist_counts, on='track_id', how='left')

        # Sélectionner les titres qui apparaissent dans peu de playlists (1 ou 2)
        discoveries = merged_df[merged_df['playlist_count'] <= 2]

    # Si toujours trop de titres, sélectionner aléatoirement
    if len(discoveries) > n:
        discoveries = discoveries.sample(n)
    elif len(discoveries) == 0:
        print("Aucune découverte trouvée avec les critères actuels.")
        return None

    # Colonnes à inclure dans le résultat
    result_columns = ['track_id', 'track_name', 'artist_name', 'album_name']

    if has_popularity:
        result_columns.append('popularity')

    if has_playlists:
        result_columns.append('playlist_name')

    return discoveries[result_columns].drop_duplicates('track_id')


def get_recommendations(track_id=None, mood=None, discover=False, size=10):
    """
    Fonction principale pour obtenir des recommandations

    Parameters:
        track_id (str, optional): ID du titre pour obtenir des titres similaires
        mood (str, optional): Ambiance pour générer une playlist thématique
        discover (bool): Option pour découvrir de nouveaux titres
        size (int): Nombre de recommandations à retourner

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
        return generate_playlist_by_mood(mood, df, size=size)
    elif discover:
        return discover_new_music(df, n=size)
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
                print(f" - {track['track_name']} par {track['artist_name']} (Valence: {track['valence']:.2f})")

        # Test de découverte de nouveaux titres
        print("\nTest de découverte de nouveaux titres:")
        discoveries = discover_new_music(df, n=3)
        if discoveries is not None:
            print("Découvertes suggérées:")
            for _, track in discoveries.iterrows():
                print(f" - {track['track_name']} par {track['artist_name']}")