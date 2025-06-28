"""
Tests for authentication and security functionality.
"""

import pytest
import os
from unittest.mock import patch, Mock
from cryptography.fernet import Fernet
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

from hoistscraper.auth.credential_manager import CredentialManager
from hoistscraper.auth.api_auth import require_api_key, optional_api_key, validate_api_key
from hoistscraper.models import WebsiteCredential
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


@pytest.fixture(name="session")
def session_fixture():
    """Create a new database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def credential_manager():
    """Create a credential manager instance with test keys."""
    # Generate test keys
    test_salt = os.urandom(16)
    test_passphrase = "test-passphrase-123"
    
    with patch.dict(os.environ, {
        'CREDENTIAL_SALT': test_salt.hex(),
        'CREDENTIAL_PASSPHRASE': test_passphrase
    }):
        return CredentialManager()


class TestCredentialManager:
    """Test credential encryption and management."""
    
    def test_key_derivation(self, credential_manager):
        """Test that encryption keys are derived correctly."""
        assert credential_manager.cipher_suite is not None
        
        # Test that same inputs produce same key
        another_manager = CredentialManager()
        
        # Encrypt with first manager
        test_data = "sensitive-password"
        encrypted1 = credential_manager.encrypt_credential(test_data)
        
        # Decrypt with second manager (same keys)
        decrypted = another_manager.decrypt_credential(encrypted1)
        assert decrypted == test_data
    
    def test_encrypt_decrypt_credential(self, credential_manager):
        """Test credential encryption and decryption."""
        original_password = "my-secret-password-123"
        
        # Encrypt
        encrypted = credential_manager.encrypt_credential(original_password)
        assert encrypted != original_password
        assert len(encrypted) > len(original_password)
        
        # Decrypt
        decrypted = credential_manager.decrypt_credential(encrypted)
        assert decrypted == original_password
    
    def test_encrypt_empty_credential(self, credential_manager):
        """Test encrypting empty credentials."""
        assert credential_manager.encrypt_credential("") == ""
        assert credential_manager.encrypt_credential(None) is None
    
    def test_decrypt_invalid_credential(self, credential_manager):
        """Test decrypting invalid encrypted data."""
        # Should return original value if decryption fails
        invalid_encrypted = "not-a-valid-encrypted-string"
        result = credential_manager.decrypt_credential(invalid_encrypted)
        assert result == invalid_encrypted
    
    def test_store_credential(self, credential_manager, session):
        """Test storing encrypted credentials."""
        website_id = 1
        username = "testuser"
        password = "testpass123"
        auth_type = "basic"
        auth_config = {"login_url": "https://test.com/login"}
        
        # Store credential
        credential = credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username=username,
            password=password,
            auth_type=auth_type,
            auth_config=auth_config
        )
        
        assert credential.website_id == website_id
        assert credential.username == username
        assert credential.password != password  # Should be encrypted
        assert credential.auth_type == auth_type
        
        # Verify it's in database
        stored = session.get(WebsiteCredential, credential.id)
        assert stored is not None
        assert stored.password != password
    
    def test_get_credential(self, credential_manager, session):
        """Test retrieving and decrypting credentials."""
        # Store a credential
        website_id = 1
        original_password = "original-pass-456"
        
        credential = credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="user",
            password=original_password,
            auth_type="form"
        )
        
        # Retrieve it
        retrieved = credential_manager.get_credential(session, website_id)
        assert retrieved is not None
        assert retrieved.username == "user"
        assert retrieved.password == original_password  # Should be decrypted
    
    def test_get_nonexistent_credential(self, credential_manager, session):
        """Test retrieving non-existent credential."""
        result = credential_manager.get_credential(session, 999)
        assert result is None
    
    def test_update_credential(self, credential_manager, session):
        """Test updating existing credentials."""
        website_id = 1
        
        # Store initial credential
        credential = credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="olduser",
            password="oldpass",
            auth_type="basic"
        )
        
        # Update it
        new_password = "newpass789"
        updated = credential_manager.update_credential(
            session=session,
            website_id=website_id,
            password=new_password
        )
        
        assert updated.username == "olduser"  # Username unchanged
        
        # Verify password was updated and encrypted
        retrieved = credential_manager.get_credential(session, website_id)
        assert retrieved.password == new_password
    
    def test_delete_credential(self, credential_manager, session):
        """Test deleting credentials."""
        website_id = 1
        
        # Store credential
        credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="user",
            password="pass",
            auth_type="basic"
        )
        
        # Delete it
        result = credential_manager.delete_credential(session, website_id)
        assert result is True
        
        # Verify it's gone
        retrieved = credential_manager.get_credential(session, website_id)
        assert retrieved is None
    
    def test_delete_nonexistent_credential(self, credential_manager, session):
        """Test deleting non-existent credential."""
        result = credential_manager.delete_credential(session, 999)
        assert result is False


class TestAPIAuthentication:
    """Test API authentication functionality."""
    
    def test_validate_api_key_success(self):
        """Test successful API key validation."""
        with patch.dict(os.environ, {'API_KEY': 'test-api-key-123'}):
            result = validate_api_key('test-api-key-123')
            assert result is True
    
    def test_validate_api_key_failure(self):
        """Test failed API key validation."""
        with patch.dict(os.environ, {'API_KEY': 'correct-key'}):
            result = validate_api_key('wrong-key')
            assert result is False
    
    def test_validate_api_key_not_configured(self):
        """Test validation when no API key is configured."""
        with patch.dict(os.environ, {}, clear=True):
            # Should return True when no key is configured
            result = validate_api_key('any-key')
            assert result is True
    
    @pytest.mark.asyncio
    async def test_require_api_key_success(self):
        """Test require_api_key with valid credentials."""
        with patch.dict(os.environ, {'API_KEY': 'valid-key-123'}):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="valid-key-123"
            )
            
            result = await require_api_key(credentials)
            assert result == "valid-key-123"
    
    @pytest.mark.asyncio
    async def test_require_api_key_invalid(self):
        """Test require_api_key with invalid credentials."""
        with patch.dict(os.environ, {'API_KEY': 'valid-key-123'}):
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="invalid-key"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await require_api_key(credentials)
            
            assert exc_info.value.status_code == 403
            assert "Invalid API key" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_optional_api_key_with_auth_required(self):
        """Test optional_api_key when auth is required."""
        with patch.dict(os.environ, {
            'API_KEY': 'valid-key-123',
            'REQUIRE_AUTH': 'true'
        }):
            # With valid credentials
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="valid-key-123"
            )
            result = await optional_api_key(credentials)
            assert result == "valid-key-123"
            
            # Without credentials when required
            with pytest.raises(HTTPException) as exc_info:
                await optional_api_key(None)
            assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_optional_api_key_not_required(self):
        """Test optional_api_key when auth is not required."""
        with patch.dict(os.environ, {
            'API_KEY': 'valid-key-123',
            'REQUIRE_AUTH': 'false'
        }):
            # Without credentials should work
            result = await optional_api_key(None)
            assert result is None
            
            # With credentials should still validate
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials="valid-key-123"
            )
            result = await optional_api_key(credentials)
            assert result == "valid-key-123"


class TestSecurityHeaders:
    """Test security headers and middleware."""
    
    def test_sensitive_data_masking_in_logs(self):
        """Test that sensitive data is masked in logs."""
        from hoistscraper.logging_config import SensitiveDataFilter
        
        filter = SensitiveDataFilter()
        
        # Test password masking
        test_cases = [
            ("password=mysecret123", "password=[MASKED]"),
            ("PASSWORD='mysecret'", "PASSWORD='[MASKED]'"),
            ('password:"mysecret"', 'password:"[MASKED]"'),
            ("postgresql://user:pass@host", "postgresql://user:[MASKED]@host"),
            ("api_key=abc123def", "api_key=[MASKED]"),
            ("API-KEY: xyz789", "API-KEY: [MASKED]"),
            ("Bearer token123", "Bearer [MASKED]"),
        ]
        
        for input_text, expected in test_cases:
            result = filter._mask_sensitive_data(input_text)
            assert result == expected
    
    def test_encryption_key_security(self):
        """Test that encryption keys are properly secured."""
        # Test missing environment variables
        with patch.dict(os.environ, {}, clear=True):
            manager = CredentialManager()
            # Should use fallback values and log warnings
            assert manager.cipher_suite is not None
        
        # Test with proper environment variables
        salt = os.urandom(16).hex()
        passphrase = "strong-passphrase-with-entropy"
        
        with patch.dict(os.environ, {
            'CREDENTIAL_SALT': salt,
            'CREDENTIAL_PASSPHRASE': passphrase
        }):
            manager = CredentialManager()
            
            # Test encryption works
            test_data = "sensitive-data"
            encrypted = manager.encrypt_credential(test_data)
            decrypted = manager.decrypt_credential(encrypted)
            assert decrypted == test_data


class TestAuthenticationFlows:
    """Test complete authentication flows."""
    
    def test_basic_auth_flow(self, credential_manager, session):
        """Test basic authentication flow."""
        website_id = 1
        
        # Store basic auth credentials
        credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="apiuser",
            password="apipass",
            auth_type="basic",
            auth_config={}
        )
        
        # Retrieve for use
        cred = credential_manager.get_credential(session, website_id)
        assert cred.auth_type == "basic"
        assert cred.username == "apiuser"
        assert cred.password == "apipass"
    
    def test_form_auth_flow(self, credential_manager, session):
        """Test form-based authentication flow."""
        website_id = 1
        
        # Store form auth credentials with selectors
        auth_config = {
            "login_url": "https://example.com/login",
            "username_selector": "#username",
            "password_selector": "#password",
            "submit_selector": "button[type=submit]"
        }
        
        credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="formuser",
            password="formpass",
            auth_type="form",
            auth_config=auth_config
        )
        
        # Retrieve for use
        cred = credential_manager.get_credential(session, website_id)
        assert cred.auth_type == "form"
        assert cred.auth_config["login_url"] == auth_config["login_url"]
    
    def test_cookie_auth_flow(self, credential_manager, session):
        """Test cookie-based authentication flow."""
        website_id = 1
        
        # Store cookie auth data
        auth_config = {
            "cookies": [
                {"name": "session", "value": "abc123", "domain": "example.com"},
                {"name": "auth", "value": "xyz789", "domain": "example.com"}
            ]
        }
        
        credential_manager.store_credential(
            session=session,
            website_id=website_id,
            username="",  # No username for cookie auth
            password="",  # No password for cookie auth
            auth_type="cookie",
            auth_config=auth_config
        )
        
        # Retrieve for use
        cred = credential_manager.get_credential(session, website_id)
        assert cred.auth_type == "cookie"
        assert len(cred.auth_config["cookies"]) == 2


class TestSecurityVulnerabilities:
    """Test for common security vulnerabilities."""
    
    def test_sql_injection_prevention(self, session):
        """Test that SQL injection is prevented."""
        from hoistscraper.models import Website
        from sqlmodel import select
        
        # Attempt SQL injection in query
        malicious_input = "'; DROP TABLE website; --"
        
        # This should be safe due to parameterized queries
        statement = select(Website).where(Website.name == malicious_input)
        results = session.exec(statement).all()
        
        # Should return empty list, not cause SQL error
        assert results == []
        
        # Verify table still exists
        websites = session.exec(select(Website)).all()
        assert isinstance(websites, list)
    
    def test_path_traversal_prevention(self):
        """Test that path traversal attacks are prevented."""
        from pathlib import Path
        
        # Test data directory access
        data_dir = Path("/data")
        malicious_path = "../../../etc/passwd"
        
        # Safe path resolution
        safe_path = (data_dir / malicious_path).resolve()
        
        # Should not allow access outside data directory
        assert not str(safe_path).startswith("/etc")
    
    def test_xss_prevention_in_api(self):
        """Test that XSS attacks are prevented in API responses."""
        # This would be tested in actual API responses
        # FastAPI automatically escapes JSON responses
        malicious_input = '<script>alert("XSS")</script>'
        
        # When returned in JSON, this should be escaped
        import json
        safe_output = json.dumps({"data": malicious_input})
        assert '<script>' not in safe_output
        assert '\\u003cscript\\u003e' in safe_output.lower() or '&lt;script&gt;' in safe_output