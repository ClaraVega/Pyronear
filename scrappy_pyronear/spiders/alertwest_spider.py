from pathlib import Path
import scrapy
import json
import os
from datetime import datetime

# Execute the code 
# NORMAL : scrapy crawl alertwest
# WITH DEBUG : scrapy crawl alertwest -s LOG_LEVEL=DEBUG

# Propriétés utiles des caméras
INTERESTING_PROPERTIES = ["Azimuth", "LastMoved", "camId", "Screenshot", "Offline","camName"]
ROOT_FOLDER_IMAGE = Path(__file__).parent.parent.parent / "images"
API_URL = "https://api.cdn.prod.alertwest.com/api/getCameraDataByLoc"

class AlertwestSpider(scrapy.Spider):
    name = "alertwest"
    start_urls = [
        API_URL
    ]

    def parse(self, response):
        # On récupère la data du json
        data = json.loads(response.text)

        # Récupérer la table des clés courtes -> noms complets (ex: "p": "camAzimuth")
        key_list = data.get("data", {}).get("cams", {}).get("key", {})
            
        # Construire un dictionnaire mapping propriété -> clé courte (ex: "Azimuth" -> "p")
        short_key = {}
        for prop in INTERESTING_PROPERTIES:
            prop_lower = prop.lower()
            for short, longname in key_list.items():
                if isinstance(longname, str) and prop_lower in longname.lower():
                    short_key[prop] = short
                    break        

        # Parcourir les caméras
        data_cams = data.get("data", {}).get("cams", {}).get("data", [])
        for cam in data_cams:
            # Récupérer les valeurs via les clés courtes détectées
            timestamp = int(cam.get(short_key.get("LastMoved"), '0'))
            cam_id = cam.get(short_key.get("camId"))
            img_name = cam.get(short_key.get("Screenshot"))
            azimuth = cam.get(short_key.get("Azimuth"))
            cam_name = cam.get(short_key.get("camName"))

            # Construire l'URL de l'image
            date_path = datetime.fromtimestamp(timestamp)
            if date_path.year >= datetime.now().year - 1:
                date_path = date_path.strftime("%Y/%m/%d")
            else:
                date_path = datetime.now().strftime("%Y/%m/%d")
                
            img_url = f"https://img.cdn.prod.alertwest.com/data/thumb/{cam_id}/{date_path}/{img_name}"

            # On renvoie un dictionnaire = une ligne du futur fichier .json ou .csv
            yield {
                "id": cam_id,
                "name": cam_name,
                "azimuth": azimuth,
                "last_moved": timestamp,
                "image_url": img_url,
            }

            # Et on peut aussi télécharger l'image (en créant une requête secondaire)
            yield scrapy.Request(
                img_url,
                callback=self.save_image,
                meta={"id": cam_id, "last_moved": timestamp, "azimuth": azimuth}
            )

    def save_image(self, response):
        # If image not found, don't create any folders/files
        if getattr(response, "status", None) == 404:
            self.logger.warning(f"Image non trouvée : {response.url}")
            return

        # Créer le dossier racine uniquement si nécessaire puis les sous-dossiers
        cam_id = str(response.meta.get("id"))
        azimuth = str(response.meta.get("azimuth", "0"))

        dir_cam_azim = ROOT_FOLDER_IMAGE / cam_id / azimuth
        dir_cam_azim.mkdir(parents=True, exist_ok=True)
        
        timestamp = response.meta.get("last_moved")  # timestamp UNIX
        filename = f"{cam_id}_{timestamp}.jpg"
        path = dir_cam_azim / filename

        self.logger.info(f"Téléchargement de {path}")
        with path.open("wb") as f:
            f.write(response.body)