import logging
from sqlalchemy.types import String, TypeDecorator
from .encrypt_decrypt import decrypt_text, encrypt_text

logger = logging.getLogger(__name__)

class EncryptedString(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return encrypt_text(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        try:
            return decrypt_text(value)
        except Exception as e:
            logger.error(f"Decryption failed | type={type(e).__name__} | {e}")
            return value  