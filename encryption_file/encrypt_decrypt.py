from cryptography.fernet import Fernet
from core.settings import settings

def get_fernet() -> Fernet:
    key = settings.FERNET_SECRET_KEY
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)

fernet = get_fernet()

def encrypt_text(value: str) -> str:
    if value is None:
        return value
    return fernet.encrypt(value.encode()).decode()

def decrypt_text(value: str) -> str:
    if value is None:
        return value
    return fernet.decrypt(value.encode()).decode()