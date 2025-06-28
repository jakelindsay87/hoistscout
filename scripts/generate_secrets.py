#!/usr/bin/env python3
"""Generate secure secrets for HoistScraper production deployment."""

import os
import secrets
import base64
from cryptography.fernet import Fernet


def generate_secure_password(length: int = 32) -> str:
    """Generate a secure password."""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_hex_key(length: int = 32) -> str:
    """Generate a hex key."""
    return secrets.token_hex(length)


def generate_urlsafe_key(length: int = 32) -> str:
    """Generate a URL-safe key."""
    return secrets.token_urlsafe(length)


def generate_fernet_key() -> str:
    """Generate a Fernet encryption key."""
    return Fernet.generate_key().decode()


def main():
    """Generate all required secrets."""
    print("=" * 60)
    print("HoistScraper Security Configuration Generator")
    print("=" * 60)
    print()
    print("Copy these values to your .env file:")
    print()
    
    # Database credentials
    db_password = generate_secure_password()
    print("# Database Configuration")
    print("DB_USER=hoistscraper")
    print(f"DB_PASSWORD={db_password}")
    print("DB_NAME=hoistscraper")
    print()
    
    # Security configuration
    credential_salt = generate_hex_key(32)
    credential_passphrase = generate_secure_password(40)
    api_key = generate_urlsafe_key(32)
    
    print("# Security Configuration (REQUIRED)")
    print(f"CREDENTIAL_SALT={credential_salt}")
    print(f"CREDENTIAL_PASSPHRASE={credential_passphrase}")
    print(f"API_KEY={api_key}")
    print("REQUIRE_AUTH=true")
    print()
    
    # Optional: Direct encryption key
    print("# Alternative: Direct Encryption Key (instead of salt+passphrase)")
    print(f"# CREDENTIAL_ENCRYPTION_KEY={generate_fernet_key()}")
    print()
    
    # Queue configuration
    print("# Queue Configuration")
    print("USE_SIMPLE_QUEUE=true")
    print("WORKER_THREADS=4")
    print()
    
    # Example nginx basic auth
    print("# Optional: Nginx Basic Auth (for extra security)")
    nginx_user = "admin"
    nginx_pass = generate_secure_password(20)
    print(f"# htpasswd -bc .htpasswd {nginx_user} {nginx_pass}")
    print(f"# NGINX_USER={nginx_user}")
    print(f"# NGINX_PASS={nginx_pass}")
    print()
    
    print("=" * 60)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 60)
    print("1. NEVER commit these values to version control")
    print("2. Store the .env file with restrictive permissions (chmod 600)")
    print("3. Use a password manager to backup these credentials")
    print("4. Rotate credentials regularly")
    print("5. Use different credentials for each environment")
    print()
    print("To use these values:")
    print("1. Copy the output above to a .env file")
    print("2. Set file permissions: chmod 600 .env")
    print("3. Load in Docker: docker-compose --env-file .env up -d")
    print()
    
    # Save to file option
    save = input("Save to .env.production? (y/N): ").lower().strip()
    if save == 'y':
        env_content = f"""# HoistScraper Production Configuration
# Generated on: {os.popen('date').read().strip()}
# KEEP THIS FILE SECURE!

# Database Configuration
DB_USER=hoistscraper
DB_PASSWORD={db_password}
DB_NAME=hoistscraper
DATABASE_URL=postgresql://${{DB_USER}}:${{DB_PASSWORD}}@hoistscraper-db:5432/${{DB_NAME}}

# Security Configuration (REQUIRED)
CREDENTIAL_SALT={credential_salt}
CREDENTIAL_PASSPHRASE={credential_passphrase}
API_KEY={api_key}
REQUIRE_AUTH=true

# Queue Configuration
USE_SIMPLE_QUEUE=true
WORKER_THREADS=4

# Frontend Configuration
FRONTEND_API_URL=/api

# Crawler Configuration
CRAWL_CONCURRENCY=3
RATE_LIMIT_DELAY=2
DATA_DIR=/data

# Ollama Configuration
OLLAMA_HOST=http://hoistscraper-ollama:11434

# Worker Configuration
WORKER_TYPE=v2
"""
        
        with open('.env.production', 'w') as f:
            f.write(env_content)
        
        os.chmod('.env.production', 0o600)
        print(f"\nSecrets saved to .env.production with permissions 600")
        print("Remember to backup this file securely!")


if __name__ == '__main__':
    main()