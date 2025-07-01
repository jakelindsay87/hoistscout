from typing import Dict, Any
from cryptography.fernet import Fernet
import json
import structlog
from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class SecureCredentialManager:
    def __init__(self):
        self.key = settings.secret_key.encode()[:32].ljust(32, b'0')
        self.cipher = Fernet(Fernet.generate_key())
        
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> bytes:
        try:
            json_data = json.dumps(credentials)
            encrypted = self.cipher.encrypt(json_data.encode())
            return encrypted
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_credentials(self, encrypted: bytes) -> Dict[str, Any]:
        try:
            decrypted = self.cipher.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise