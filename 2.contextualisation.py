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
parcs_publics_nettoyee = gpd.read_file(
    "data/2.data_nettoyee/parcs_publics_nettoyee.gpkg", layer="parcs_publics_nettoyee")

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
ev_3857 = gdf_ev.to_crs("EPSG:3857")                                   # conversion en Web Mercator

# On garde parcs_publics_nettoyee en Lambert-93 pour calculer les distances en mètres
parcs_2154 = parcs_publics_nettoyee.to_crs("EPSG:2154").copy()
parcs_2154["surface_parc_m2"] = parcs_2154.geometry.area
parcs_3857 = parcs_2154.to_crs("EPSG:3857")                             # conversion en Web Mercator

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
ax.set_title("Espaces verts à Paris selon les données du Ministère") 
fig.savefig("figures/carte_ev.png", dpi=200, bbox_inches="tight")
plt.show()



#----------------------------------------------------------------------------------------
#                  Carte 1 : concentration des logements et espaces verts  (base de données Paris)
#---------------------------------------------------------------------------------------- 

fig, ax = plt.subplots(figsize=(11, 9)) # on crée la figure 
parcs_3857.plot(ax=ax, color="#2e8b57", alpha=0.6, edgecolor="none", zorder = 2) # on trace les espaces verts en vert semi-transparent
hb = ax.hexbin(px, py, gridsize=45, mincnt=1, cmap="YlOrRd", alpha=0.55, linewidths=0, zorder = 1) # découpe la carte en cellules hexagonales et les colorie selon le nombre de ventes qu'elles contiennent 
fond_de_carte(ax) #on ajoute le fond de carte 

fig.colorbar(hb, ax=ax, shrink=0.6, label="Nombre de ventes par cellule")
ax.legend(
    handles=[Patch(facecolor="#2e8b57", alpha=0.6, label="Espaces verts d'après données du Ministère")],
    loc="lower left", frameon=True, framealpha=0.9,
)

# legende 
ax.set_title("Ventes d'appartements et espaces verts à Paris") 
fig.savefig("figures/carte_superposee.png", dpi=200, bbox_inches="tight")
plt.show()


#----------------------------------------------------------------------------------------
#                 Carte 2 : prix median au m2 par classes (base de données paris) 
#---------------------------------------------------------------------------------------- 

print(dvf_x_ev["prix_m2"].describe(percentiles=[.05, .25, .5, .75, .95]))

bornes = [0, 1375, 7956, 9640, 11481, 15437, 125000] #d'après le describe() ci-dessus
couleurs = plt.get_cmap("YlOrRd")(np.linspace(0.15, 0.95, len(bornes) - 1)) # on prélève 5 couleurs régulièrement espacées dans la palette jaune-rouge 
cmap = ListedColormap(couleurs)
norm = BoundaryNorm(bornes, cmap.N) # associe chaque classe de prix à une couleur

fig, ax = plt.subplots(figsize=(11, 9))
parcs_3857.plot(ax=ax, color="#2e8b57", alpha=0.6, edgecolor="none", zorder = 2) # on trace les espaces verts en vert semi-transparent
hb = ax.hexbin(px, py, C=dvf_x_ev["prix_m2"], reduce_C_function=np.median, # reduce_C_function=np.median : on calcule le prix médian au m² par cellule
               gridsize=45, mincnt=10, cmap=cmap, norm=norm, alpha=0.65, linewidths=0, zorder = 1) # mincnt : on ne garde que les cellules avec au moins 10 ventes pour prix fiable 
fond_de_carte(ax)
ax.legend(
    handles=[Patch(facecolor="#2e8b57", alpha=0.6, label="Parcs et Jardins de plus de 500m ouverts au publics (données Ministère)")],
    loc="lower left", frameon=True, framealpha=0.9,
)
cb = fig.colorbar(hb, ax=ax, shrink=0.6, ticks=bornes)
cb.set_label("Prix médian au m² (€)")
ax.set_title("Prix médian au m² par zone (cellules d'au moins 10 ventes)")
fig.savefig("figures/carte_prix_m2.png", dpi=200, bbox_inches="tight")
plt.show()

# ----------------------------------------------------------------------------------------
#                 Carte 3 : Typologie des espaces verts (Parc, Jardin, Square)
# ----------------------------------------------------------------------------------------

COL_TYPE_ESPACE = "nature"

# On prépare les parcs en Web Mercator (EPSG:3857) avec des majuscules propres
parcs_3857 = parcs_publics_nettoyee.to_crs("EPSG:3857").copy()
#parcs_3857[COL_TYPE_PARC] = parcs_3857[COL_TYPE_PARC].str.strip().str.capitalize()

couleurs_types = {
    "Parc": "#005a32",    # vert très foncé
    "Jardin": "#238b45",  # vert moyen
    "Square": "#74c476",  # vert clair
}

fig, ax = plt.subplots(figsize=(11, 9))

# Tracé catégorie par catégorie pour maîtriser les couleurs et l'ordre d'affichage
for type_ev in ["Square", "Jardin", "Parc"]:  # On trace les grands parcs en dernier pour qu'ils ressortent bien
    sous_gdf = parcs_3857[parcs_3857[COL_TYPE_ESPACE] == type_ev]
    if not sous_gdf.empty:
        sous_gdf.plot(
            ax=ax,
            color=couleurs_types[type_ev],
            edgecolor="#00441b",
            linewidth=0.4,
            alpha=0.85,
            zorder=2,
        )

fond_de_carte(ax)

# Légende personnalisée propre
legend_handles = [
    Patch(facecolor=couleurs_types["Parc"], edgecolor="#00441b", label="Parc"),
    Patch(facecolor=couleurs_types["Jardin"], edgecolor="#00441b", label="Jardin"),
    Patch(facecolor=couleurs_types["Square"], edgecolor="#00441b", label="Square"),
]
ax.legend(handles=legend_handles, title="Nature de l'espace vert", loc="lower left", frameon=True, framealpha=0.92)
ax.set_title("Répartition des espaces verts publics par typologie à Paris (données Ministère)")

fig.savefig("figures/carte_typologie_parcs.png", dpi=200, bbox_inches="tight")
plt.show()

# %%
# ----------------------------------------------------------------------------------------
#                 Carte 4 : Rayon d'accessibilité de 250 m autour des espaces verts
# ----------------------------------------------------------------------------------------

# 1. Calcul du buffer de 250 m en mètres (Lambert-93 : EPSG:2154)
buffers_250m = parcs_2154.buffer(250).union_all()  # fusionne les cercles qui se chevauchent
gdf_buffers_3857 = gpd.GeoDataFrame(geometry=[buffers_250m], crs="EPSG:2154").to_crs("EPSG:3857")

# 2. Tracé
fig, ax = plt.subplots(figsize=(11, 9))

# Zone tampon de 250 m en vert très pâle
gdf_buffers_3857.plot(ax=ax, color="#a1d99b", alpha=0.35, edgecolor="#41ab5d", linewidth=0.8, zorder=1)
# Espaces verts réels par-dessus en vert foncé
parcs_3857.plot(ax=ax, color="#006d2c", alpha=0.9, edgecolor="none", zorder=2)

fond_de_carte(ax)

legend_handles = [
    Patch(facecolor="#006d2c", alpha=0.9, label="Espace vert public"),
    Patch(facecolor="#a1d99b", alpha=0.45, edgecolor="#41ab5d", label="Zone à moins de 250 m"),
]
ax.legend(handles=legend_handles, loc="lower left", frameon=True, framealpha=0.92)
ax.set_title("Accessibilité aux espaces verts : zones situées à moins de 250 mètres")

fig.savefig("figures/carte_buffers_250m.png", dpi=200, bbox_inches="tight")
plt.show()

# %%
# ----------------------------------------------------------------------------------------
#                 Carte 5 : Ventes colorées selon leur distance au parc le plus proche
# ----------------------------------------------------------------------------------------
# Distance au parc public le plus proche (en mètres, grâce au CRS EPSG:2154)
gdf_desc = gpd.sjoin_nearest(
    pts_2154,
    parcs_2154[["geometry", "surface_parc_m2"]],
    how="left",
    distance_col="dist_parc_m",
)
# On utilise gdf_desc (qui contient dist_parc_m calculé en Lambert-93) et on le passe en 3857
pts_dist_3857 = gdf_desc.to_crs("EPSG:3857")

fig, ax = plt.subplots(figsize=(11, 9))

# Espaces verts en vert vif
parcs_3857.plot(ax=ax, color="#1b7837", alpha=0.85, edgecolor="none", zorder=3)

# Hexbin de la distance médiane au parc le plus proche par cellule
hb = ax.hexbin(
    pts_dist_3857.geometry.x,
    pts_dist_3857.geometry.y,
    C=pts_dist_3857["dist_parc_m"],
    reduce_C_function=np.median,
    gridsize=45,
    mincnt=5,
    cmap="YlGnBu_r",  # Vert/bleu foncé = très proche d'un parc, jaune = éloigné
    vmin=0,
    vmax=500,
    alpha=0.65,
    linewidths=0,
    zorder=2,
)

fond_de_carte(ax)

cb = fig.colorbar(hb, ax=ax, shrink=0.6, extend="max")
cb.set_label("Distance médiane au parc le plus proche (mètres)")
ax.legend(
    handles=[Patch(facecolor="#1b7837", alpha=0.85, label="Espaces verts publics")],
    loc="lower left",
    frameon=True,
    framealpha=0.92,
)
ax.set_title("Accessibilité des logements vendus aux espaces verts publics")

fig.savefig("figures/carte_distance_ventes_ev.png", dpi=200, bbox_inches="tight")
plt.show()

# ----------------------------------------------------------------------------------------
#                 Carte 6 : Superposition de la typologie des parcs et des ventes (DVF)
# ----------------------------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(11, 9))

# 1. Couche du dessous : densité des ventes immobilières (palette chaude)
hb = ax.hexbin(
    px,
    py,
    gridsize=45,
    mincnt=1,
    cmap="YlOrRd",
    alpha=0.50,
    linewidths=0,
    zorder=1,
)

# 2. Couche du dessus : espaces verts par nature (palette verte contrastée)
couleurs_types = {
    "Parc": "#00441b",    # vert très sombre (fort contraste)
    "Jardin": "#1b7837",  # vert soutenu
    "Square": "#41ab5d",  # vert franc (lisible même sur fond orangé)
}

for type_ev in ["Square", "Jardin", "Parc"]:
    sous_gdf = parcs_3857[parcs_3857[COL_TYPE_ESPACE] == type_ev]
    if not sous_gdf.empty:
        sous_gdf.plot(
            ax=ax,
            color=couleurs_types[type_ev],
            edgecolor="white",  # fin liseré blanc pour détacher le parc des ventes autour
            linewidth=0.35,
            alpha=0.90,
            zorder=2,
        )

fond_de_carte(ax)

# Barre de couleur pour les ventes + légende pour les 3 types d'espaces verts
cb = fig.colorbar(hb, ax=ax, shrink=0.6, label="Nombre de ventes par cellule")

legend_handles = [
    Patch(facecolor=couleurs_types["Parc"], edgecolor="white", label="Parc"),
    Patch(facecolor=couleurs_types["Jardin"], edgecolor="white", label="Jardin"),
    Patch(facecolor=couleurs_types["Square"], edgecolor="white", label="Square"),
]
ax.legend(
    handles=legend_handles,
    title="Nature de l'espace vert",
    loc="lower left",
    frameon=True,
    framealpha=0.92,
)
ax.set_title("Densité des ventes immobilières et typologie des espaces verts à Paris")

fig.savefig("figures/carte_ventes_typologie_parcs.png", dpi=200, bbox_inches="tight")
plt.show()

##########################################################################################
#                                                                                        #
#                                  Analyse descriptive des données                       #
#                                                                                        #                      
##########################################################################################

# %%
sns.set_theme(style="whitegrid", context="notebook")
os.makedirs("figures", exist_ok=True)

# Évite les doublons si une vente est à égale distance de 2 parcs
gdf_desc = gdf_desc[~gdf_desc.index.duplicated(keep="first")]

# Découpage en tranches de distance et taille de parc
gdf_desc = gpd.sjoin_nearest(
    pts_2154,
    parcs_2154[["geometry", "surface_parc_m2", COL_TYPE_ESPACE]],
    how="left",
    distance_col="dist_parc_m",
)

gdf_desc["tranche_dist"] = pd.cut(
    gdf_desc["dist_parc_m"],
    bins=[-1, 100, 250, 500, 1000],
    labels=["0–100 m", "100–250 m", "250–500 m", "500–1000 m"],     #Il n'y a pas de ventes à plus de 1000m
)                                                                   

#----------------------------------------------------------------------------------------
#                           Tables de statistique descriptive 
#----------------------------------------------------------------------------------------   

print("=== 1. PARCS PUBLICS (parcs_publics_nettoyee) ===")
print(f"Nombre de parcs : {len(parcs_2154)}")
print(parcs_2154["surface_parc_m2"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(2))

print("\n=== 2. VENTES IMMOBILIÈRES (dvf_x_ev) ===")
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

print("\n=== 1B. RÉPARTITION PAR TYPE D'ESPACE VERT ===")
print(
    parcs_2154.groupby(COL_TYPE_ESPACE)["surface_parc_m2"]
    .agg(nombre="count", surface_mediane_m2="median", surface_totale_m2="sum")
    .round(2)
)

print("\n=== 3B. PRIX MÉDIAN AU M² SELON LA DISTANCE ET LE TYPE DE PARC ===")
pivot_prix = gdf_desc.pivot_table(
    index="tranche_dist",
    columns=COL_TYPE_ESPACE,
    values="prix_m2",
    aggfunc="median",
    observed=False,
).round(0)
print(pivot_prix)

# --- Graphique A : Distributions univariées (taille des parcs & distance aux parcs) ---
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

sns.histplot(parcs_2154["surface_parc_m2"], bins=30, log_scale=True, color="#2e8b57", ax=axes[0])
axes[0].axvline(parcs_2154["surface_parc_m2"].median(), color="black", linestyle="--", label=f"Médiane : {parcs_2154['surface_parc_m2'].median():.2f} m2")
axes[0].set_title("Surface des parcs publics (échelle log)")
axes[0].set_xlabel("Surface (m2)")
axes[0].set_ylabel("Nombre de parcs")
axes[0].legend()

sns.histplot(gdf_desc["dist_parc_m"].clip(upper=1500), bins=40, color="#3b7ea1", ax=axes[1])
axes[1].axvline(gdf_desc["dist_parc_m"].median(), color="black", linestyle="--", label=f"Médiane : {gdf_desc['dist_parc_m'].median():.0f} m")
axes[1].set_title("Distance des ventes au parc le plus proche")
axes[1].set_xlabel("Distance (m, plafonnée à 1500 m)")
axes[1].set_ylabel("Nombre de ventes")
axes[1].legend()

plt.tight_layout()
fig.savefig("figures/desc_univariee.png", dpi=200)
plt.show()

# --- Graphique B : Boxplot prix/m² par tranche de distance ---
#p01, p99 = gdf_desc["prix_m2"].quantile([0.01, 0.99])        # Arajouter si on veut enlever les 1% extrèmes
df_clean_visu = gdf_desc#[(gdf_desc["prix_m2"] >= p01) & (gdf_desc["prix_m2"] <= p99)]

fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df_clean_visu, x="tranche_dist", y="prix_m2", palette="Greens_r", showfliers=False, ax=ax)
ax.set_title("Prix au m² selon la distance au parc public le plus proche")
ax.set_xlabel("Distance au parc le plus proche")
ax.set_ylabel("Prix au m² (€)")
plt.tight_layout()
fig.savefig("figures/desc_boxplot_prix_distance.png", dpi=200)
plt.show()

# --- Graphique C : Courbe de gradient (0 à 800 m) selon le type (Parc / Jardin / Square) ---
df_grad = df_clean_visu[df_clean_visu["dist_parc_m"] <= 800].copy()
df_grad["pas_50m"] = (df_grad["dist_parc_m"] // 50) * 50 + 25

grad_table = (
    df_grad.groupby(["pas_50m", COL_TYPE_ESPACE])["prix_m2"]
    .agg(prix_median="median", n="count")
    .reset_index()
)
grad_table = grad_table[grad_table["n"] >= 30]

# Palette ordonnée du plus grand au plus petit type d'espace vert
palette_types = {
    "Parc": "#005a32",    # vert très foncé
    "Jardin": "#41ab5d",  # vert moyen
    "Square": "#a1d99b",  # vert clair
}

fig, ax = plt.subplots(figsize=(10, 6))
sns.lineplot(
    data=grad_table,
    x="pas_50m",
    y="prix_median",
    hue=COL_TYPE_ESPACE,
    hue_order=["Parc", "Jardin", "Square"],
    marker="o",
    linewidth=2.2,
    palette=palette_types,
    ax=ax,
)
ax.set_title("Prix médian au m² en s'éloignant d'un espace vert (par type)")
ax.set_xlabel("Distance à l'espace vert le plus proche (mètres)")
ax.set_ylabel("Prix médian au m² (€)")
ax.legend(title="Nature de l'espace vert")

plt.tight_layout()
fig.savefig("figures/desc_gradient_prix_type_parc.png", dpi=200)
plt.show()