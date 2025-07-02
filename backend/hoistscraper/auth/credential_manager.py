"""Credential management for authenticated website scraping."""

import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlmodel import Session, select
from loguru import logger

from hoistscraper.models_credentials import WebsiteCredential, WebsiteCredentialCreate


class CredentialManager:
    """Manages encrypted storage and retrieval of website credentials."""
    
    def __init__(self):
        # Get or generate encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate one."""
        key_env = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
        
        if key_env:
            # Use provided key
            return base64.urlsafe_b64decode(key_env.encode())
        else:
            # Generate key from environment variable or random salt
            salt_env = os.getenv("CREDENTIAL_SALT")
            if salt_env:
                salt = salt_env.encode()
            else:
                # Generate a random salt if not provided
                salt = os.urandom(16)
                logger.warning("Generated random salt - set CREDENTIAL_SALT env var for consistent encryption")
            
            # Use passphrase from environment or generate warning
            passphrase_env = os.getenv("CREDENTIAL_PASSPHRASE", "")
            if not passphrase_env:
                logger.error("CREDENTIAL_PASSPHRASE not set - credentials cannot be encrypted securely")
                raise ValueError("CREDENTIAL_PASSPHRASE environment variable must be set")
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(passphrase_env.encode()))
            return key
    
    def encrypt_password(self, password: str) -> str:
        """Encrypt a password."""
        return self.cipher.encrypt(password.encode()).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """Decrypt a password."""
        return self.cipher.decrypt(encrypted_password.encode()).decode()
    
    def store_credential(
        self, 
        session: Session, 
        credential_create: WebsiteCredentialCreate
    ) -> WebsiteCredential:
        """Store encrypted credentials for a website."""
        # Check if credential already exists
        existing = session.exec(
            select(WebsiteCredential).where(
                WebsiteCredential.website_id == credential_create.website_id
            )
        ).first()
        
        if existing:
            # Update existing
            existing.username = credential_create.username
            existing.password_encrypted = self.encrypt_password(credential_create.password)
            existing.auth_type = credential_create.auth_type
            existing.additional_fields = credential_create.additional_fields
            existing.notes = credential_create.notes
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        
        # Create new credential
        encrypted_password = self.encrypt_password(credential_create.password)
        
        db_credential = WebsiteCredential(
            website_id=credential_create.website_id,
            username=credential_create.username,
            password_encrypted=encrypted_password,
            auth_type=credential_create.auth_type,
            additional_fields=credential_create.additional_fields,
            notes=credential_create.notes
        )
        
        session.add(db_credential)
        session.commit()
        session.refresh(db_credential)
        
        logger.info(f"Stored credentials for website {credential_create.website_id}")
        return db_credential
    
    def get_credential(
        self, 
        session: Session, 
        website_id: int
    ) -> Optional[tuple[str, str, dict]]:
        """
        Get decrypted credentials for a website.
        
        Returns:
            Tuple of (username, password, additional_data) or None
        """
        credential = session.exec(
            select(WebsiteCredential).where(
                WebsiteCredential.website_id == website_id,
                WebsiteCredential.is_valid == True
            )
        ).first()
        
        if not credential:
            return None
        
        try:
            password = self.decrypt_password(credential.password_encrypted)
            
            # Parse additional fields if present
            additional_data = {}
            if credential.additional_fields:
                import json
                try:
                    additional_data = json.loads(credential.additional_fields)
                except:
                    pass
            
            # Update last used timestamp
            from datetime import datetime, timezone
            credential.last_used_at = datetime.now(timezone.utc)
            session.add(credential)
            session.commit()
            
            return (credential.username, password, additional_data)
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for website {website_id}: {e}")
            # Mark as invalid if decryption fails
            credential.is_valid = False
            session.add(credential)
            session.commit()
            return None
    
    def mark_invalid(self, session: Session, website_id: int):
        """Mark credentials as invalid (e.g., after auth failure)."""
        credential = session.exec(
            select(WebsiteCredential).where(
                WebsiteCredential.website_id == website_id
            )
        ).first()
        
        if credential:
            credential.is_valid = False
            session.add(credential)
            session.commit()
            logger.warning(f"Marked credentials for website {website_id} as invalid")


# Global instance
credential_manager = CredentialManager()


# Helper functions for easy access
def store_website_credential(
    session: Session,
    website_id: int,
    username: str,
    password: str,
    auth_type: str = "basic",
    additional_fields: Optional[dict] = None,
    notes: Optional[str] = None
) -> WebsiteCredential:
    """Store credentials for a website."""
    import json
    
    credential_create = WebsiteCredentialCreate(
        website_id=website_id,
        username=username,
        password=password,
        auth_type=auth_type,
        additional_fields=json.dumps(additional_fields) if additional_fields else None,
        notes=notes
    )
    
    return credential_manager.store_credential(session, credential_create)


def get_website_credentials(
    session: Session,
    website_id: int
) -> Optional[tuple[str, str, dict]]:
    """Get credentials for a website."""
    return credential_manager.get_credential(session, website_id)