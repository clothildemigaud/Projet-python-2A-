from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


# Les chemins partent du dossier qui contient ce script.
dossier = Path(__file__).resolve().parent
donnees = dossier / "data" / "2.data_nettoyee"


# 1. Charger les ventes sans dépendances

colonnes = [
    "id_vente", "id_parcelle", "date", "prix_m2", "surface_m2",
    "nb_pieces", "nb_dependances", "code_arrondissement",
    "x_lambert93", "y_lambert93", "dist_ev_m",
]

ventes = pd.read_csv(
    donnees / "dvf_paris_sans_dependances.csv",
    usecols=colonnes,
)

ventes = ventes.loc[
    ventes["nb_dependances"].eq(0)
    & ventes["prix_m2"].between(1000, 30000)
].copy()

assert ventes["id_vente"].is_unique, "Plusieurs lignes ont le même identifiant de vente."
assert ventes.notna().all().all(), "Certaines ventes ont des informations manquantes."
assert ventes["surface_m2"].gt(0).all(), "Certaines surfaces sont nulles ou négatives."
assert ventes["dist_ev_m"].ge(0).all(), "Certaines distances de l'ancien inventaire sont négatives."

ventes["log_prix_m2"] = np.log(ventes["prix_m2"])
ventes["log_surface"] = np.log(ventes["surface_m2"])
ventes["trimestre"] = pd.to_datetime(ventes["date"]).dt.to_period("Q").astype(str)


# 2. Trouver le parc, le jardin ou le square le plus proche

parcs = gpd.read_file(donnees / "parcs_publics_nettoyee.gpkg").to_crs(2154)
categories = ["Parc", "Jardin", "Square"]
parcs = parcs.loc[parcs["nature"].isin(categories), ["nom", "geometry"]].copy()

assert len(parcs) > 0, "Aucun parc, jardin ou square trouvé."
assert parcs["nom"].notna().all(), "Certains sites n'ont pas de nom."
assert parcs["nom"].is_unique, "Plusieurs sites portent le même nom."

parcs.geometry = parcs.geometry.make_valid()

# Plusieurs ventes peuvent se situer au même endroit.
# On calcule les distances une seule fois par emplacement.
xy = ["x_lambert93", "y_lambert93"]
lieux = ventes[xy].drop_duplicates().reset_index(drop=True)
points = gpd.points_from_xy(lieux["x_lambert93"], lieux["y_lambert93"])
lieux = gpd.GeoDataFrame(lieux, geometry=points, crs=2154)

proches = gpd.sjoin_nearest(lieux, parcs, how="left", distance_col="distance_m")

# Si deux sites sont exactement à la même distance, on garde le premier
# par ordre alphabétique pour éviter de compter deux fois le logement.
proches = proches.sort_values("nom").drop_duplicates(xy)


# 3. Mesurer la surface de parcs, jardins et squares autour de chaque logement

# Réunir les polygones évite de compter deux fois les surfaces qui se chevauchent.
morceaux = gpd.GeoSeries(parcs.geometry.union_all(), crs=2154)
morceaux = morceaux.explode().reset_index(drop=True)

for rayon in [500, 1000]:
    print(f"Calcul des surfaces dans un rayon de {rayon} m…", flush=True)
    disques = lieux.geometry.buffer(rayon)

    # Repérer les polygones qui touchent chaque disque.
    i, j = morceaux.sindex.query(disques, predicate="intersects")

    # Compter uniquement la partie de chaque polygone située dans le disque.
    surfaces = disques.iloc[i].intersection(morceaux.iloc[j], align=False).area
    total = surfaces.groupby(i).sum()

    # Un emplacement sans parc dans le rayon reçoit une surface de zéro.
    lieux[f"parcs_{rayon}m_ha"] = total.reindex(lieux.index, fill_value=0) / 10000

mesures = proches[xy + ["nom", "distance_m"]].merge(
    lieux[xy + ["parcs_500m_ha", "parcs_1000m_ha"]],
    on=xy,
    validate="one_to_one",
)

base = ventes.merge(mesures, on=xy, how="left", validate="many_to_one")
assert len(base) == len(ventes)
assert base["distance_m"].ge(0).all()

# Les deux distances sont exprimées en centaines de mètres.
base["distance_ev_100m"] = base["dist_ev_m"] / 100   # Ancien inventaire
base["distance_100m"] = base["distance_m"] / 100     # Parcs, jardins et squares


# 4. Estimer les régressions sur les mêmes ventes

# M1 : relation brute entre la distance au parc, jardin ou square et le prix au m².
m1 = "log_prix_m2 ~ distance_100m"

# Les deux versions de M2 utilisent exactement les mêmes contrôles.
controles = " + log_surface + C(nb_pieces) + C(trimestre) + C(code_arrondissement)"

# M2 avec la distance à l'espace vert le plus proche dans l'ancien inventaire.
m2_espaces_verts = "log_prix_m2 ~ distance_ev_100m" + controles

# M2 avec la distance au parc, jardin ou square le plus proche.
m2 = m1 + controles

# M3 : comparer les ventes qui ont le même parc, jardin ou square le plus proche.
m3 = m2 + " + C(nom)"

# M4 : ajouter la surface cumulée dans le rayon de 500 m ou de 1 km.
formules = {
    "M1": m1,
    "M2_espaces_verts": m2_espaces_verts,
    "M2": m2,
    "M3": m3,
    "M4_500m": m3 + " + parcs_500m_ha",
    "M4_1km": m3 + " + parcs_1000m_ha",
}

variables_a_afficher = [
    "distance_ev_100m",
    "distance_100m",
    "parcs_500m_ha",
    "parcs_1000m_ha",
]

lignes = []
for nom_modele, formule in formules.items():
    # Des ventes situées sur une même parcelle peuvent avoir des erreurs corrélées.
    modele = smf.ols(formule, data=base, missing="raise").fit(
        cov_type="cluster",
        cov_kwds={"groups": base["id_parcelle"]},
    )

    for variable in variables_a_afficher:
        if variable in modele.params:
            bas, haut = modele.conf_int().loc[variable]
            lignes.append({
                "modele": nom_modele,
                "variable": variable,
                "coefficient": modele.params[variable],
                "p_value": modele.pvalues[variable],
                "IC95_bas": bas,
                "IC95_haut": haut,
                "R2": modele.rsquared,
                "R2_ajuste": modele.rsquared_adj,
                "n": int(modele.nobs),
            })

resultats = pd.DataFrame(lignes)
print(f"{len(base)} ventes et {len(parcs)} parcs, jardins et squares.")
print(resultats.round(4).to_string(index=False))
resultats.to_csv(dossier / "resultats_regressions.csv", index=False)

# penser à analyser les résultats dans le notebook 
# peut être comparer aux résultats d'études sur le sujet : par ex https://www.defiscalisation.immo/informations/parc-jardin-les-exterieurs-font-grimper-le-prix-des-logements/
# soutient que un appartement (dans toute la france) qui dispose d'un parc à 10-15 min voit son prix augmenter de 1.1% en moyenne / 8% quand moins de 5 min 
# + évoque le fait que à Paris, la proximité joue surtout sur l'acte d'achat 
