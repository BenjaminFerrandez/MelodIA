import pandas as pd
import numpy as np
import os
from config import DATA_DIR
from data_processing import load_data, process_data


def get_basic_stats(df):
    """Calcule des statistiques de base sur les données"""
    if df is None or df.empty:
        return None

    stats = {
        'total_tracks': len(df),
        'unique_artists': df['artist_name'].nunique(),
        'unique_albums': df['album_name'].nunique() if 'album_name' in df.columns else 0,
        'playlists': df['playlist_name'].nunique() if 'playlist_name' in df.columns else 0
    }

    # Ajouter des statistiques sur les caractéristiques audio si disponibles
    audio_features = ['danceability', 'energy', 'valence', 'tempo', 'acousticness']

    for feature in audio_features:
        if feature in df.columns:
            stats[f'avg_{feature}'] = df[feature].mean()
            stats[f'min_{feature}'] = df[feature].min()
            stats[f'max_{feature}'] = df[feature].max()

    # Top artistes
    top_artists = df['artist_name'].value_counts().head(10).to_dict()
    stats['top_artists'] = top_artists

    # Top playlists
    if 'playlist_name' in df.columns:
        playlist_counts = df.groupby('playlist_name').size().sort_values(ascending=False).to_dict()
        stats['playlist_counts'] = playlist_counts

    # Distribution temporelle si disponible
    if 'release_year' in df.columns:
        year_counts = df['release_year'].value_counts().sort_index().to_dict()
        stats['years_distribution'] = year_counts

        # Décennies
        if 'decade' in df.columns:
            decade_counts = df['decade'].value_counts().sort_index().to_dict()
            stats['decades_distribution'] = decade_counts

    return stats


def analyze_audio_features(df):
    """Analyse les caractéristiques audio des titres"""
    if df is None or df.empty:
        return None

    # Vérifier si les caractéristiques audio sont disponibles
    audio_features = ['danceability', 'energy', 'valence', 'acousticness', 'tempo']
    if not all(feature in df.columns for feature in audio_features):
        print("Certaines caractéristiques audio ne sont pas disponibles pour l'analyse audio complète.")
        # Créer un dictionnaire vide pour indiquer que l'analyse audio n'a pas pu être effectuée
        return {'error': 'Caractéristiques audio non disponibles'}

    analysis = {}

    # Corrélations entre les caractéristiques
    correlations = df[audio_features].corr()
    analysis['correlations'] = correlations.to_dict()

    # Analyse par playlist si disponible
    if 'playlist_name' in df.columns:
        playlist_analysis = df.groupby('playlist_name')[audio_features].mean()
        analysis['playlist_profiles'] = playlist_analysis.to_dict()

        # Identifier les playlists avec les valeurs extrêmes pour chaque caractéristique
        for feature in audio_features:
            max_playlist = playlist_analysis[feature].idxmax()
            min_playlist = playlist_analysis[feature].idxmin()
            analysis[f'highest_{feature}_playlist'] = max_playlist
            analysis[f'lowest_{feature}_playlist'] = min_playlist

    # Analyse par artiste (pour les artistes ayant au moins 3 titres)
    artist_counts = df['artist_name'].value_counts()
    artists_with_multiple_tracks = artist_counts[artist_counts >= 3].index

    if len(artists_with_multiple_tracks) > 0:
        artist_df = df[df['artist_name'].isin(artists_with_multiple_tracks)]
        artist_analysis = artist_df.groupby('artist_name')[audio_features].mean()
        analysis['artist_profiles'] = artist_analysis.to_dict()

    # Sauvegarder l'analyse
    analysis_path = os.path.join(DATA_DIR, "audio_analysis.csv")
    pd.DataFrame(analysis['playlist_profiles']).to_csv(analysis_path)
    print(f"Analyse des caractéristiques audio sauvegardée dans: {analysis_path}")

    return analysis


def categorize_music(df):
    """Catégorise les titres en clusters basés sur leurs caractéristiques audio"""
    if df is None or df.empty:
        return df

    # Vérifier si les caractéristiques audio sont disponibles
    audio_features = ['danceability', 'energy', 'valence', 'acousticness']
    if not all(feature in df.columns for feature in audio_features):
        print("Caractéristiques audio insuffisantes pour la catégorisation.")
        return df

    # Approche simplifiée pour la catégorisation sans clustering sophistiqué
    # Création de catégories basées sur les valeurs des caractéristiques

    # Copie pour éviter de modifier l'original
    categorized_df = df.copy()

    # Catégorie Énergie/Danse
    conditions = [
        (categorized_df['energy'] > 0.7) & (categorized_df['danceability'] > 0.7),
        (categorized_df['energy'] > 0.7) & (categorized_df['danceability'] <= 0.7),
        (categorized_df['energy'] <= 0.7) & (categorized_df['danceability'] > 0.7),
        (categorized_df['energy'] <= 0.4) & (categorized_df['danceability'] <= 0.4)
    ]

    choices = ['Énergique et Dansant', 'Énergique', 'Dansant', 'Calme']

    categorized_df['energy_dance_category'] = np.select(conditions, choices, default='Modéré')

    # Catégorie Acoustique/Mood
    conditions = [
        (categorized_df['acousticness'] > 0.7) & (categorized_df['valence'] > 0.7),
        (categorized_df['acousticness'] > 0.7) & (categorized_df['valence'] <= 0.3),
        (categorized_df['acousticness'] <= 0.3) & (categorized_df['valence'] > 0.7),
        (categorized_df['acousticness'] <= 0.3) & (categorized_df['valence'] <= 0.3)
    ]

    choices = ['Acoustique Joyeux', 'Acoustique Mélancolique', 'Électronique Joyeux', 'Électronique Intense']

    categorized_df['acoustic_mood_category'] = np.select(conditions, choices, default='Équilibré')

    # Sauvegarder le DataFrame catégorisé
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")
    categorized_df.to_csv(categorized_path, index=False)
    print(f"Titres catégorisés sauvegardés dans: {categorized_path}")

    return categorized_df


def analyze_data():
    """Fonction principale pour analyser les données"""
    # Charger les données nettoyées si disponibles, sinon les traiter
    cleaned_path = os.path.join(DATA_DIR, "cleaned_tracks.csv")

    if os.path.exists(cleaned_path):
        df = pd.read_csv(cleaned_path)
    else:
        df = process_data()

    if df is not None:
        # Obtenir les statistiques de base
        stats = get_basic_stats(df)

        # Analyser les caractéristiques audio
        audio_analysis = analyze_audio_features(df)

        # Catégoriser les titres
        categorized_df = categorize_music(df)

        return stats, audio_analysis, categorized_df
    else:
        return None, None, None


if __name__ == "__main__":
    # Test du module
    stats, audio_analysis, categorized_df = analyze_data()

    if stats:
        print("\nStatistiques de base:")
        print(f"Total des titres: {stats['total_tracks']}")
        print(f"Artistes uniques: {stats['unique_artists']}")
        print("\nTop 5 artistes:")
        for i, (artist, count) in enumerate(list(stats['top_artists'].items())[:5]):
            print(f"{i + 1}. {artist}: {count} titres")

    if categorized_df is not None:
        print(f"\nCatégories créées: {categorized_df['energy_dance_category'].unique()}")
        print(f"Répartition des catégories:")
        print(categorized_df['energy_dance_category'].value_counts())