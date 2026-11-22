# importer les donnees et les nettoyer pour pouvoir les merge / analyser
##########################################################################################
#                                                                                        #
#                                  import packages et paramètres                         #
#                                                                                        #                      
##########################################################################################

import numpy as np 
import json 
import geopandas as gpd
from shapely.geometry import shape
import pandas as pd
import gdown
import os

os.chdir("/home/onyxia/work/Projet-python-2A-") #Pour que ça fonctionne sur vscode depuis sspcloud chez Joceran

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

## paramètres (pour les données foncières) 
FILE_DVF_PLUS_ID = "1Mnsnm-OCvw-5zLuVBf6p41NtDChE_yg1"
FICHIER_LOCAL_DVF_PLUS = "dvf_plus_d75.csv"


##########################################################################################
#                                                                                        #
#                                  import data                                           #
#                                                                                        #                      
##########################################################################################

######################## espaces verts actuels et supplémentaires ########################

ev_actuels = pd.read_csv("data/1.data_brute/espaces_verts.csv", sep=";", encoding="utf-8")
ev_supp = pd.read_csv("data/1.data_brute/espaces_verts_supplementaires.csv", sep=";", encoding="utf-8")

# visualisation 
print(ev_actuels.head(10))
print(ev_supp.head(10))

######################## Parcs et Jardins ouverts au public ########################

parcs_publics = gpd.read_file("data/1.data_brute/PJ_75_2021.gpkg")
print(parcs_publics.info())

#################################### données foncières (2023-2025) ###################################
# fichiers volumineux donc télécharge automatiquement en local à partir du drive partagé (mettre nom dans le gitignore)
# Téléchargement uniquement si le fichier n'existe pas déjà

if not os.path.exists(FICHIER_LOCAL_DVF_PLUS):
    gdown.download(id=FILE_DVF_PLUS_ID, output=FICHIER_LOCAL_DVF_PLUS, quiet=False)
dvf_plus = pd.read_csv(FICHIER_LOCAL_DVF_PLUS, sep="|", low_memory=False)

#############################’############################################################
#                                                                                        #
#                                  nettoyage des données                                 #
#                                                                                        #                      
##########################################################################################

############################on ne conserve que Paris centre (75) #########################
ev_actuels = ev_actuels[ev_actuels["Code postal"].astype("string").str.startswith("75")]

############################ on refusionne les parcs séparés en sous-parties #########################

# Nombre d'occurrences de chaque nom
occurrences = parcs_publics["nom"].value_counts()

# Liste des noms espaces à fusionner
noms_a_fusionner = occurrences[occurrences > 1].index

# Séparer les espaces à fusionner des autres
a_fusionner = parcs_publics[parcs_publics["nom"].isin(noms_a_fusionner)]
a_conserver = parcs_publics[~parcs_publics["nom"].isin(noms_a_fusionner)]

# Fusionner les géométries
fusionnes = a_fusionner.dissolve(by="nom", as_index=False)

# Reconstituer la base
parcs_publics_nettoyee = gpd.GeoDataFrame(pd.concat([fusionnes, a_conserver], ignore_index=True), crs=parcs_publics.crs)

############################ sélection des ventes pour dvf ###############################

#1. on selectionnes les ventes d'un appartement seul 
# On garde les dépendances pr le moment (on fait deux bases à la fin)
# on ne garde pas les maisons car trop peu nombreuses et prix dépend pas que de la surface 
dvf_plus = dvf_plus[dvf_plus['anneemut'].between(2023, 2025)] #année de mutation
dvf_plus = dvf_plus[dvf_plus['libnatmut'] == 'Vente'] #on ne garde que les ventes (on exclut "vente en l'état futur d'achèvement" et "échange")
dvf_plus = dvf_plus[dvf_plus['nblocapt'] == 1] # nombre d'appartements ayant muté 
dvf_plus = dvf_plus[dvf_plus['nblocmai'] == 0] # nombre de maisons ayant muté 
dvf_plus = dvf_plus[dvf_plus['nblocact'] == 0] # nombre de locaux d'activité ayant muté
dvf_plus = dvf_plus[dvf_plus['codtypbien'] == 121]  # Un appartement, selon cette livraison

#2. on évite les ventes complexes (plusieurs communes, dispositions ou parcelles)
dvf_plus = dvf_plus[dvf_plus['nbcomm'] == 1] # nombre de communes 
dvf_plus = dvf_plus[dvf_plus['nbdispo'] == 1] # nombre de dispositions associées à la mutation (98% des mutations ont une seule disposition)
dvf_plus = dvf_plus[dvf_plus['nbpar'] == 1] # nombre de parcelles 


# remarque : une mutation peut comprendre un mélange des biens suivants : une parcelle nue / un local / un volume
# Le code idmutation est présent dans toutes les tables de DV3F et permet d’effectuer très simplement des jointures entre celles-ci.

########################### on ne conserve que les types d'espaces verts utiles ###########

# visualisation pour faire le tri 

# (ev_actuels[["Typologie d'espace vert", "Catégorie"]]
#     .drop_duplicates()
#     .sort_values(["Typologie d'espace vert", "Catégorie"]))

categories_to_keep = [ 'Jardin',
 'Square',
 'Promenade',
 #'Murs vegetalises',
 'Espace Vert',
 'Jardin partage',
 'Parc',
 'Pelouse',
 'Arboretum',
 'Mail',
 "Jardin d'immeubles",
 'Archipel',
 'Foret urbaine',
 'Terrain de boules',
 'jardiniere',
 'Jardiniere',
 'Cimetière'
 'Bois',
 'Ile']
types_to_keep = ["Bois", "Ephémères, partagés, pédagogiques", "Jardinets décoratifs", "Promenades ouvertes",
                      "Végétalisation d'espace public"]
ev_actuels = ev_actuels[ev_actuels["Typologie d'espace vert"].isin(types_to_keep)]
ev_actuels = ev_actuels[ev_actuels["Catégorie"].isin(categories_to_keep)]

# stats après tri : il reste 762 lignes sur 2535 au départ 

############################ on enlève les colonnes inutiles #############################
col_to_drop = [
    (ev_actuels, ["Identifiant espace vert", "Présence cloture",
                                    "Année de rénovation","Ancien nom de l'espace vert", 
                                      "Année de changement de nom","Nombre d'entités", 
                                        "Ouverture 24h_24h",
                                        "ID_DIVISION", "ID_ATELIER_HORTICOLE", "IDA3D_ENB", "ID_EQPT",
                                        "Compétence","last_edited_user",
                                        "last_edited_date" ]),
    (ev_supp, ["Type d'opération", "Secteur administratif"]) ]

for df, cols in col_to_drop:
    df.drop(columns=cols, inplace=True)


############################### harmonisation des types ##################################
##
col_to_integer = [
    (ev_actuels, ["Adresse - Numéro", "Code postal", "Surface calculée", "Superficie totale réelle",
            "Surface horticole", "Année de l'ouverture"]),
    (ev_supp, ["M2 d’espaces verts supplémentaires"])
]

for df, cols in col_to_integer:
    for col in cols:
        df[col] = df[col].astype("Int64")

#print(ev_actuels.info())
#print(ev_supp.info())

############################## harmonisation des valeurs nulles ou NAN #####################

# on détecte les valeurs qui correspondent à des NaN (certains 0 sont des NaN, d'autres sont des valeurs réelles)
#print(ev_actuels.describe())
#print(ev_supp.describe())

col_zero_to_nan = [(ev_actuels, ["Adresse - Numéro"])]
col_val_to_nan = [(ev_actuels, ["Année de l'ouverture"])]

for df, cols in col_zero_to_nan:
    for col in cols:
        df[col] = df[col].replace(0, np.nan)

for df, cols in col_val_to_nan:
    for col in cols:
        df[col] = df[col].replace(9999, np.nan)

# On supprimes les données manquantes ou atypiques pour dvf_plus 
necessaires = ['valeurfonc', 'sbatapt', 'geompar_x', 'geompar_y']
dvf_plus = dvf_plus.dropna(subset=necessaires).copy()
dvf_plus = dvf_plus[dvf_plus['valeurfonc'] > 0].copy()
dvf_plus = dvf_plus[dvf_plus['sbatapt'] > 9].copy() # chat voulait limiter à 300 m2 ??

dvf_plus['prix_m2'] = dvf_plus['valeurfonc'] / dvf_plus['sbatapt'] # on rajoute une colonne px_m2
dvf_plus = dvf_plus[dvf_plus['prix_m2'].between(1000, 30000)].copy()                                      

############################ création des variables utiles pour la régression ############

dvf_plus['avec_dependance'] = (dvf_plus['nblocdep'] > 0).astype(int)
dvf_plus['nb_pieces'] = (
    dvf_plus['nbapt1pp'] + 2 * dvf_plus['nbapt2pp'] + 3 * dvf_plus['nbapt3pp']
    + 4 * dvf_plus['nbapt4pp'] + 5 * dvf_plus['nbapt5pp']
)  # 5 signifie 5 pieces ou plus

dvf_plus['log_prix_m2'] = np.log(dvf_plus['prix_m2'])
dvf_plus['log_surface'] = np.log(dvf_plus['sbatapt'])

############################ harmonisation des noms de colonnes ##########################
# pr dvf : on garde les variables intéressantes et on donne des noms simples 
colonnes = {
    'idmutation': 'id_vente',
    'datemut': 'date',
    'anneemut': 'annee',
    'moismut': 'mois',
    'l_codinsee': 'code_arrondissement',
    'l_idpar': 'id_parcelle',
    'valeurfonc': 'prix_euros',
    'sbatapt': 'surface_m2',
    'prix_m2': 'prix_m2',
    'nblocdep': 'nb_dependances',
    'avec_dependance': 'avec_dependance',
    'nb_pieces': 'nb_pieces',
    'geompar_x': 'x_lambert93',
    'geompar_y': 'y_lambert93',
    'log_prix_m2': 'log_prix_m2',
    'log_surface': 'log_surface',
}
dvf_plus = dvf_plus[list(colonnes)].rename(columns=colonnes)
dvf_plus = dvf_plus.sort_values(['date', 'id_vente']).reset_index(drop=True)

# 7. Verifications 
assert dvf_plus['id_vente'].is_unique, 'Attention : ventes en double'
assert dvf_plus['prix_m2'].gt(0).all(), 'Attention : prix au m2 invalide'


######################### création des deux couches géométriques #########################

# on transforme les deux tableaux en couches géographiques (GeoDataFrames) pour pouvoir les croiser spatialement
# tout en convertissant ev_actuels en Lambert93 

# --- Espaces verts : polygones en WGS84 --

ev = ev_actuels.dropna(subset=["Geo Shape"]).copy() #on enlève les lignes sans géométrie (il en reste 762)

#1. création colonne geometry avec pr chaque ligne : Geoshape contient le contour sous forme JSON, transformé en dictionnaire par json.loads (issinstance laisse passer les valeurs qui sont déjà des dictionnaires)
# shape convertit le dictionnaire en polygone utilisable par geopandas 
ev["geometry"] = ev["Geo Shape"].apply(
    lambda s: shape(json.loads(s) if isinstance(s, str) else s) 
)

#2. on crée le Geodataframe en indiquant quelle colonne contient la géométrie avec to_crs qui convertit en Lambert93
gdf_ev = gpd.GeoDataFrame(ev, geometry="geometry", crs="EPSG:4326").to_crs("EPSG:2154")

# --- DVF : points en Lambert 93 ---
dvf_plus.dropna(subset=["x_lambert93", "y_lambert93"]) #garde seulement les ventes qui ont des coordonnées 
gdf_dvf = gpd.GeoDataFrame(
    dvf_plus,
    geometry=gpd.points_from_xy(dvf_plus["x_lambert93"], dvf_plus["y_lambert93"]), #points_from_xy crée un point pour chaque vente à partir de ses coordonnées x et y 
    crs="EPSG:2154", # déclare que les coordonnées sont en Lambert93 (EPSG:2154) : pas de conversion
)

# CONCLUSION : gdf_ev contient des polygones et gdf_dvf des points. Ils peuvent donc être croisés et les distances sont en mètres

############## calcul de la distance de chaque logement à l'espace vert le plus proche ########
### à modifier pour ne prendre en compte que les espaces verts avec une taille suffisante , et vérifier que accessibles au public

#1 On ne garde que les espaces verts de taille suffisante 
gdf_ev = gdf_ev[gdf_ev["Surface calculée"] >= 80]
gdf_ev["id_ev"] = gdf_ev.index  # on crée un identifiant unique pour chaque espace vert

#jointure spatiale 
ev_proche_1 = gpd.sjoin_nearest(
    gdf_dvf[["geometry"]],
    gdf_ev[["id_ev", "Typologie d'espace vert","Nom de l'espace vert", "Catégorie", "geometry", "Surface calculée"]],
    how="left",
    distance_col="dist_ev_m",
)

RAYONS = [100, 200, 300]
# 300m = 4m à pied, distance recommandée par l'OMS Europe 
# 500 m = 6 min à pied 
# 1000 m = 12 min à pied (distances à vol d'oiseau, sous estiment le trajet réel à pied)

ev_g = gdf_ev[["id_ev", "Nom de l'espace vert", "geometry", "Surface calculée"]].copy()
ev_g["nom"] = ev_g["Nom de l'espace vert"].fillna("Sans nom")

# 1. tous les couples (logement, espace vert) à moins de 1 000 m
zone = gdf_dvf[["geometry"]].copy()
zone["geometry"] = zone.geometry.buffer(max(RAYONS))
paires = gpd.sjoin(zone, ev_g, how="inner", predicate="intersects")

# 2. distance exacte de chaque couple (le point du polygone le plus proche)
paires["dist_m"] = gdf_dvf.geometry.loc[paires.index].distance(
    ev_g.geometry.loc[paires["index_right"]], align=False
)

# 3. une colonne par rayon : dictionnaire {nom: distance}, et le nombre d'espaces verts
for r in RAYONS:
    p = paires[paires["dist_m"] <= r]

    # distance minimale par (logement, nom), un parc découpé en plusieurs polygones = une seule entrée (distance minimale, surface du parc)
    d = (p.groupby([p.index, "nom"])
           .agg(dist=("dist_m", "min"), surface=("Surface calculée", "max"))
           .reset_index())
    d.columns = ["idx", "nom", "dist", "surface"]
    d = d.sort_values(["idx", "dist"])

    # dictionnaire {nom: {"dist_m": ..., "surface_m2": ...}} par logement, trié par distance
    dicts = {}
    for idx, nom, dist, surf in zip(d["idx"], d["nom"], d["dist"], d["surface"]):
        dicts.setdefault(idx, {})[nom] = {
            "dist_m": int(round(dist)),
            "surface_m2": None if pd.isna(surf) else int(round(surf)),
        }

    dvf_plus[f"ev_{r}m"] = [dicts.get(i, {}) for i in dvf_plus.index]
    dvf_plus[f"nb_ev_{r}m"] = dvf_plus[f"ev_{r}m"].apply(len)
    
# Une seule ligne par logement (en cas d'égalité de distance)
ev_proche_1 = ev_proche_1[~ev_proche_1.index.duplicated(keep="first")]

# Ajout à dvf_plus (affectation par index, NaN pour les logements sans coordonnées)
dvf_plus["id_ev_proche"] = ev_proche_1["id_ev"]
dvf_plus["typologie_ev_proche"] = ev_proche_1["Typologie d'espace vert"]
dvf_plus["categorie_ev_proche"] = ev_proche_1["Catégorie"]
dvf_plus["dist_ev_m"] = ev_proche_1["dist_ev_m"]
dvf_plus["nom_ev_proche"] = ev_proche_1["Nom de l'espace vert"]
dvf_plus["surface_ev_proche"] = ev_proche_1["Surface calculée"]

############## calcul de la surface des parcs et jardins publics  ########
parcs_publics_nettoyee["surface_m2"] = parcs_publics_nettoyee.geometry.area

##########################################################################################
#                                                                                        #
#                         Enregistrement des données nettoyées                           #
#                                                                                        #                      
##########################################################################################

# enregistrement des données 
dvf_plus.to_csv(os.path.join("data/2.data_nettoyee", 'dvf_paris_nettoyee.csv'), index=False)
ev_actuels.to_csv(os.path.join("data/2.data_nettoyee", 'ev_actuels_nettoyes.csv'), index=False)
ev_supp.to_csv(os.path.join("data/2.data_nettoyee", 'ev_supp_nettoyes.csv'), index=False)
parcs_publics_nettoyee.to_file("data/2.data_nettoyee/parcs_publics_nettoyee.gpkg", layer="parcs_publics_nettoyee", driver="GPKG")
# version sans dépendances 
sans_dependances = dvf_plus[dvf_plus['nb_dependances'] == 0].copy()
sans_dependances.to_csv(os.path.join("data/2.data_nettoyee", 'dvf_paris_sans_dependances.csv'), index=False)

print(list(dvf_plus.columns))