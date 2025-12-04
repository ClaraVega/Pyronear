# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

import scrapy
from scrapy.pipelines.images import ImagesPipeline
from tqdm import tqdm
import os

class AlertwestImagePipeline(ImagesPipeline):

    def open_spider(self, spider):
        self.spiderinfo = self.SpiderInfo(spider)
        self.total = getattr(spider, "total_cams", 0)
        self.progress_bar = None

    def close_spider(self, spider):
        self.progress_bar.close()

    def get_media_requests(self, item, info):
        """Send a request to download the image with metadata"""

        if self.progress_bar is None:
            total = info.spider.total_cams or 0
            self.progress_bar = tqdm(
                total=total,
                desc="Downloading images 🚀 ",
                bar_format="{l_bar}\033[92m{bar}\033[0m| {n_fmt}/{total_fmt} images",
                unit="image"
            )

        url = item["image_url"]
        if url :
            self.progress_bar.update(1)
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

    def media_failed(self, failure, request, info):
        cam_id = request.meta.get("id")
        print(f"Failed to download image for camera ID {cam_id} because the camera is unavaiblable")
        return None

    def file_path(self, request, response=None, info=None, item=None):

        cam_id = str(item.get("id"))

        # If there is no azimuth, it is replaced by unknown
        azimuth = str(item.get("azimuth") or "unknown")
        filename = f"{cam_id}.jpg"

        return os.path.join(cam_id, azimuth, filename)