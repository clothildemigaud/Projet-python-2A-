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
import seaborn as sns

#pour voir toutes les colonnes dans les sorties python
pd.set_option("display.max_columns", None)  

os.chdir("/home/onyxia/work/Projet-python-2A-") #Pour que ça fonctionne sur vscode depuis sspcloud chez Joceran
print(os.listdir("data/2.data_nettoyee"))

##########################################################################################
#                                                                                        #
#                                  import data nettoyée                                  #
#                                                                                        #                      
##########################################################################################

ev_actuels_nettoyes = pd.read_csv("data/2.data_nettoyee/ev_actuels_nettoyes.csv", sep=",", encoding="utf-8")
dvf_x_ev = pd.read_csv("data/2.data_nettoyee/dvf_paris_sans_dependances.csv", sep=",", encoding="utf-8")
dvf_x_ev_dep = pd.read_csv("data/2.data_nettoyee/dvf_paris_nettoyee.csv", sep=",", encoding="utf-8")
parcs_publics_nettoyee = gpd.read_file("/home/onyxia/work/Projet-python-2A-/data/2.data_nettoyee/parcs_publics_nettoyee.gpkg", layer="parcs_publics_nettoyee")

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
pts_2154 = gpd.GeoDataFrame(
    dvf_x_ev,
    geometry=gpd.points_from_xy(dvf_x_ev["x_lambert93"], dvf_x_ev["y_lambert93"]),
    crs="EPSG:2154",
)
# On convertit en Web Mercator pour l'affichage sur tes cartes
pts = pts_2154.to_crs("EPSG:3857")
px, py = pts.geometry.x, pts.geometry.y

# espaces verts dans le même système
# on écarte les espaces verts sans contour, puis on convertit en polygones
ev = ev_actuels_nettoyes.dropna(subset=["Geo Shape"]).copy()
ev["geometry"] = ev["Geo Shape"].apply(
    lambda s: shape(json.loads(s) if isinstance(s, str) else s)
)
gdf_ev = gpd.GeoDataFrame(ev, geometry="geometry", crs="EPSG:4326")   # contours en latitude/longitude
#ev_3857 = gdf_ev.to_crs("EPSG:3857")                                   # conversion en Web Mercator

# On garde parcs_publics_nettoyee en Lambert-93 pour calculer les distances en mètres
parcs_2154 = parcs_publics_nettoyee.to_crs("EPSG:2154").copy()
parcs_2154["surface_parc_m2"] = parcs_2154.geometry.area
ev_3857 = parcs_2154.to_crs("EPSG:3857")                             # conversion en Web Mercator

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




##########################################################################################
#                                                                                        #
#                                  Analyse descriptive des données                                  #
#                                                                                        #                      
##########################################################################################

# %%
sns.set_theme(style="whitegrid", context="notebook")
os.makedirs("figures", exist_ok=True)

# Distance au parc public le plus proche (en mètres, grâce au CRS EPSG:2154)
gdf_desc = gpd.sjoin_nearest(
    pts_2154,
    parcs_2154[["geometry", "surface_parc_m2"]],
    how="left",
    distance_col="dist_parc_m",
)
# Évite les doublons si une vente est à égale distance de 2 parcs
gdf_desc = gdf_desc[~gdf_desc.index.duplicated(keep="first")]

# Découpage en tranches de distance et taille de parc
gdf_desc["tranche_dist"] = pd.cut(
    gdf_desc["dist_parc_m"],
    bins=[-1, 100, 250, 500, 1000, np.inf],
    labels=["0–100 m", "100–250 m", "250–500 m", "500–1000 m", "> 1000 m"],
)
gdf_desc["taille_parc"] = np.where(
    gdf_desc["surface_parc_m2"] >= 2.0,
    "Grand parc (≥ 2 ha)",
    "Petit square (< 2 ha)",
)

# %%
print("=== 1. PARCS PUBLICS (parcs_publics_nettoyee) ===")
print(f"Nombre de parcs : {len(parcs_2154)}")
print(parcs_2154["surface_parc_m2"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(2))

print("\n=== 2. VENTES IMMOBILIÈRES (dvf_x_ev) ===")
# ⚠️ Vérifie les noms exacts de tes colonnes de surface/pièces dans dvf_x_ev
cols_a_decrire = [c for c in ["prix_m2", "surface_reelle_bati", "nombre_pieces_principales", "dist_parc_m"] if c in gdf_desc.columns]
print(gdf_desc[cols_a_decrire].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(1))

print("\n=== 3. PRIX AU M² SELON LA DISTANCE AU PARC ===")
stats_dist = (
    gdf_desc.groupby("tranche_dist", observed=False)["prix_m2"]
    .agg(nb_ventes="count", prix_median="median", prix_moyen="mean", ecart_type="std")
    .round(0)
)
stats_dist["part_%"] = (stats_dist["nb_ventes"] / len(gdf_desc) * 100).round(1)
print(stats_dist)
