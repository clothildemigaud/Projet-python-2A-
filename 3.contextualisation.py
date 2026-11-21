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

##########################################################################################
#                                                                                        #
#                                  import data nettoyée                                  #
#                                                                                        #                      
##########################################################################################

ev_actuels_nettoyes = pd.read_csv("data/2.data_nettoyee/ev_actuels_nettoyes.csv", sep=",", encoding="utf-8")
ev_supp_nettoyes = pd.read_csv("data/2.data_nettoyee/ev_supp_nettoyes.csv", sep=",", encoding="utf-8")
dvf_x_ev = pd.read_csv("data/2.data_nettoyee/dvf_paris_sans_dependances.csv", sep=",", encoding="utf-8")
