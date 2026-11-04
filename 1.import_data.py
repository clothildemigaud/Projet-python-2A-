# importer les donnees et les nettoyer pour pouvoir les merge / analyser
##########################################################################################
#                                                                                        #
#                                  import packages et paramètres                         #
#                                                                                        #                      
##########################################################################################

import numpy as np 
import pandas as pd
import zipfile
import gdown
import os

os.chdir("/home/onyxia/work/Projet-python-2A-") #Pour que ça fonctionne sur vscode depuis sspcloud chez Joceran

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

## paramètres (pour les données foncières) 
# pr le fichier zip 
FILE_DVF_PLUS_ID = "1Mnsnm-OCvw-5zLuVBf6p41NtDChE_yg1"
FICHIER_LOCAL_DVF_PLUS = "dvf_plus_d75.csv"
#anciennes bases 
FILE_ID_26 = "1A9e-cSJgbGsv7mFS24ncDGyU7ckDr7Db"
FICHIER_LOCAL_26 = "DVF-2026-S1.txt"
FILE_ID_25 = "1mPm7rU1sN5c3udpn_VbAFNhqNxSIRdUs"
FICHIER_LOCAL_25 = "ValeursFoncieres-2025.txt"

##########################################################################################
#                                                                                        #
#                                  import data                                           #
#                                                                                        #                      
##########################################################################################



######################## espaces verts actuels et supplémentaires ########################

ev_actuels = pd.read_csv("data/espaces_verts.csv", sep=";", encoding="utf-8")
ev_supp = pd.read_csv("data/espaces_verts_supplementaires.csv", sep=";", encoding="utf-8")

# visualisation 
print(ev_actuels.head(10))
print(ev_supp.head(10))

#################################### données foncières ###################################
# fichiers volumineux donc télécharge automatiquement en local à partir du drive partagé
# Téléchargement uniquement si le fichier n'existe pas déjà

# dvf + : ventes d'appartement sur 2023 -2025
if not os.path.exists(FICHIER_LOCAL_DVF_PLUS):
    gdown.download(id=FILE_DVF_PLUS_ID, output=FICHIER_LOCAL_DVF_PLUS, quiet=False)
dvf_plus = pd.read_csv(FICHIER_LOCAL_DVF_PLUS, sep="|", low_memory=False)

# anciennes bases 
# pour dvf 2026
if not os.path.exists(FICHIER_LOCAL_26):
    gdown.download(id=FILE_ID_26, output=FICHIER_LOCAL_26, quiet=False)

dvf_2026 = pd.read_csv(
    FICHIER_LOCAL_26,
    sep="|",            # les fichiers DVF sont séparés par des barres verticales
    decimal=",",        # montants avec virgule décimale
    low_memory=False,
    encoding="utf-8",   # essaie "latin-1" si les accents sont cassés
)
#visualisation 
print(dvf_2026.shape)
print(dvf_2026.head())

#pour dvf 2025
if not os.path.exists(FICHIER_LOCAL_25):
    gdown.download(id=FILE_ID_25, output=FICHIER_LOCAL_25, quiet=False)

dvf_2025 = pd.read_csv(
    FICHIER_LOCAL_25,
    sep="|",            
    decimal=",",        
    low_memory=False,
    encoding="utf-8",   
)
#visualisation 
print(dvf_2025.shape)
print(dvf_2025.head())

#############################’#############################################################
#                                                                                        #
#                                  nettoyage des données                                 #
#                                                                                        #                      
##########################################################################################

############################on ne conserve que Paris centre (75) #########################
ev_actuels = ev_actuels[ev_actuels["Code postal"].astype("string").str.startswith("75")]
dvf_2026 = dvf_2026[dvf_2026["Code departement"] == "75"]
dvf_2025 = dvf_2025[dvf_2025["Code departement"] == "75"]

############################ sélection des ventes pour dvf ###############################
#1. on selectionnes les ventes d'un appartement seul 
# Les dependances (caves, parkings...) sont autorisees ici.
dvf_plus = dvf_plus[dvf_plus['anneemut'].between(2023, 2025)]
dvf_plus = dvf_plus[dvf_plus['libnatmut'] == 'Vente']
dvf_plus = dvf_plus[dvf_plus['nblocapt'] == 1]
dvf_plus = dvf_plus[dvf_plus['nblocmai'] == 0]
dvf_plus = dvf_plus[dvf_plus['nblocact'] == 0]
dvf_plus = dvf_plus[dvf_plus['codtypbien'] == 121]  # Un appartement, selon cette livraison

#2. on évite les ventes complexes (plusieurs communes, dispositions ou parcelles)
dvf_plus = dvf_plus[dvf_plus['nbcomm'] == 1]
dvf_plus = dvf_plus[dvf_plus['nbdispo'] == 1]
dvf_plus = dvf_plus[dvf_plus['nbpar'] == 1]


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
    (ev_supp, ["Type d'opération", "Secteur administratif"]),
    (dvf_2026, ["Identifiant de document", "Reference document", "1 Articles CGI", "2 Articles CGI",
                                        "3 Articles CGI", "4 Articles CGI", "5 Articles CGI",
                                        "No disposition", "B/T/Q", "Commune", "Code commune",
                                        "Prefixe de section", "No plan", "No Volume",
                                        "Identifiant local", "Nature culture speciale"]),
                                        
    (dvf_2025, ["Identifiant de document", "Reference document", "1 Articles CGI", "2 Articles CGI",
                                        "3 Articles CGI", "4 Articles CGI", "5 Articles CGI",
                                        "No disposition", "B/T/Q", "Commune", "Code commune",
                                        "Prefixe de section", "No plan", "No Volume",
                                        "Identifiant local", "Nature culture speciale"]) ]

    

for df, cols in col_to_drop:
    df.drop(columns=cols, inplace=True)

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
dvf_ = dvf_plus.sort_values(['date', 'id_vente']).reset_index(drop=True)


############################### harmonisation des types ##################################
##
col_to_integer = [
    (ev_actuels, ["Adresse - Numéro", "Code postal", "Surface calculée", "Superficie totale réelle",
            "Surface horticole", "Année de l'ouverture"]),
    (ev_supp, ["M2 d’espaces verts supplémentaires"]),
    (dvf_2026, ["No voie", "Code postal",
            "Code type local", "Surface reelle bati", "Nombre pieces principales",
            "Surface terrain"]),
    (dvf_2025, ["No voie", "Code postal",
            "Code type local", "Surface reelle bati", "Nombre pieces principales",
            "Surface terrain"])
]

for df, cols in col_to_integer:
    for col in cols:
        df[col] = df[col].astype("Int64")

#print(ev_actuels.info())
#print(ev_supp.info())
#print(dvf_2026.info())
print(dvf_2025.info())
############################## harmonisation des valeurs nulles ou NAN #####################

# on détecte les valeurs qui correspondent à des NaN (certains 0 sont des NaN, d'autres sont des valeurs réelles)
#print(ev_actuels.describe())
#print(ev_supp.describe())
#print(dvf_2026.describe())
print(dvf_2025.describe())
col_zero_to_nan = [(ev_actuels, ["Adresse - Numéro"])]
col_val_to_nan = [(ev_actuels, ["Année de l'ouverture"])]

for df, cols in col_zero_to_nan:
    for col in cols:
        df[col] = df[col].replace(0, np.nan)

for df, cols in col_val_to_nan:
    for col in cols:
        df[col] = df[col].replace(9999, np.nan)

# On supprimes les données manquantes ou atypiques pour dvf_plus 
necessaires = ['prix_euros', 'surface_m2', 'x_lambert93', 'y_lambert93']
dvf_plus = dvf_plus.dropna(subset=necessaires).copy()
dvf_plus = dvf_plus[dvf_plus['prix_euros'] > 0].copy()
dvf_plus = dvf_plus[dvf_plus['surface_m2'].between(9, 300)].copy()

dvf_plus['prix_m2'] = dvf_plus['prix_euros'] / dvf_plus['surface_m2']
dvf_plus = dvf_plus[dvf_plus['prix_m2'].between(1000, 30000)].copy()

############################ création des variables utiles pour la régression ############
dvf_plus['avec_dependance'] = (dvf_plus['nb_dependances'] > 0).astype(int)
dvf_plus['nb_pieces'] = (
    dvf_plus['nbapt1pp'] + 2 * dvf_plus['nbapt2pp'] + 3 * dvf_plus['nbapt3pp']
    + 4 * dvf_plus['nbapt4pp'] + 5 * dvf_plus['nbapt5pp']
)  # 5 signifie 5 pieces ou plus

dvf_plus['log_prix_m2'] = np.log(dvf_plus['prix_m2'])
dvf_plus['log_surface'] = np.log(dvf_plus['surface_m2'])

# 7. Verifications 
assert dvf_plus['id_vente'].is_unique, 'Attention : ventes en double'
assert dvf_plus['prix_m2'].gt(0).all(), 'Attention : prix au m2 invalide'


##########################################################################################
#                                                                                        #
#                         Enregistrement des données nettoyées                           #
#                                                                                        #                      
##########################################################################################

# enregistrement de dvf_plus 
dvf_plus.to_csv('dvf_paris_nettoyee.csv', index=False)
# version sans dépendances 
sans_dependances = dvf_plus[dvf_plus['nb_dependances'] == 0].copy()
sans_dependances.to_csv('dvf_paris_sans_dependances.csv', index=False)

print('Ventes conservees :', len(df))
print('Sans dependances :', len(sans_dependances))
print('Ventes par annee :')
print(df['annee'].value_counts().sort_index())
print('Fichiers CSV crees.')