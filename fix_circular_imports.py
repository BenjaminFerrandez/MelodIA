def resolve_circular_imports():
    """
    Résout les importations circulaires en réorganisant certaines importations
    """
    print("Résolution des importations circulaires...")

    # Patch pour data_analysis.py
    import sys
    from importlib import reload

    # Première passe pour charger les modules de base
    import data_processing
    import config

    # Recharger data_analysis proprement
    if 'data_analysis' in sys.modules:
        reload(sys.modules['data_analysis'])

    # Informer l'utilisateur
    print("✅ Importations réorganisées avec succès")