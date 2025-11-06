import pytest
import pytz
from unittest.mock import MagicMock
import os

def duration_to_seconds(duration_str):
    """
    Convert a duration string to the equivalent number of seconds.

    Args:
        duration_str (str): A duration string in the format "Xh" (X hours) or "Xmn" (X minutes).

    Returns:
        int: The number of seconds equivalent to the duration string.

    Raises:
        ValueError: If the duration string format is invalid.
    """
    duration_str = duration_str.lower()
    if duration_str.endswith("h"):
        hours = int(duration_str[:-1])
        return hours * 60 * 60
    elif duration_str.endswith("mn"):
        minutes = int(duration_str[:-2])
        return minutes * 60
    else:
        raise ValueError("Invalid duration string format")

def test_duration_to_seconds_hours():
    assert duration_to_seconds("6h") == 21600

def test_duration_to_seconds_minutes():
    assert duration_to_seconds("15mn") == 900

def test_duration_to_seconds_invalid():
    with pytest.raises(ValueError):
        duration_to_seconds("6hours")
        
""""
from Test_scrapp.py import generate_chunks

def test_generate_chunks_parses_jpeg_bytes():
    fake_response = type("FakeResp", (), {})()
    fake_response.content = b"--frame\r\nrandombytes\xff\xd8jpegdata--frame\r\n"
    chunks = list(generate_chunks(fake_response))
    assert len(chunks) == 1
    assert chunks[0].startswith(b"\xff\xd8")
"""



def test_local_time_for_CA():
    t = get_camera_local_time("CA")
    assert t.tzinfo.zone == pytz.timezone("America/Los_Angeles").zone
    
    

def process_camera_images(response, state, source, region, az_current):
    """
    Process and save camera images, organized by region, source, and azimuth.
    """
    local_time = get_camera_local_time(state)
    date_folder = local_time.strftime("%Y_%m_%d")
    source_path = os.path.join(
        OUTPUT_BASE_PATH, region, source, f"az_{az_current}", date_folder
    )
    os.makedirs(source_path, exist_ok=True)

    try:
        for i, chunk in enumerate(generate_chunks(response)):
            img_path = os.path.join(source_path, f"{str(i).zfill(8)}.jpg")
            with open(img_path, "wb") as f:
                f.write(chunk)

        sort_and_rename_images(source_path, local_time)
    except Exception as e:
        logging.error(f"Error processing {source}: {e}")

def test_process_camera_images_creates_jpgs(tmp_path):
    response = MagicMock()
    response.content = b"--frame\r\n\xff\xd8FAKEJPEGDATA--frame\r\n"
    state, source, region, az = "CA", "testcam", "LAC", "90"
    process_camera_images(response, state, source, region, az)
    saved_imgs = list(tmp_path.glob("**/*.jpg"))
    assert len(saved_imgs) > 0
    
    
    
    
    
if __name__ == "__main__":
    response = requests.get(CAMERAS_URL, headers=HEADERS)
    cameras_data = response.json()
    subset = cameras_data["features"][:2]  # test 2 cams
    download_and_process_images(subset)