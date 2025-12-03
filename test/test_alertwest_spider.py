import os
import sys
# Ensure project root is on sys.path so tests can import scrappy_pyronear
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import shutil
import json
import requests
from scrappy_pyronear.spiders.alertwest_spider import ROOT_FOLDER_IMAGE, AlertwestSpider
from scrapy.http import TextResponse

# Execution line : pytest -v .\test\test_alertwest_spider.py

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
            "key": {
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
                },  
            "data": [
                {
                    "p": "90",
                    "lmt": "1763078579",
                    "id": "123",
                    "img": "test.jpg",
                    "cn": "TestCam2"
                }
            ]
        }
    }
}

    body = json.dumps(fake_json)
    response = TextResponse(url=API_URL, body=body.encode("utf-8"), encoding="utf-8")

    results = list(spider.parse(response))
    dict_items = [r for r in results if isinstance(r, dict)]

    assert len(dict_items) >= 1
    item = dict_items[0]

    assert item["id"] == "123"
    assert item["name"] == "TestCam2"
    assert item["azimuth"] == "90"
    assert isinstance(item["last_moved"], int)
    assert item["last_moved"] == int("1763078579")
    assert "image_url" in item and item["image_url"].startswith(f"https://img.cdn.prod.alertwest.com/data/thumb/{item['id']}/")
    assert item["image_url"].endswith("test.jpg")

    # s'assurer qu'une requête d'image a bien été générée avec le bon meta
    assert any(getattr(r, "meta", {}).get("id") == "123" for r in results)


def test_parse_handles_missing_properties():
    """When some short keys are missing, parser should still yield entries with None/defaults."""
    spider = AlertwestSpider()
    fake_json = {
        "data": {"cams": {"key": {"id": "camId", "lmt": "camLastMoved"}, "data": [{"id": "999"}]}}
    }
    body = json.dumps(fake_json)
    response = TextResponse(url=API_URL, body=body.encode("utf-8"), encoding="utf-8")

    results = list(spider.parse(response))
    dict_items = [r for r in results if isinstance(r, dict)]
    assert len(dict_items) == 1
    item = dict_items[0]
    assert item["id"] == "999"
    # last_moved should be parsed (missing => default '0' -> int 0)
    assert item["last_moved"] == 0
    # missing name/azimuth/image_url -> values may be None or constructed; ensure keys exist
    assert "name" in item and "azimuth" in item and "image_url" in item

    # When cam_id is present but azimuth is None, no scrapy.Request should be yielded
    # to avoid directory paths containing the string "None"
    request_items = [r for r in results if hasattr(r, "meta")]
    assert len(request_items) == 0, "No Request should be yielded when azimuth is None"


def test_parse_skips_request_when_cam_id_is_none():
    """When cam_id is None, no scrapy.Request should be yielded."""
    spider = AlertwestSpider()
    # Missing camId in keys, so cam_id will be None
    fake_json = {
        "data": {"cams": {"key": {"p": "camAzimuth", "lmt": "camLastMoved"}, "data": [{"p": "90", "lmt": "1763078579"}]}}
    }
    body = json.dumps(fake_json)
    response = TextResponse(url=API_URL, body=body.encode("utf-8"), encoding="utf-8")

    results = list(spider.parse(response))
    # dict items should still be yielded
    dict_items = [r for r in results if isinstance(r, dict)]
    assert len(dict_items) == 1

    # No scrapy.Request should be yielded when cam_id is None
    request_items = [r for r in results if hasattr(r, "meta")]
    assert len(request_items) == 0, "No Request should be yielded when cam_id is None"


def test_parse_no_data_returns_nothing():
    spider = AlertwestSpider()
    fake_json = {"data": {"cams": {"key": {}, "data": []}}}
    body = json.dumps(fake_json)
    response = TextResponse(url=API_URL, body=body.encode("utf-8"), encoding="utf-8")
    results = list(spider.parse(response))
    # No dict items and no requests expected
    assert results == []


def test_save_image_writes_file_and_content():
    """Test that save_image writes a file with the exact content."""
    # ensure clean state
    if ROOT_FOLDER_IMAGE.exists():
        shutil.rmtree(ROOT_FOLDER_IMAGE)

    spider = AlertwestSpider()
    img_bytes = b"fakeimagecontent"

    class DummyResponse:
        status = 200
        url = "https://example.com/img.jpg"
        body = img_bytes
        meta = {"id": "123", "last_moved": 456, "azimuth": "90"}

    spider.save_image(DummyResponse())

    expected_path = ROOT_FOLDER_IMAGE / "123" / str(DummyResponse.meta["azimuth"]) / f"123_456.jpg"
    assert expected_path.exists(), f"Expected image file at {expected_path} but it does not exist"

    # verify content
    with expected_path.open("rb") as f:
        content = f.read()
    assert content == img_bytes

    # cleanup
    shutil.rmtree(ROOT_FOLDER_IMAGE)


def test_save_image_ignores_404():
    # ensure clean state
    if ROOT_FOLDER_IMAGE.exists():
        shutil.rmtree(ROOT_FOLDER_IMAGE)

    spider = AlertwestSpider()
    class Dummy404:
        status = 404
        url = "https://example.com/no.jpg"
        body = b""
        meta = {"id": "404", "last_moved": 0, "azimuth": "0"}

    spider.save_image(Dummy404())

    # no files or directories should be created
    assert not ROOT_FOLDER_IMAGE.exists()