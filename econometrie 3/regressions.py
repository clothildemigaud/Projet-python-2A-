"""Prix hédoniques. Chaque appel à estimer utilise un échantillon explicite."""
import argparse
from pathlib import Path

from lire_base import lire_ventes

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import build_design_matrices, dmatrices

DOSSIER = Path(__file__).resolve().parent
arguments = argparse.ArgumentParser(description="Estimer les modèles sur la base indiquée.")
arguments.add_argument("base", type=Path, help="CSV des ventes enrichies, éventuellement .csv.gz")
arguments.add_argument("--sortie", type=Path, default=DOSSIER / "resultats")
options = arguments.parse_args()
RESULTATS = options.sortie
ventes = lire_ventes(options.base)
# Un carreau est identifié par ses deux coordonnées sur la grille Lambert-93.
colonne = (ventes["x_lambert93"] // 500).astype(int)
rangee = (ventes["y_lambert93"] // 500).astype(int)
ventes["carreau"] = colonne.astype(str) + "_" + rangee.astype(str)
filtrees = ventes.loc[~ventes["prix_bas"] & ~ventes["prix_eleve"]]
sans_dependance = ventes.loc[ventes["nb_dependances"] == 0]

distance = "distance_100m"
surface = "log_surface_parc_ha"
interaction = distance + ":" + surface
parc = distance + " * " + surface
logement = "log_surface + C(nb_pieces)"
controles = logement + " + avec_dependance + C(trimestre)"
modeles, coefficients, contrastes = [], [], []


def estimer(nom, donnees, formule):
    y, x = dmatrices("log_prix_m2 ~ " + formule, donnees,
                     return_type="dataframe", NA_action="raise")
    modele = sm.OLS(y, x).fit(cov_type="cluster",
                              cov_kwds={"groups": donnees["id_parcelle"]})
    bilan = dict(modele=nom, formule=formule, ventes=len(y),
                 parcelles=donnees["id_parcelle"].nunique(),
                 r2=modele.rsquared, r2_ajuste=modele.rsquared_adj)
    if interaction in x.columns:
        bilan["p_test_joint_distance"] = float(
            modele.f_test(f"{distance} = 0, {interaction} = 0").pvalue
        )
    modeles.append(bilan)
    tableau = modele.conf_int()
    tableau.columns = ["borne_basse", "borne_haute"]
    tableau["coefficient"] = modele.params
    tableau["erreur_standard"] = modele.bse
    tableau["p"] = modele.pvalues
    tableau["modele"] = nom
    coefficients.append(tableau.rename_axis("variable").reset_index())

    # Deux logements identiques. Seule leur distance change (100 ou 300 m).
    exemple = donnees.iloc[[0, 0]].copy()
    exemple[distance] = [1., 3.]
    exemple[surface] = 0.  # Parc de référence de 1 hectare si interaction.
    profils = np.asarray(build_design_matrices([x.design_info], exemple)[0])
    test = modele.t_test(profils[0] - profils[1])
    bas, haut = test.conf_int()[0]
    # Conversion d'une différence de logarithmes en pourcentage.
    ecart, bas, haut = 100 * np.expm1([test.effect.item(), bas, haut])
    contrastes.append(dict(modele=nom, ecart_pct=ecart, bas95=bas, haut95=haut))


estimer("M1", ventes, distance)
estimer("M2", ventes, parc)
estimer("M2_logement", ventes, parc + " + " + logement + " + avec_dependance")
estimer("M2_trimestre", ventes, parc + " + " + controles)
complet = parc + " + " + controles + " + C(code_arrondissement)"
estimer("M3", ventes, complet)
estimer("M3_sans_dependance", sans_dependance, parc + " + " + logement
        + " + C(trimestre) + C(code_arrondissement)")

# La spline laisse la pente varier avec la distance. Sa forme est commune aux parcs.
courbe = "bs(distance_100m, df=4) + log_surface_parc_ha + " + controles
for nom, donnees in [("principal", ventes), ("filtre", filtrees)]:
    estimer("arr_" + nom, donnees, courbe + " + C(code_arrondissement)")
    estimer("carreau_" + nom, donnees, courbe + " + C(carreau)")
    # L'effet fixe du parc absorbe aussi sa surface. L'interaction reste estimable.
    estimer("parc_" + nom, donnees, distance + " + " + interaction
            + " + " + controles + " + C(id_parc)")

RESULTATS.mkdir(parents=True, exist_ok=True)
pd.DataFrame(modeles).to_csv(RESULTATS / "modeles.csv", index=False)
pd.concat(coefficients).to_csv(RESULTATS / "coefficients.csv", index=False)
comparaisons = pd.DataFrame(contrastes).set_index("modele")
comparaisons.to_csv(RESULTATS / "comparaison_100m_300m.csv")
print(comparaisons.round(2))

fig, ax = plt.subplots(figsize=(8, 4))
selection = comparaisons.loc[["arr_principal", "carreau_principal", "arr_filtre", "carreau_filtre"]]
for i, ligne in enumerate(selection.itertuples()):
    ax.plot([ligne.bas95, ligne.haut95], [i, i], color="#286274")
    ax.scatter(ligne.ecart_pct, i, color="#174655")
ax.axvline(0, color="gray", linestyle="--")
ax.set_yticks(range(4), ["Arrondissement", "Carreau de 500 m",
                        "Arrondissement · prix filtrés", "Carreau de 500 m · prix filtrés"])
ax.invert_yaxis()
ax.set_xlabel("Écart estimé à 100 m par rapport à 300 m (%)")
ax.set_title("Proximité du parc et prix au m² · intervalles à 95 %")
fig.tight_layout()
fig.savefig(RESULTATS / "comparaison.png", dpi=160)
