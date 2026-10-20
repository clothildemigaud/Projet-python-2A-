# importer les donnees et les nettoyer pour pouvoir les merge / analyser
########################### import packages ################################################

import numpy as np 
import pandas as pd

########################## import data #####################################################

#val foncières format zip : voir comment telecharger 

espaces_verts_actuels = pd.read_csv("data/espaces_verts.csv", sep=";", encoding="utf-8")
print(espaces_verts_actuels.head(10))

espaces_verts_supp = pd.read_csv("data/espaces_verts_supplementaires.csv", sep=";", encoding="utf-8")
print(espaces_verts_supp.head(10))

