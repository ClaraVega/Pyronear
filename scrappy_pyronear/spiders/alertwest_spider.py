from pathlib import Path
import scrapy
import json
import os
from datetime import datetime


class AlertwestSpider(scrapy.Spider):
    name = "alertwest"
    start_urls = [
        "https://api.cdn.prod.alertwest.com/api/getCameraDataByLoc"
    ]

    def parse(self, response):
        # On récupère la data du json
        data = json.loads(response.text)

        for cam in data["data"]["cams"]["data"]:
            timestamp = int(cam["lmt"])
            date_path = datetime.fromtimestamp(timestamp).strftime("%Y/%m/%d")
            cam_id = cam["id"]   # ou le champ correspondant au dossier 2185
            timestamp = cam["lmt"]
            img_name = cam["img"]
            img_url = f"https://img.cdn.prod.alertwest.com/data/thumb/{cam_id}/{date_path}/{img_name}"

            # On renvoie un dictionnaire = une ligne du futur fichier .json ou .csv
            yield {
                "id": cam["id"],
                "name": cam["cn"],
                "county": cam["co"],
                "sponsor": cam["sp"],
                "image_url": img_url
            }

            # Et on peut aussi télécharger l'image (en créant une requête secondaire)
            yield scrapy.Request(
                img_url,
                callback=self.save_image,
                meta={"id": cam["id"], "lmt": cam["lmt"]}
            )

    def save_image(self, response):
        folder = "images"
        os.makedirs(folder, exist_ok=True)  # crée le dossier si nécessaire

        if response.status == 404:
            self.logger.warning(f"Image non trouvée : {response.url}")
            return

        cam_id = response.meta["id"]      # l'id de la caméra
        timestamp = response.meta["lmt"]  # timestamp UNIX

        filename = f"{cam_id}_{timestamp}.jpg"
        path = os.path.join(folder, filename)

        self.logger.info(f"Téléchargement de {path}")
        with open(path, "wb") as f:
            f.write(response.body)