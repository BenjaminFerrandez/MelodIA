import pandas as pd
import os
import re
from datetime import datetime
from config import DATA_DIR


def load_data(merged=True):
    """Charge les données depuis les fichiers CSV sauvegardés"""
    if merged and os.path.exists(os.path.join(DATA_DIR, "tracks_with_features.csv")):
        # Charger le dataset fusionné si disponible
        return pd.read_csv(os.path.join(DATA_DIR, "tracks_with_features.csv"))
    elif os.path.exists(os.path.join(DATA_DIR, "tracks.csv")):
        # Sinon, charger uniquement les titres
        return pd.read_csv(os.path.join(DATA_DIR, "tracks.csv"))
    else:
        print("Aucun fichier de données trouvé.")
        return None


def clean_data(df):
    """Nettoie et prépare les données pour l'analyse"""
    if df is None or df.empty:
        return None

    print("Nettoyage des données...")

    # Faire une copie pour éviter de modifier l'original
    cleaned_df = df.copy()

    # Vérifier si nous avons des caractéristiques audio
    has_audio_features = all(feature in cleaned_df.columns for feature in
                             ['danceability', 'energy', 'valence', 'acousticness'])

    if not has_audio_features:
        print("Avertissement: Caractéristiques audio non disponibles. L'analyse sera limitée.")

    # Supprimer les doublons basés sur l'ID du titre
    initial_rows = len(cleaned_df)
    cleaned_df.drop_duplicates(subset=['track_id'], inplace=True)
    print(f"Doublons supprimés: {initial_rows - len(cleaned_df)} titres")

    # Gestion des valeurs manquantes
    # Pour les colonnes obligatoires, supprimer les lignes avec des valeurs manquantes
    essential_cols = ['track_id', 'track_name', 'artist_name']
    cleaned_df.dropna(subset=essential_cols, inplace=True)

    # Pour les colonnes non-essentielles, remplacer les valeurs manquantes
    if 'popularity' in cleaned_df.columns:
        cleaned_df['popularity'].fillna(0, inplace=True)

    # Convertir les dates en format datetime si disponible
    if 'release_date' in cleaned_df.columns:
        # Traiter différents formats de date possibles
        def parse_date(date_str):
            if pd.isna(date_str):
                return None

            # Format YYYY
            if re.match(r'^\d{4}$', str(date_str)):
                return datetime.strptime(str(date_str), '%Y')

            # Format YYYY-MM
            elif re.match(r'^\d{4}-\d{2}$', str(date_str)):
                return datetime.strptime(str(date_str), '%Y-%m')

            # Format YYYY-MM-DD
            elif re.match(r'^\d{4}-\d{2}-\d{2}$', str(date_str)):
                return datetime.strptime(str(date_str), '%Y-%m-%d')
            else:
                return None

        # Appliquer la fonction de parsing et créer des colonnes pour année et décennie
        cleaned_df['release_date_parsed'] = cleaned_df['release_date'].apply(parse_date)
        cleaned_df['release_year'] = cleaned_df['release_date_parsed'].apply(
            lambda x: x.year if x else None)
        cleaned_df['decade'] = cleaned_df['release_year'].apply(
            lambda x: (x // 10) * 10 if x else None)

    # Normaliser les caractéristiques audio si disponibles
    audio_features = ['danceability', 'energy', 'speechiness', 'acousticness',
                      'instrumentalness', 'liveness', 'valence']

    for feature in audio_features:
        if feature in cleaned_df.columns:
            # La plupart des caractéristiques sont déjà normalisées entre 0 et 1
            # Mais on s'assure qu'elles sont dans cette plage
            cleaned_df[feature] = cleaned_df[feature].clip(0, 1)

    # Normaliser le tempo qui est généralement en BPM
    if 'tempo' in cleaned_df.columns:
        # Créer une version normalisée pour la comparaison
        min_tempo = cleaned_df['tempo'].min()
        max_tempo = cleaned_df['tempo'].max()

        if max_tempo > min_tempo:  # Éviter division par zéro
            cleaned_df['tempo_normalized'] = (cleaned_df['tempo'] - min_tempo) / (max_tempo - min_tempo)

    # Ajouter des catégories pour certaines caractéristiques
    if 'energy' in cleaned_df.columns:
        cleaned_df['energy_category'] = pd.cut(
            cleaned_df['energy'],
            bins=[0, 0.33, 0.66, 1],
            labels=['Basse', 'Moyenne', 'Haute']
        )

    if 'valence' in cleaned_df.columns:
        cleaned_df['mood'] = pd.cut(
            cleaned_df['valence'],
            bins=[0, 0.33, 0.66, 1],
            labels=['Triste', 'Neutre', 'Joyeux']
        )

    # Sauvegarder le DataFrame nettoyé
    cleaned_path = os.path.join(DATA_DIR, "cleaned_tracks.csv")
    cleaned_df.to_csv(cleaned_path, index=False)
    print(f"Données nettoyées sauvegardées dans: {cleaned_path}")

    return cleaned_df


def process_data():
    """Fonction principale pour charger et nettoyer les données"""
    # Charger les données
    df = load_data()

    if df is not None:
        # Nettoyer les données
        cleaned_df = clean_data(df)
        return cleaned_df
    else:
        return None


if __name__ == "__main__":
    # Test du module
    cleaned_data = process_data()
    if cleaned_data is not None:
        print(f"Traitement réussi: {len(cleaned_data)} titres après nettoyage.")
        print(f"Colonnes disponibles: {cleaned_data.columns.tolist()}")