"""Vérifier les colonnes nécessaires et calculer les variables des modèles."""
import numpy as np
import pandas as pd


def lire_ventes(fichier):
    base = pd.read_csv(fichier)
    colonnes = [
        "id_vente", "id_parcelle", "date", "code_arrondissement", "prix_euros",
        "surface_m2", "nb_pieces", "nb_dependances", "x_lambert93", "y_lambert93",
        "id_parc", "dist_ev_m", "surface_parc_m2",
    ]
    absentes = sorted(set(colonnes) - set(base.columns))
    if absentes:
        raise ValueError("Colonnes à ajouter ou renommer : " + ", ".join(absentes))
    ventes = base[colonnes].copy()
    if ventes.isna().any().any():
        raise ValueError("Valeurs manquantes : " + str(ventes.isna().sum().loc[lambda n: n > 0]))
    if ventes["id_vente"].duplicated().any():
        raise ValueError("La base doit contenir une seule ligne par vente.")
    for nom in ["prix_euros", "surface_m2", "surface_parc_m2"]:
        if not ventes[nom].gt(0).all():
            raise ValueError(f"{nom} doit être strictement positif.")
    if ventes["dist_ev_m"].lt(0).any():
        raise ValueError("La distance doit être positive ou nulle.")
    # Même règle de sélection que dans la première analyse.
    ventes = ventes.loc[ventes["prix_euros"] != 1].copy()
    prix_m2 = ventes["prix_euros"] / ventes["surface_m2"]
    ventes["log_prix_m2"] = np.log(prix_m2)
    ventes["log_surface"] = np.log(ventes["surface_m2"])
    ventes["avec_dependance"] = ventes["nb_dependances"].gt(0).astype(int)
    ventes["trimestre"] = pd.to_datetime(ventes["date"]).dt.to_period("Q").astype(str)
    ventes["distance_100m"] = ventes["dist_ev_m"] / 100
    ventes["log_surface_parc_ha"] = np.log(ventes["surface_parc_m2"] / 10000)
    ventes["prix_bas"] = prix_m2.lt(1000)
    ventes["prix_eleve"] = prix_m2.gt(30000)
    return ventes
