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

### Lancer le scrapping des images ET enregistrement du json 

```
scrapy crawl alertwest -o alertwest.json
```
## Lancer les tests 

```
pytest -v .\test\test_alertwest_spider.py
```