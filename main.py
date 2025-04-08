import os
import sys
import time

# Ajouter le répertoire racine au PATH pour les imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR
from spotify_api import extract_spotify_data
from data_processing import process_data
from data_analysis import analyze_data
from visualization import create_visualizations
from recommendation import get_recommendations
from top_artists import analyze_top_artists, TopArtistsAnalyzer


def print_header(message):
    """Affiche un en-tête formaté pour les étapes du programme"""
    print("\n" + "=" * 70)
    print(f"  {message}")
    print("=" * 70 + "\n")


def check_setup():
    """Vérifie si la configuration est correcte"""
    # Vérifier si le répertoire de données existe
    if not os.path.exists(DATA_DIR):
        print("Création du répertoire de données...")
        os.makedirs(DATA_DIR, exist_ok=True)

    # Vérifier si le fichier .env existe avec les identifiants Spotify
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_file):
        print("AVERTISSEMENT: Fichier .env non trouvé!")
        print("Créez un fichier .env avec les variables suivantes:")
        print("  SPOTIFY_CLIENT_ID=votre_client_id")
        print("  SPOTIFY_CLIENT_SECRET=votre_client_secret")
        print("  SPOTIFY_REDIRECT_URI=http://localhost:8888/callback")
        print("\nVous pouvez obtenir ces informations en créant une application dans le")
        print("tableau de bord Spotify Developer: https://developer.spotify.com/dashboard/")
        return False

    return True


def clear_data():
    """Supprime toutes les données extraites pour permettre un nouveau départ"""
    # Fichiers à supprimer
    data_files = [
        "tracks.csv",
        "audio_features.csv",
        "tracks_with_features.csv",
        "cleaned_tracks.csv",
        "categorized_tracks.csv",
        "audio_analysis.csv"
    ]

    deleted = False
    for file_name in data_files:
        file_path = os.path.join(DATA_DIR, file_name)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Fichier supprimé: {file_name}")
                deleted = True
            except Exception as e:
                print(f"Erreur lors de la suppression de {file_name}: {e}")

    # Supprimer aussi le dossier des visualisations
    viz_dir = os.path.join(DATA_DIR, "visualizations")
    if os.path.exists(viz_dir) and os.path.isdir(viz_dir):
        try:
            for file in os.listdir(viz_dir):
                os.remove(os.path.join(viz_dir, file))
            os.rmdir(viz_dir)
            print("Dossier des visualisations supprimé")
            deleted = True
        except Exception as e:
            print(f"Erreur lors de la suppression du dossier des visualisations: {e}")

    if deleted:
        print("\nToutes les données ont été supprimées. Vous pouvez désormais repartir de zéro.")
        return True
    else:
        print("\nAucune donnée à supprimer.")
        return False


def logout_spotify():
    """Déconnecte l'utilisateur de Spotify en supprimant le fichier cache et les jetons d'authentification"""
    # Chemins des fichiers de cache Spotify
    cache_path = os.path.join(DATA_DIR, ".spotify_cache")
    cache_files = [
        cache_path,
        # Chercher d'autres fichiers de cache possibles dans le répertoire de données
        *[os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if '.cache' in f]
    ]

    deleted = False
    for file_path in cache_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Fichier cache supprimé: {os.path.basename(file_path)}")
                deleted = True
            except Exception as e:
                print(f"Erreur lors de la suppression de {file_path}: {e}")

    # Chercher et supprimer les jetons dans le répertoire courant aussi
    for file in os.listdir(os.path.dirname(os.path.abspath(__file__))):
        if '.cache' in file:
            try:
                os.remove(os.path.join(os.path.dirname(os.path.abspath(__file__)), file))
                print(f"Fichier cache supprimé: {file}")
                deleted = True
            except Exception as e:
                print(f"Erreur lors de la suppression de {file}: {e}")

    if deleted:
        print("\nDéconnexion réussie. Vous devrez vous authentifier à nouveau lors de la prochaine extraction.")
        return True
    else:
        print("\nAucune session active trouvée.")
        return False


def run_extraction_process(force_new_auth=False):
    """Exécute le processus d'extraction des données Spotify"""
    print_header("EXTRACTION DES DONNÉES SPOTIFY")
    tracks, features = extract_spotify_data(force_new_auth=force_new_auth)

    if tracks is not None:
        print(
            f"\nExtraction réussie: {len(tracks)} titres avec {len(features) if features is not None else 0} caractéristiques audio.")
        return True
    else:
        print("\nÉchec de l'extraction des données. Vérifiez vos identifiants Spotify et la connexion Internet.")
        return False


def run_processing_step():
    """Exécute l'étape de traitement et nettoyage des données"""
    print_header("TRAITEMENT ET NETTOYAGE DES DONNÉES")
    cleaned_data = process_data()

    if cleaned_data is not None:
        print(f"\nTraitement réussi: {len(cleaned_data)} titres après nettoyage.")
        return True
    else:
        print("\nÉchec du traitement des données. Assurez-vous que l'extraction a réussi.")
        return False


def run_analysis_step():
    """Exécute l'étape d'analyse des données"""
    print_header("ANALYSE DES DONNÉES")
    stats, audio_analysis, categorized_df = analyze_data()

    if stats:
        print("\nStatistiques de base:")
        print(f"- Total des titres: {stats['total_tracks']}")
        print(f"- Artistes uniques: {stats['unique_artists']}")

        print("\nTop 5 artistes:")
        for i, (artist, count) in enumerate(list(stats['top_artists'].items())[:5]):
            print(f"  {i + 1}. {artist}: {count} titres")

        if 'playlist_counts' in stats:
            print("\nRépartition par playlist:")
            for i, (playlist, count) in enumerate(list(stats['playlist_counts'].items())[:5]):
                print(f"  {i + 1}. {playlist}: {count} titres")

        # Vérifier si l'analyse des caractéristiques audio est disponible
        if audio_analysis and 'error' in audio_analysis:
            print("\nL'analyse des caractéristiques audio n'est pas disponible.")
            print("Certaines fonctionnalités comme les recommandations basées sur la similarité")
            print("et les visualisations avancées ne seront pas disponibles.")

        # Vérifier si la catégorisation a été possible
        if categorized_df is not None and 'energy_dance_category' in categorized_df.columns:
            print(f"\nCatégories créées: {categorized_df['energy_dance_category'].nunique()}")
            print(f"Répartition des catégories:")
            print(categorized_df['energy_dance_category'].value_counts().head())
        elif categorized_df is not None:
            print("\nLa catégorisation basée sur les caractéristiques audio n'a pas pu être effectuée.")
            print("Mais l'analyse de base des titres est disponible.")

        return True
    else:
        print("\nÉchec de l'analyse des données. Assurez-vous que le traitement a réussi.")
        return False


def run_visualization_step():
    """Exécute l'étape de création des visualisations"""
    print_header("CRÉATION DES VISUALISATIONS")
    viz_paths = create_visualizations()

    if viz_paths:
        print(
            f"\nVisualisation réussie: {len(viz_paths)} graphiques créés dans {os.path.join(DATA_DIR, 'visualizations')}")
        return True
    else:
        print("\nÉchec de la création des visualisations.")
        return False


def run_recommendation_demo():
    """Exécute un exemple de recommandations"""
    print_header("DÉMONSTRATION DU SYSTÈME DE RECOMMANDATION")

    # Charger les données catégorisées
    categorized_path = os.path.join(DATA_DIR, "categorized_tracks.csv")

    if not os.path.exists(categorized_path):
        print("Données catégorisées non disponibles. Exécutez d'abord l'analyse.")
        return False

    import pandas as pd
    df = pd.read_csv(categorized_path)

    if df.empty:
        print("Données catégorisées vides.")
        return False

    # Afficher un titre aléatoire pour tester les recommandations similaires
    sample_track = df.sample(1).iloc[0]
    print(f"\nTitre de test: {sample_track['track_name']} par {sample_track['artist_name']}")

    # Obtenir des titres similaires
    print("\nRecherche de titres similaires...")
    similar_tracks = get_recommendations(track_id=sample_track['track_id'], size=5)

    if similar_tracks is not None:
        print("\nTitres similaires recommandés:")
        for i, (_, track) in enumerate(similar_tracks.iterrows()):
            print(
                f"  {i + 1}. {track['track_name']} par {track['artist_name']} (Score: {track['similarity_score']:.2f})")

    # Tester une génération de playlist par ambiance
    print("\nGénération d'une playlist 'energetic'...")
    energetic_playlist = get_recommendations(mood='energetic', size=5)

    if energetic_playlist is not None:
        print("\nPlaylist énergique recommandée:")
        for i, (_, track) in enumerate(energetic_playlist.iterrows()):
            print(f"  {i + 1}. {track['track_name']} par {track['artist_name']}")

    # Tester la découverte de nouveaux titres
    print("\nRecherche de découvertes musicales...")
    discoveries = get_recommendations(discover=True, size=5)

    if discoveries is not None:
        print("\nDécouvertes recommandées:")
        for i, (_, track) in enumerate(discoveries.iterrows()):
            print(f"  {i + 1}. {track['track_name']} par {track['artist_name']}")

    return True


def run_top_artists_analysis(force_new_auth=False):
    """Exécute l'analyse des artistes les plus écoutés"""
    print_header("ANALYSE DES ARTISTES LES PLUS ÉCOUTÉS")

    results = analyze_top_artists(force_new_auth=force_new_auth)

    if results:
        # Afficher les artistes les plus écoutés pour différentes périodes
        print("\nVos artistes les plus écoutés:")

        print("\nDernières semaines:")
        for artist in results['short_term'][:5]:  # Top 5
            print(
                f"{artist['position']}. {artist['name']} (Genres: {', '.join(artist['genres'][:3]) if artist['genres'] else 'Non spécifié'})")

        print("\n6 derniers mois:")
        for artist in results['medium_term'][:5]:  # Top 5
            print(
                f"{artist['position']}. {artist['name']} (Genres: {', '.join(artist['genres'][:3]) if artist['genres'] else 'Non spécifié'})")

        print("\nDe tous les temps:")
        for artist in results['long_term'][:5]:  # Top 5
            print(
                f"{artist['position']}. {artist['name']} (Genres: {', '.join(artist['genres'][:3]) if artist['genres'] else 'Non spécifié'})")

        # Demander si l'utilisateur souhaite créer une playlist
        create_playlist = input(
            "\nSouhaitez-vous créer une playlist avec les meilleurs titres de ces artistes? (o/n): ")

        if create_playlist.lower() == 'o':
            # Demander la période
            print("\nChoisissez la période:")
            print("1. Dernières semaines")
            print("2. 6 derniers mois")
            print("3. De tous les temps")

            period_choice = input("Votre choix (1-3): ")

            time_range = 'medium_term'  # Par défaut
            if period_choice == '1':
                time_range = 'short_term'
            elif period_choice == '3':
                time_range = 'long_term'

            # Créer la playlist
            analyzer = TopArtistsAnalyzer()
            playlist = analyzer.create_top_artists_playlist(time_range=time_range)

            if playlist:
                print(f"\nPlaylist créée: {playlist['name']}")
                print(f"URL: {playlist['url']}")
                print(f"Nombre de titres: {playlist['tracks_count']}")

        return True
    else:
        print("\nÉchec de l'analyse des artistes les plus écoutés.")
        return False


def main():
    """Fonction principale du programme"""
    print_header("ANALYSEUR ET GÉNÉRATEUR DE PLAYLISTS MUSICALES")
    print("Ce programme analyse vos playlists Spotify et génère des recommandations personnalisées.")

    # Vérifier la configuration
    if not check_setup():
        print("\nConfiguration incomplète. Veuillez corriger les problèmes avant de continuer.")
        sys.exit(1)

    # Menu principal
    while True:
        print("\nQue souhaitez-vous faire?")
        print("1. Extraire les données de Spotify")
        print("2. Nettoyer et traiter les données")
        print("3. Analyser les données")
        print("4. Créer des visualisations")
        print("5. Tester le système de recommandation")
        print("6. Exécuter tout le pipeline")
        print("7. Se déconnecter du compte Spotify")
        print("8. Effacer toutes les données et recommencer")
        print("9. Forcer une nouvelle connexion Spotify")
        print("10. Voir vos artistes les plus écoutés et créer une playlist")
        print("0. Quitter")

        choice = input("\nVotre choix (0-10): ")

        if choice == '1':
            run_extraction_process()
        elif choice == '2':
            run_processing_step()
        elif choice == '3':
            run_analysis_step()
        elif choice == '4':
            run_visualization_step()
        elif choice == '5':
            run_recommendation_demo()
        elif choice == '6':
            # Exécuter toutes les étapes
            if run_extraction_process():
                time.sleep(1)
                if run_processing_step():
                    time.sleep(1)
                    if run_analysis_step():
                        time.sleep(1)
                        run_visualization_step()
                        time.sleep(1)
                        run_recommendation_demo()
        elif choice == '7':
            # Se déconnecter de Spotify
            logout_spotify()
        elif choice == '8':
            # Effacer toutes les données
            if input("Êtes-vous sûr de vouloir supprimer toutes les données? (o/n): ").lower() == 'o':
                clear_data()
        elif choice == '9':
            # Forcer une nouvelle connexion
            print("Forçage d'une nouvelle connexion Spotify...")
            # D'abord déconnecter
            logout_spotify()
            # Puis forcer une nouvelle connexion
            run_extraction_process(force_new_auth=True)
        elif choice == '10':
            # Analyser les artistes les plus écoutés
            run_top_artists_analysis(force_new_auth=False)
        elif choice == '0':
            print("\nMerci d'avoir utilisé l'analyseur de playlists musicales!")
            sys.exit(0)
        else:
            print("\nChoix non valide. Veuillez réessayer.")

        input("\nAppuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    main()