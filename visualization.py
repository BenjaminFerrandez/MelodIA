import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from config import DATA_DIR
from data_processing import load_data, process_data
from data_analysis import analyze_data

# Configuration du style de visualisation
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12


def save_fig(fig, filename):
    """Sauvegarde une figure dans le répertoire de visualisations"""
    # Créer un sous-répertoire pour les visualisations
    viz_dir = os.path.join(DATA_DIR, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)

    # Sauvegarder la figure
    fig_path = os.path.join(viz_dir, filename)
    fig.savefig(fig_path, bbox_inches='tight', dpi=300)
    plt.close(fig)

    return fig_path


def plot_top_artists(df, top_n=15):
    """Génère un graphique des artistes les plus écoutés"""
    if df is None or df.empty:
        return None

    top_artists = df['artist_name'].value_counts().head(top_n)

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = sns.barplot(x=top_artists.values, y=top_artists.index, ax=ax)

    # Ajouter les valeurs sur les barres
    for i, v in enumerate(top_artists.values):
        ax.text(v + 0.5, i, str(v), va='center')

    ax.set_title(f"Top {top_n} Artistes les Plus Écoutés", fontsize=16)
    ax.set_xlabel("Nombre de titres", fontsize=14)
    ax.set_ylabel("")

    return save_fig(fig, "top_artists.png")


def plot_audio_features_distribution(df):
    """Génère des distributions des caractéristiques audio principales"""
    if df is None or df.empty:
        return None

    # Vérifier si les caractéristiques audio sont disponibles
    audio_features = ['danceability', 'energy', 'valence', 'acousticness']
    if not all(feature in df.columns for feature in audio_features):
        print("Caractéristiques audio manquantes pour la visualisation.")
        return None

    # Créer une figure avec des sous-graphiques
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for i, feature in enumerate(audio_features):
        sns.histplot(df[feature], kde=True, ax=axes[i])
        axes[i].set_title(f"Distribution de {feature}", fontsize=14)
        axes[i].set_xlabel(feature, fontsize=12)
        axes[i].set_ylabel("Nombre de titres", fontsize=12)

    plt.tight_layout()

    return save_fig(fig, "audio_features_distribution.png")


def plot_energy_valence_scatter(df):
    """Génère un nuage de points Énergie vs Valence par playlist"""
    if df is None or df.empty:
        return None

    # Vérifier si les caractéristiques nécessaires sont disponibles
    if not all(col in df.columns for col in ['energy', 'valence', 'playlist_name']):
        print("Colonnes manquantes pour le nuage de points Énergie/Valence.")
        return None

    # Limiter le nombre de playlists pour la lisibilité
    top_playlists = df['playlist_name'].value_counts().head(10).index.tolist()
    plot_df = df[df['playlist_name'].isin(top_playlists)]

    fig, ax = plt.subplots(figsize=(14, 10))
    scatter = sns.scatterplot(
        data=plot_df,
        x='energy',
        y='valence',
        hue='playlist_name',
        palette='viridis',
        alpha=0.7,
        s=100,
        ax=ax
    )

    # Ajouter une grille pour faciliter la lecture
    ax.grid(True, linestyle='--', alpha=0.7)

    # Ajouter des lignes pour diviser le graphique en quadrants
    ax.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)

    # Ajouter des annotations pour les quadrants
    ax.text(0.25, 0.75, "Calme & Positif", fontsize=12, ha='center')
    ax.text(0.75, 0.75, "Énergique & Positif", fontsize=12, ha='center')
    ax.text(0.25, 0.25, "Calme & Sombre", fontsize=12, ha='center')
    ax.text(0.75, 0.25, "Énergique & Sombre", fontsize=12, ha='center')

    ax.set_title("Relation entre Énergie et Valence (positivité) par Playlist", fontsize=16)
    ax.set_xlabel("Énergie", fontsize=14)
    ax.set_ylabel("Valence", fontsize=14)

    # Ajuster la légende
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, title="Playlist", fontsize=12, title_fontsize=14)

    return save_fig(fig, "energy_valence_scatter.png")


def plot_playlist_profiles(df):
    """Génère un graphique radar des profils audio de chaque playlist"""
    if df is None or df.empty or 'playlist_name' not in df.columns:
        return None

    # Caractéristiques pour le graphique radar
    features = ['danceability', 'energy', 'valence', 'acousticness', 'instrumentalness']

    if not all(feature in df.columns for feature in features):
        print("Caractéristiques manquantes pour les profils de playlist.")
        return None

    # Calculer la moyenne des caractéristiques par playlist
    playlist_profiles = df.groupby('playlist_name')[features].mean()

    # Limiter à un nombre raisonnable de playlists
    top_playlists = df['playlist_name'].value_counts().head(6).index
    playlist_profiles = playlist_profiles.loc[top_playlists]

    # Nombre de variables
    N = len(features)

    # Préparer le graphique radar
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Angles pour chaque caractéristique (répartis uniformément)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    # Fermer le graphique en répétant le premier angle
    angles += angles[:1]

    # Ajouter les axes au graphique radar
    ax.set_theta_offset(np.pi / 2)  # Déplacer le premier axe en haut
    ax.set_theta_direction(-1)  # Sens horaire

    # Étiquettes pour chaque axe
    plt.xticks(angles[:-1], features, fontsize=12)

    # Tracer chaque playlist
    for i, playlist in enumerate(playlist_profiles.index):
        values = playlist_profiles.loc[playlist].values.flatten().tolist()
        values += values[:1]  # Fermer le graphique en répétant la première valeur

        # Tracer la ligne et remplir l'aire
        ax.plot(angles, values, linewidth=2, linestyle='solid', label=playlist)
        ax.fill(angles, values, alpha=0.1)

    # Ajouter une légende
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

    plt.title("Profils Audio des Playlists", fontsize=16)

    return save_fig(fig, "playlist_profiles_radar.png")


def plot_categorized_tracks(df):
    """Génère un graphique des catégories de titres"""
    if df is None or df.empty or not all(
            col in df.columns for col in ['energy_dance_category', 'acoustic_mood_category']):
        return None

    # Créer deux sous-graphiques pour les deux types de catégorisation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Graphique pour la catégorie Énergie/Danse
    energy_dance_counts = df['energy_dance_category'].value_counts().sort_values(ascending=False)
    sns.barplot(x=energy_dance_counts.values, y=energy_dance_counts.index, palette='viridis', ax=ax1)
    ax1.set_title("Répartition par Catégorie Énergie/Danse", fontsize=14)
    ax1.set_xlabel("Nombre de titres", fontsize=12)

    # Ajouter les valeurs sur les barres
    for i, v in enumerate(energy_dance_counts.values):
        ax1.text(v + 0.5, i, str(v), va='center')

    # Graphique pour la catégorie Acoustique/Mood
    acoustic_mood_counts = df['acoustic_mood_category'].value_counts().sort_values(ascending=False)
    sns.barplot(x=acoustic_mood_counts.values, y=acoustic_mood_counts.index, palette='mako', ax=ax2)
    ax2.set_title("Répartition par Catégorie Acoustique/Mood", fontsize=14)
    ax2.set_xlabel("Nombre de titres", fontsize=12)

    # Ajouter les valeurs sur les barres
    for i, v in enumerate(acoustic_mood_counts.values):
        ax2.text(v + 0.5, i, str(v), va='center')

    plt.tight_layout()

    return save_fig(fig, "categorized_tracks.png")


def create_visualizations():
    """Fonction principale pour créer toutes les visualisations"""
    # Charger les données catégorisées si disponibles
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

    if os.path.exists(categorized_path):
        df = pd.read_csv(categorized_path)
    else:
        # Si les données catégorisées ne sont pas disponibles, exécuter l'analyse
        _, _, df = analyze_data()

    if df is not None:
        print("Création des visualisations...")

        # Créer les visualisations
        top_artists_path = plot_top_artists(df)
        features_dist_path = plot_audio_features_distribution(df)
        scatter_path = plot_energy_valence_scatter(df)
        radar_path = plot_playlist_profiles(df)
        categories_path = plot_categorized_tracks(df)

        # Liste des chemins vers les visualisations créées
        viz_paths = [
            p for p in [top_artists_path, features_dist_path, scatter_path,
                        radar_path, categories_path] if p is not None
        ]

        print(f"Visualisations créées: {len(viz_paths)}")
        for path in viz_paths:
            print(f" - {os.path.basename(path)}")

        return viz_paths
    else:
        print("Aucune donnée disponible pour créer des visualisations.")
        return None


if __name__ == "__main__":
    # Test du module
    viz_paths = create_visualizations()