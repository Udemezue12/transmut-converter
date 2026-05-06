import hashlib

import requests
from quart import abort


class ComputeHash:

    def compute_file_hash_sync(self, file_url: str) -> str:
        try:
            resp = requests.get(file_url, timeout=30)
        except requests.RequestException:
            abort(400, description="Failed to fetch file")

        if resp.status_code != 200:
            abort(400, description="Failed to fetch file")

        return hashlib.sha256(resp.content).hexdigest()
    def hash_email(self, email: str) -> str:
     return hashlib.sha256(email.lower().encode()).hexdigest()
