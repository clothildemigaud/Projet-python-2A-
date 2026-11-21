# Économétrie — espaces verts et prix des appartements parisiens

Ce dossier reçoit une table de ventes déjà enrichie par le travail géographique. La liste des jardins et les contours sont gérés en amont. Après une modification de couverture, recalculer le parc le plus proche pour toutes les ventes afin que son identifiant, sa surface et sa distance restent cohérents.

## Format de la base

CSV (virgule, point décimal), éventuellement compressé en .csv.gz. Une ligne par transaction.

| Colonnes | Sens |
|---|---|
| id_vente, id_parcelle | Identifiant unique de la mutation et identifiant de la parcelle |
| date, code_arrondissement | Date de vente au format AAAA-MM-JJ et code géographique |
| prix_euros, surface_m2 | Prix total et surface de l'appartement en m² |
| nb_pieces, nb_dependances | Nombre de pièces (5 pour 5 ou plus) et de dépendances |
| x_lambert93, y_lambert93 | Coordonnées métriques de la parcelle en Lambert-93 |
| id_parc, dist_ev_m, surface_parc_m2 | Identifiant stable, distance point-polygone en mètres et surface en m² du même espace vert |

## Lancer les estimations après correction

À la racine du dépôt, adapter le chemin du CSV à son emplacement réel.

```bash
python -m pip install -r econometrie/requirements.txt
OPENBLAS_NUM_THREADS=1 python econometrie/regressions.py data/base_corrigee.csv
```

Pour conserver deux versions des estimations, préciser un dossier différent avec --sortie, par exemple --sortie econometrie/resultats/version_2.

## Lire le code

1. lire_base.py contrôle les entrées, écarte les ventes à 1 € et recalcule les logarithmes, le trimestre, les distances en centaines de mètres et les indicateurs de prix atypiques.
2. regressions.py estime des MCO du log-prix au m² et regroupe les erreurs standards par parcelle. M1 utilise la distance seule. M2 introduit la surface du parc et son interaction avec la distance. Les modèles intermédiaires ajoutent les caractéristiques du logement puis le trimestre. M3 ajoute les effets fixes d'arrondissement. La variante sans dépendance reprend M3 sur les ventes sans dépendance.
3. Le même script estime des courbes de distance par spline avec effets fixes d'arrondissement ou de carreau de 500 m, puis un modèle linéaire avec effets fixes de parc et interaction. Ces extensions sont reproduites sur l'échantillon principal et sur les ventes entre 1 000 et 30 000 €/m² inclus.

## Sorties

modeles.csv contient les formules, effectifs, R², R² ajustés et tests conjoints pour les modèles avec interaction. coefficients.csv contient les estimations, erreurs standards, intervalles et valeurs p. comparaison_100m_300m.csv et comparaison.png expriment la différence prédite à 100 m relativement à 300 m. Pour les modèles avec interaction, ce contraste correspond à un parc de 1 ha. Les résultats décrivent des associations.
