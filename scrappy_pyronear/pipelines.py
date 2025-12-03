# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
from itemadapter import ItemAdapter
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from tqdm import tqdm

class AlertwestImagePipeline(ImagesPipeline):

    def open_spider(self, spider):
        self.spiderinfo = self.SpiderInfo(spider)
        self.total = getattr(spider, "total_cams", 0)
        self.progress_bar = None

    def close_spider(self, spider):
        self.progress_bar.close()

    def get_media_requests(self, item, info):
        """Send a request to download the image with metadata"""
        url = item["image_url"]
        if url :
            yield scrapy.Request(
                url,
                meta={
                    "id": item["id"],
                    "azimuth": item["azimuth"],
                    "last_moved": item["last_moved"],
                }
            )
        else :
            self.progress_bar.update(1)
            print(f"Image URL is None for camera ID {item['id']}")

    def file_path(self, request, response=None, info=None):
        """Define the file path for the downloaded image"""
        cam_id = str(request.meta["id"])
        azimuth = str(request.meta["azimuth"])
        timestamp = request.meta["last_moved"]

        filename = f"{cam_id}_{timestamp}.jpg"

        return f"{cam_id}/{azimuth}/{filename}"

    def item_completed(self, results, item, info):
        if self.progress_bar is None:
            total = getattr(info.spider, "total_cams", 0)  # récupère total_cams maintenant que le parse a tourné
            self.progress_bar = tqdm(
                total=total,
                desc="Downloading images 🔥",
                bar_format="{l_bar}\033[92m{bar}\033[0m| {n_fmt}/{total_fmt} images",
                unit="image"
            )
        self.progress_bar.update(1)
        success = any(x[0] for x in results)
        if not success and item.get("image_url"):
            logging.warning(f"Image download failed for camera ID {item['id']}")
        return item