# importer les donnees et les nettoyer pour pouvoir les merge / analyser
##########################################################################################
#                                                                                        #
#                                  import packages et paramètres                         #
#                                                                                        #                      
##########################################################################################

import numpy as np 
import pandas as pd
import gdown
import os

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

## paramètres (pour les données foncières) 
FILE_ID = "1A9e-cSJgbGsv7mFS24ncDGyU7ckDr7Db"
FICHIER_LOCAL = "DVF-2026-S1.txt"

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
if not os.path.exists(FICHIER_LOCAL):
    gdown.download(id=FILE_ID, output=FICHIER_LOCAL, quiet=False)

dvf_2026 = pd.read_csv(
    FICHIER_LOCAL,
    sep="|",            # les fichiers DVF sont séparés par des barres verticales
    decimal=",",        # montants avec virgule décimale
    low_memory=False,
    encoding="utf-8",   # essaie "latin-1" si les accents sont cassés
)

#visualisation 
print(dvf_2026.shape)
print(dvf_2026.head())

##########################################################################################
#                                                                                        #
#                                  nettoyage des données                                 #
#                                                                                        #                      
##########################################################################################

############################ on enlève les colonnes inutiles #############################
col_to_drop = {
    ev_actuels : ["Identifiant espace vert", "Typologie d'espace vert", 
                                      "Présence cloture", "Année de rénovation","Ancien nom de l'espace vert", 
                                      "Année de changement de nom","Nombre d'entités", 
                                        "Ouverture 24h_24h",
                                        "ID_DIVISION", "ID_ATELIER_HORTICOLE", "IDA3D_ENB", "ID_EQPT",
                                        "Compétence","last_edited_user",
                                        "last_edited_date" ],
    ev_supp : ["Type d'opération ", "Secteur adminsitratif"]}

for df, cols in col_to_drop.items():
    df.drop(columns=cols, inplace=True)


############################ harmonisation des noms de colonnes ##########################

############################### harmonisation des types ##################################

col_to_integer = {
    ev_actuels : ['Adresse - Numéro', "Code postal", "Surface calculée", "Superficie totale réelle",
                    "Surface horticole", "Année de l'ouverture"],
    ev_supp : ["M2 d'espaces verts supplémentaires"]}

for df, cols in col_to_integer.items():
    for col in cols:
        df[col] = df[col].astype('Int64')

print(ev_actuels.info())
print(ev_supp.info())

############################## harmonisation des valeurs nulles ou NAN #####################

# on détecte les valeurs qui correspondent à des NaN (certains 0 sont des NaN, d'autres sont des valeurs réelles)
print(ev_actuels.describe())
print(ev_supp.describe())

col_zero_to_nan = { ev_actuels : ["Surface calculée", "Surface horticole", "Périmètre", "Adresse - Numéro"]
                   }
col_val_to_nan = { ev_actuels : ["Année de l'ouverture"] }

for df, cols in col_zero_to_nan.items():
    for col in cols:
        df[col] = df[col].replace(0, np.nan)

for df, cols in col_val_to_nan.items():
    for col in cols:
        df[col] = df[col].replace(9999, np.nan)

##### fusion de colonnes 
# adresse et surface pour les espaces verts actuels 

############################### tri des données #####################################

#on ne conserve que Paris centre (75)
ev_actuels = ev_actuels[ev_actuels["Code postal"].astype("string").isin([f"750{i:02d}" for i in range(1, 21)])]


##########################################################################################
#                                                                                        #
#                         Enregistrement des données nettoyées                           #
#                                                                                        #                      
##########################################################################################

### trouver un moyen pr que l'enregistrement focntionne pour tous les utilsiateurs 