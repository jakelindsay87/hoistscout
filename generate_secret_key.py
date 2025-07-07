#!/usr/bin/env python3
"""Generate a secure SECRET_KEY for HoistScout production"""
import secrets
import string

def generate_secret_key(length=64):
    """Generate a cryptographically secure secret key"""
    # Use all ASCII letters, digits, and some special characters
    # Avoiding characters that might cause issues in shell/env vars
    characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return ''.join(secrets.choice(characters) for _ in range(length))

# Generate multiple options
print("=== HoistScout Production SECRET_KEY Options ===\n")
print("Choose one of these secure secret keys for your production environment:")
print("(Each is 64 characters long and cryptographically secure)\n")

for i in range(3):
    secret_key = generate_secret_key()
    print(f"Option {i+1}:")
    print(f"{secret_key}")
    print()

print("=== Recommended Production SECRET_KEY ===")
recommended = generate_secret_key()
print(f"\n{recommended}\n")

print("=== How to use ===")
print("1. Copy one of the secret keys above")
print("2. In Render Dashboard, go to your API service")
print("3. Navigate to Environment > Environment Variables")
print("4. Add/Update: SECRET_KEY=<your-chosen-key>")
print("5. Also update the Worker service with the same SECRET_KEY")
print("6. Save and let services redeploy")
print("\nIMPORTANT: Use the SAME secret key for all services!")