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

os.chdir("/home/onyxia/work/Projet-python-2A-") #Pour que ça fonctionne sur vscode depuis sspcloud chez Joceran

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

## paramètres (pour les données foncières) 
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

##########################################################################################
#                                                                                        #
#                                  nettoyage des données                                 #
#                                                                                        #                      
##########################################################################################

############################on ne conserve que Paris centre (75) #########################
ev_actuels = ev_actuels[ev_actuels["Code postal"].astype("string").isin([f"750{i:02d}" for i in range(1, 21)])]
dvf_2026 = dvf_2026[dvf_2026["Code departement"] == "75"]
dvf_2025 = dvf_2025[dvf_2025["Code departement"] == "75"]
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


##########################################################################################
#                                                                                        #
#                         Enregistrement des données nettoyées                           #
#                                                                                        #                      
##########################################################################################

### trouver un moyen pr que l'enregistrement focntionne pour tous les utilsiateurs 