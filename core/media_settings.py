

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "project_media" / "converted"
TEMP_DIR = BASE_DIR / "project_media" / "temp"
MEDIA_URL = "/project_media/converted"


MEDIA_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
