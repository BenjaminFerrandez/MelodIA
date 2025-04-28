import pandas as pd
import numpy as np
import os
from config import DATA_DIR


def load_data():
    """Charge les données depuis les fichiers disponibles"""
    # Chercher les fichiers dans l'ordre de préférence
    potential_files = [
        os.path.join(DATA_DIR, "cleaned_tracks.csv"),
        os.path.join(DATA_DIR, "tracks_with_features.csv"),
        os.path.join(DATA_DIR, "tracks.csv")
    ]

    # Utiliser le premier fichier disponible
    for file_path in potential_files:
        if os.path.exists(file_path):
            print(f"Chargement des données depuis {file_path}")
            try:
                return pd.read_csv(file_path)
            except Exception as e:
                print(f"Erreur lors du chargement de {file_path}: {e}")

    print("Aucun fichier de données trouvé.")
    return None


def get_basic_stats(df):
    """Calcule des statistiques de base sur les données"""
    if df is None or df.empty:
        return None

    # Statistiques de base qui ne dépendent que des colonnes obligatoires
    stats = {
        'total_tracks': len(df),
        'unique_artists': df['artist_name'].nunique() if 'artist_name' in df.columns else 0,
        'unique_albums': df['album_name'].nunique() if 'album_name' in df.columns else 0,
        'playlists': df['playlist_name'].nunique() if 'playlist_name' in df.columns else 0
    }

    # Top artistes (si disponible)
    if 'artist_name' in df.columns:
        top_artists = df['artist_name'].value_counts().head(10).to_dict()
        stats['top_artists'] = top_artists

    # Top playlists (si disponible)
    if 'playlist_name' in df.columns:
        playlist_counts = df['playlist_name'].value_counts().to_dict()
        stats['playlist_counts'] = playlist_counts

    # Ajouter des statistiques sur les caractéristiques audio si disponibles
    audio_features = ['danceability', 'energy', 'valence', 'acousticness']
    available_features = [f for f in audio_features if f in df.columns]

    for feature in available_features:
        stats[f'avg_{feature}'] = df[feature].mean()
        stats[f'min_{feature}'] = df[feature].min()
        stats[f'max_{feature}'] = df[feature].max()

    return stats


def analyze_audio_features(df):
    """Analyse les caractéristiques audio des titres (si disponibles)"""
    if df is None or df.empty:
        return None

    # Vérifier quelles caractéristiques audio sont disponibles
    audio_features = ['danceability', 'energy', 'valence', 'acousticness', 'tempo']
    available_features = [f for f in audio_features if f in df.columns]

    # Si aucune caractéristique n'est disponible, retourner un résultat vide
    if not available_features:
        print("Aucune caractéristique audio n'est disponible pour l'analyse.")
        return {'available_features': []}

    # Créer une analyse basée sur les caractéristiques disponibles
    analysis = {'available_features': available_features}

    # Corrélations entre les caractéristiques (si plus d'une caractéristique)
    if len(available_features) > 1:
        correlations = df[available_features].corr()
        analysis['correlations'] = correlations.to_dict()

    # Analyse par playlist si disponible
    if 'playlist_name' in df.columns and len(available_features) > 0:
        # Calculer les moyennes par playlist
        playlist_analysis = df.groupby('playlist_name')[available_features].mean()
        analysis['playlist_profiles'] = playlist_analysis.to_dict()

    return analysis


def categorize_music(df):
    """Catégorise les titres de manière simple"""
    if df is None or df.empty:
        return df

    # Copie pour éviter de modifier l'original
    result_df = df.copy()

    # Vérifier quelles caractéristiques sont disponibles
    has_energy = 'energy' in df.columns
    has_danceability = 'danceability' in df.columns
    has_valence = 'valence' in df.columns
    has_acousticness = 'acousticness' in df.columns

    # Uniquement ajouter les catégories si les caractéristiques nécessaires sont présentes

    # Catégorie Énergie/Danse
    if has_energy and has_danceability:
        # Créer une version simplifiée de catégorisation
        conditions = [
            (df['energy'] > 0.7) & (df['danceability'] > 0.7),
            (df['energy'] > 0.7) & (df['danceability'] <= 0.7),
            (df['energy'] <= 0.7) & (df['danceability'] > 0.7),
            (df['energy'] <= 0.4) & (df['danceability'] <= 0.4)
        ]
        choices = ['Énergique et Dansant', 'Énergique', 'Dansant', 'Calme']
        result_df['energy_dance_category'] = np.select(conditions, choices, default='Modéré')

    # Catégorie Mood
    if has_valence:
        # Simplifier en trois catégories basées uniquement sur la valence
        result_df['mood_category'] = pd.cut(
            df['valence'],
            bins=[0, 0.33, 0.67, 1],
            labels=['Mélancolique', 'Neutre', 'Joyeux']
        )

    # Catégorie Acoustique/Électronique
    if has_acousticness:
        # Simplifier en deux catégories
        result_df['acoustic_category'] = np.where(df['acousticness'] > 0.5, 'Acoustique', 'Électronique')

    # Catégorie combinée Acoustique/Mood (si les deux sont disponibles)
    if has_acousticness and has_valence:
        # Version simplifiée
        acoustic_cond = df['acousticness'] > 0.5
        happy_cond = df['valence'] > 0.5

        result_df['acoustic_mood_category'] = np.select(
            [
                acoustic_cond & happy_cond,
                acoustic_cond & ~happy_cond,
                ~acoustic_cond & happy_cond,
                ~acoustic_cond & ~happy_cond
            ],
            [
                'Acoustique Joyeux',
                'Acoustique Mélancolique',
                'Électronique Joyeux',
                'Électronique Sombre'
            ],
            default='Équilibré'
        )

    # Sauvegarder le DataFrame catégorisé
    try:
        categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")
        result_df.to_csv(categorized_path, index=False)
        print(f"Titres catégorisés sauvegardés dans: {categorized_path}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde des données catégorisées: {e}")

    return result_df


def analyze_data():
    """Fonction principale pour analyser les données"""
    print("Démarrage de l'analyse de données...")

    # Charger les données
    df = load_data()

    if df is None:
        print("ERREUR: Aucune donnée disponible pour l'analyse.")
        return None, None, None

    # Vérifier que les colonnes minimales sont présentes
    required_cols = ['track_name', 'artist_name']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"ERREUR: Colonnes requises manquantes: {missing_cols}")
        return None, None, None

    print(f"Analyse en cours pour {len(df)} titres...")

    try:
        # 1. Obtenir les statistiques de base
        stats = get_basic_stats(df)
        print("Statistiques de base calculées.")

        # 2. Analyser les caractéristiques audio (si disponibles)
        audio_analysis = analyze_audio_features(df)
        print("Analyse des caractéristiques audio terminée.")

        # 3. Catégoriser les titres
        categorized_df = categorize_music(df)
        print("Catégorisation des titres terminée.")

        print("Analyse complète terminée avec succès.")
        return stats, audio_analysis, categorized_df

    except Exception as e:
        print(f"ERREUR pendant l'analyse: {e}")
        import traceback
        traceback.print_exc()

        # En cas d'erreur, essayer de retourner ce qui a été calculé jusqu'à présent
        return (
            get_basic_stats(df) if 'stats' not in locals() else stats,
            None if 'audio_analysis' not in locals() else audio_analysis,
            df if 'categorized_df' not in locals() else categorized_df
        )


if __name__ == "__main__":
    # Test du module
    stats, audio_analysis, categorized_df = analyze_data()

    if stats:
        print("\nStatistiques de base:")
        print(f"Total des titres: {stats['total_tracks']}")
        print(f"Artistes uniques: {stats['unique_artists']}")

        if 'top_artists' in stats:
            print("\nTop 5 artistes:")
            for i, (artist, count) in enumerate(list(stats['top_artists'].items())[:5]):
                print(f"{i + 1}. {artist}: {count} titres")

        if categorized_df is not None and 'energy_dance_category' in categorized_df.columns:
            print(f"\nCatégories créées: {categorized_df['energy_dance_category'].unique()}")
            print(f"Répartition des catégories:")
            print(categorized_df['energy_dance_category'].value_counts())
    else:
        print("L'analyse n'a pas pu être effectuée. Vérifiez vos données d'entrée.")