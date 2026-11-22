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
import os
import matplotlib.pyplot as plt
import contextily as cx
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

##########################################################################################
#                                                                                        #
#                                  import data nettoyée                                  #
#                                                                                        #                      
##########################################################################################

ev_actuels_nettoyes = pd.read_csv("data/2.data_nettoyee/ev_actuels_nettoyes.csv", sep=",", encoding="utf-8")
ev_supp_nettoyes = pd.read_csv("data/2.data_nettoyee/ev_supp_nettoyes.csv", sep=",", encoding="utf-8")
dvf_x_ev = pd.read_csv("data/2.data_nettoyee/dvf_paris_sans_dependances.csv", sep=",", encoding="utf-8")
dvf_x_ev_dep = pd.read_csv("data/2.data_nettoyee/dvf_paris_nettoyee.csv", sep=",", encoding="utf-8")



##########################################################################################
#                                                                                        #
#                                  Analyse descriptive des données                                  #
#                                                                                        #                      
##########################################################################################




##########################################################################################
#                                                                                        #
#                                  Visualisation : Cartes graphiques                                     #
#                                                                                        #                      
##########################################################################################

#----------------------------------------------------------------------------------------
#                           Préparation commune : fond de la carte 
#----------------------------------------------------------------------------------------   

os.makedirs("figures", exist_ok=True)

# Chaque vente devient un point géographique ) à partir de ses coordonnées Lambert93
pts = gpd.GeoDataFrame(
    dvf_x_ev,
    geometry=gpd.points_from_xy(dvf_x_ev["x_lambert93"], dvf_x_ev["y_lambert93"]),
    crs="EPSG:2154",
).to_crs("EPSG:3857") # convertit en Web Mercator, le système des cartes en ligne 
px, py = pts.geometry.x, pts.geometry.y # colonnes x et y converties utilisées pour tracer 

# espaces verts dans le même système
# on écarte les espaces verts sans contour, puis on convertit en polygones
ev = ev_actuels_nettoyes.dropna(subset=["Geo Shape"]).copy()
ev["geometry"] = ev["Geo Shape"].apply(
    lambda s: shape(json.loads(s) if isinstance(s, str) else s)
)
gdf_ev = gpd.GeoDataFrame(ev, geometry="geometry", crs="EPSG:4326")   # contours en latitude/longitude
ev_3857 = gdf_ev.to_crs("EPSG:3857")                                   # conversion en Web Mercator

# cadrage sur Paris (quantiles pour ignorer d'éventuels points isolés)
marge = 500
xlim = (px.quantile(0.002) - marge, px.quantile(0.998) + marge)
ylim = (py.quantile(0.002) - marge, py.quantile(0.998) + marge)

def fond_de_carte(ax):
    ax.set_xlim(xlim); ax.set_ylim(ylim)
    ax.set_aspect("equal"); ax.axis("off")
    cx.add_basemap(ax, source=cx.providers.Esri.WorldStreetMap, zoom=13, zorder = 0 )   # on importe le fond de carte sur Esri sur lequel on superpose les données 



#----------------------------------------------------------------------------------------
#                 Carte 0 : vérification des espaces verts présents dans la base de données 
#---------------------------------------------------------------------------------------- 

fig, ax = plt.subplots(figsize=(11, 9)) # on crée la figure 
ev_3857.plot(ax=ax, color="#2e8b57", alpha=0.6, edgecolor="none", zorder = 2) # on trace les espaces verts en vert semi-transparent
fond_de_carte(ax) #on ajoute le fond de carte 

# legende 
ax.set_title("Espaces verts à Paris selon base de données") 
fig.savefig("figures/carte_ev.png", dpi=200, bbox_inches="tight")
plt.show()




#----------------------------------------------------------------------------------------
#                  Carte 1 : concentration des logements et espaces verts  
#---------------------------------------------------------------------------------------- 

fig, ax = plt.subplots(figsize=(11, 9)) # on crée la figure 
ev_3857.plot(ax=ax, color="#2e8b57", alpha=0.6, edgecolor="none", zorder = 2) # on trace les espaces verts en vert semi-transparent
hb = ax.hexbin(px, py, gridsize=45, mincnt=1, cmap="YlOrRd", alpha=0.55, linewidths=0, zorder = 1) # découpe la carte en cellules hexagonales et les colorie selon le nombre de ventes qu'elles contiennent 
fond_de_carte(ax) #on ajoute le fond de carte 

fig.colorbar(hb, ax=ax, shrink=0.6, label="Nombre de ventes par cellule")
ax.legend(
    handles=[Patch(facecolor="#2e8b57", alpha=0.6, label="Espaces verts")],
    loc="lower left", frameon=True, framealpha=0.9,
)

# legende 
ax.set_title("Ventes d'appartements et espaces verts à Paris") 
fig.savefig("figures/carte_superposee.png", dpi=200, bbox_inches="tight")
plt.show()


#----------------------------------------------------------------------------------------
#                 Carte 2 : prix median au m2 par classes 
#---------------------------------------------------------------------------------------- 

print(dvf_x_ev["prix_m2"].describe(percentiles=[.05, .25, .5, .75, .95]))

bornes = [0, 1375, 7956, 9640, 11481, 15437, 125000] #d'après le describe() ci-dessus
couleurs = plt.get_cmap("YlOrRd")(np.linspace(0.15, 0.95, len(bornes) - 1)) # on prélève 5 couleurs régulièrement espacées dans la palette jaune-rouge 
cmap = ListedColormap(couleurs)
norm = BoundaryNorm(bornes, cmap.N) # associe chaque classe de prix à une couleur

fig, ax = plt.subplots(figsize=(11, 9))
ev_3857.plot(ax=ax, color="#2e8b57", alpha=0.6, edgecolor="none", zorder = 2) # on trace les espaces verts en vert semi-transparent
hb = ax.hexbin(px, py, C=dvf_x_ev["prix_m2"], reduce_C_function=np.median, # reduce_C_function=np.median : on calcule le prix médian au m² par cellule
               gridsize=45, mincnt=10, cmap=cmap, norm=norm, alpha=0.65, linewidths=0, zorder = 1) # mincnt : on ne garde que les cellules avec au moins 10 ventes pour prix fiable 
fond_de_carte(ax)
cb = fig.colorbar(hb, ax=ax, shrink=0.6, ticks=bornes)
cb.set_label("Prix médian au m² (€)")
ax.set_title("Prix médian au m² par zone (cellules d'au moins 10 ventes)")
fig.savefig("figures/carte_prix_m2.png", dpi=200, bbox_inches="tight")
plt.show()

