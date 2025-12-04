# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface

from twisted.python.failure import Failure
import logging
import scrapy
from scrapy.pipelines.images import ImagesPipeline
from tqdm import tqdm
import time
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

    def file_path(self, request, response=None, info=None, item=None):
        # logging.getLogger(__name__).debug(
        #     "file_path called — request.meta=%r item=%r",
        #     getattr(request, 'meta', None),
        #     item
        # )

        cam_id = str(item.get("id"))
        azimuth = str(item.get("azimuth") or "unknown")
        filename = f"{cam_id}.jpg"

        # logging.getLogger(__name__).debug(
        #     "file_name = %r", filename
        # )
        return os.path.join(cam_id, azimuth, filename)

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
        
    
        ## Debug and diagnostics
        for ok, info_or_failure in results:
            if ok:
                continue

            # info_or_failure is normally a twisted.python.failure.Failure
            if isinstance(info_or_failure, Failure):
                tb = info_or_failure.getTraceback() or "<no traceback available>"
                logging.error("Media failed for item %r: type=%r value=%r\nTraceback:\n%s",
                              item.get('id'), info_or_failure.type, info_or_failure.value, tb)

                # Inspect chained exceptions (cause / context)
                try:
                    val = info_or_failure.value
                    cause = getattr(val, '__cause__', None)
                    context = getattr(val, '__context__', None)
                    if cause:
                        logging.error("Underlying cause: %r", repr(cause))
                    if context:
                        logging.error("Exception context: %r", repr(context))
                    logging.debug("Failure.value dir: %r", dir(val))
                except Exception:
                    logging.exception("Error while inspecting Failure cause/context")
            else:
                logging.error("Media failed for item %r: %r", item.get('id'), info_or_failure)

            # Diagnostics about IMAGES_STORE path and disk state
            try:
                images_store = None
                try:
                    images_store = info.spider.settings.get('IMAGES_STORE')
                except Exception:
                    images_store = None

                logging.error("Images store setting: %r", images_store)
                if images_store and isinstance(images_store, str):
                    try:
                        if os.path.exists(images_store):
                            logging.error("Images store exists, writable=%r", os.access(images_store, os.W_OK))
                            try:
                                import shutil
                                du = shutil.disk_usage(images_store)
                                logging.error("Disk usage for images store: total=%d free=%d", du.total, du.free)
                            except Exception:
                                logging.exception("Failed to get disk usage for images store")
                        else:
                            logging.error("Images store path does not exist: %r", images_store)
                    except Exception:
                        logging.exception("Error while checking images store path: %r", images_store)
                else:
                    logging.error("Images store is not a valid path string: %r", images_store)
            except Exception:
                logging.exception("Error while collecting images store diagnostics")

        return item