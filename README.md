# Pyronear
Pipeline de scrapping d'images de caméras de surveillance pour entrainement d'un modèle de détection de départs de feu.

### Commande pour se placer dans le bon dossier 

```
cd Pyronear
```

### Lancer le scrapping des images 

```
scrapy crawl alertwest
```

### Utiliser les paramètres pour ajuster le scrapping

```
scrapy crawl alertwest -s
    DOWNLOAD_TIMEOUT=3 # Temps maximum (en secondes) pour télécharger une image
    CONCURRENT_ITEMS=100 # Nombre d'items traités en parallèle
```

### Lancer le scrapping des images ET enregistrement du json 

```
scrapy crawl alertwest -o alertwest.json
```
## Lancer les tests 

```
pytest -v .\test\test_alertwest_spider.py
```