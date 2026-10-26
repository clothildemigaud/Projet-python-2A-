# importer les donnees et les nettoyer pour pouvoir les merge / analyser
########################### import packages ################################################

import numpy as np 
import pandas as pd
import gdown
import os

pd.set_option("display.max_columns", None) #pour voir toutes les colonnes dans les sorties python 

########################## paramètres (pour les données foncières) #####################################################
FILE_ID = "1A9e-cSJgbGsv7mFS24ncDGyU7ckDr7Db"
FICHIER_LOCAL = "DVF-2026-S1.txt"

########################## import data #####################################################

##### espaces verts actuels et supplémentaires
ev_actuels = pd.read_csv("data/espaces_verts.csv", sep=";", encoding="utf-8")
print(ev_actuels.head(10))

ev_supp = pd.read_csv("data/espaces_verts_supplementaires.csv", sep=";", encoding="utf-8")
print(ev_supp.head(10))

###### pour les données foncières, fichiers volumineux donc télécharge automatiquement en local à partir du drive partagé

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

print(dvf_2026.shape)
print(dvf_2026.head())

############################# nettoyage des données #####################################################

##### on enlève les colonnes inutiles 
ev_actuels = ev_actuels.drop(columns=["Identifiant espace vert", "Typologie d'espace vert", "Présence cloture", "Année de rénovation",
                         "Ancien nom de l'espace vert", "Année de changement de nom","Nombre d'entités", "Ouverture 24h_24h",
                          "ID_DIVISION", "ID_ATELIER_HORTICOLE", "IDA3D_ENB", "ID_EQPT", "Compétence","last_edited_user",
                          "last_edited_date" ])


##### harmonisation des noms de colonnes

##### harmonisation des types 

col_to_integer = ['Adresse - Numéro', "Code postal", "Surface calculée", "Superficie totale réelle",
                    "Surface horticole", "Année de l'ouverture"]
for col in col_to_integer:
    ev_actuels[col] =  ev_actuels[col].astype('Int64') 


print(ev_actuels.info())
print(ev_supp.info())
##### harmonisation des valeurs nulles ou NAN 

##### fusion de colonnes 
# adresse et surface pour les espaces verts actuels 

