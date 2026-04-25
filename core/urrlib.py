import re
import unicodedata
from urllib.parse import quote


def safe_quote(s):
    return quote(s)


def sanitize_filename(filename: str) -> str:

    filename = unicodedata.normalize("NFKD", filename)

    filename = re.sub(r"[\\/]+", "_", filename)

    filename = re.sub(r'[<>:"|?*]', "", filename)

    filename = re.sub(r"\s+", "_", filename)

    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

    filename = re.sub(r"_+", "_", filename)

    filename = filename.strip("._")

    return filename[:225]
