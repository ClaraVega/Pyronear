import os
import sys
# Ensure project root is on sys.path so tests can import scrappy_pyronear
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import requests
from scrappy_pyronear.spiders.alertwest_spider import AlertwestSpider

# Execution line : pytest -v test_alertwest_spider.py

API_URL = "https://api.cdn.prod.alertwest.com/api/getCameraDataByLoc"


def test_api_access():
    """Check API accessibility and expected JSON structure."""
    response = requests.get(API_URL, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data and "cams" in data["data"]


def test_parse_creates_items(tmp_path):
    """Test parse() on a fake response."""
    spider = AlertwestSpider()
    fake_json = {
    "data": {
        "cams": {
            "key": [
                {
                    "ato": "camAutoTargetOverride",
                    "p": "camAzimuth",
                    "t": "camElevation",
                    "z": "camZoom",
                    "af": "camAutoFocus",
                    "foc": "camFocus",
                    "br": "camBrightness",
                    "ptz": "camHasPTZ",
                    "id": "camId",
                    "pv": "camPrivate",
                    "lmt": "camLastMoved",
                    "lid": "camLocation",
                    "cn": "camName",
                    "hn": "camHostname",
                    "img": "camScreenshot",
                    "off": "camOffline",
                    "cl": "camLatency",
                    "isp": "camISP",
                    "typ": "camType",
                    "cc": "camClass",
                    "fov": "camViewWidth",
                    "sp": "camSponsor",
                    "co": "camCounty",
                    "st": "camState",
                    "pn": "camProviderName",
                    "pl": "camProviderLink",
                    "pi": "camProviderLogo",
                    "ps": "camProviderLogoSquare",
                    "tb": "camTourable",
                    "trg": "camTouring",
                    "tr": "camTour"
                }
            ]
        }
    }
}

    body = json.dumps(fake_json)
    response = requests.get(url=API_URL, body=body, encoding="utf-8")

    results = list(spider.parse(response))
    dict_items = [r for r in results if isinstance(r, dict)]

    assert len(dict_items) == 1
    item = dict_items[0]

    assert ["Azimuth","Id","Screenshot","Offline"] in item


def test_save_image(tmp_path):
    """Test that save_image writes a file."""
    spider = AlertwestSpider()
    img_bytes = b"fakeimagecontent"

    class DummyResponse:
        status = 200
        url = "https://example.com/img.jpg"
        body = img_bytes
        meta = {"id": "123", "lmt": 456}

    spider.save_image(DummyResponse())

    path = os.path.join("images", "123_456.jpg")
    assert os.path.exists(path)
    os.remove(path)