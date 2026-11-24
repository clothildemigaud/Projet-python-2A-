# Projet Python pour la Data Science

_Auteurs : Joceran jaillet, Thibault Lefort, Clothilde Migaud_

## Sujet : Influence de la proximité aux espaces verts sur le prix de l'immobilier à Paris 

L'épisode caniculaire de l'été 2026 a montré à quel point les espaces verts publics étaient devenus indispensables pour faire face aux vagues de chaleur de plus en plus fréquentes. Ce fut notamment le cas à Paris, où les parcs publics sont devenus très prisés par les parisiens pour se rafraichir; certains parcs étant même restés ouverts la nuit pour permettre aux habitants de dormir au frais. Dans un contexte où les espaces verts semblent devenir un facteur valorisé par les ménages, nous nous interrogeons sur leur impact potentiel sur le prix des logements. 

**Problématique** : Le fait d'habiter à proximité d'un espace vert augmente-t-il la valeur du logement? 

Nous concentrons ici notre enquête sur Paris intramuros. 

## Données 
Nous exploitons les données suivantes : 
- prix au mètre carré des logements à Paris vendus entre 2014 et 2026
- localisation et surface des espaces verts parisiens tels que recensés par la Ville de Paris 
- localisation et surface des espaces verts parisiens recensés par le ministère de la transition écologique

Ces données ont obtenues au sources suivantes, respectivement: 
- mutations immobilières du département de Paris, construit par Cerema à partir des Demandes de valeurs foncières de la DGFiP 
- inventaire des espaces verts et assimilés de la Ville de Paris 
- parcs et jardins ouverts au public à Paris, Ministère de la transition écologique 

La base de données du ministère est plus complète et présente de meilleurs résultats. 


## Reproduction du projet
**Installation**. Cloner le projet.
Installer les dépendances Python à l’aide de la commande :
```python
pip install -r requirements.txt
```

**Lancement**. Ouvrir le notebook `main.ipynb`, qui constitue le rapport analytique principal du projet.

Certaines données étant stockées dans un dossier hebergé sur google drive, nous avons partagé ledit dossier à notre chargé de TD, afin que l'import fonctionne. Si besoin, le dossier est accessible au lien suivant : https://drive.google.com/drive/folders/1pCbUYh9dp9OUCQJH-HGou9i4GJB4-9UD?usp=share_link

## Structure du repo 
- dossier `data` : contient les données brutes et reçoit les données nettoyées 
- dossier `figures` : contient l'ensemble des cartes et graphiques produits pour la visualisation des données 
- fichier `import_data.py` : code d'import et de nettoyage des données 
- fichier `contextualisation.py` : code qui permet de visualiser les données à l'aide de graphiques et de cartes 
- fichier `regression_lineaire.py` : code qui a servi à produire la regression linéaire. Les résultats sont sotckés dans le fichier `resultats_regressions.csv`
- fichier `rapport_final_main_ipynb` : notebook principal servant de support de restitution 


