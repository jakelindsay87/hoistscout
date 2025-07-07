#!/usr/bin/env python3
"""Test the exact token verification logic"""
import jwt
from datetime import datetime
import json

# The token from the API (you'll need to update this with a fresh one)
SECRET_KEY = "ldV%0YU9gZ(!Iq()Mcs=obbqgzLVlA4GQM&-%-U*%LDoL5x_X=qu)o@RaWohIrK&"

def verify_token_like_api(token: str, token_type: str = "access"):
    """Replicate the API's verify_token logic"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        print(f"Token decoded successfully!")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Check token type
        if payload.get("type") != token_type:
            print(f"ERROR: Token type mismatch! Expected '{token_type}', got '{payload.get('type')}'")
            return None
            
        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        
        print(f"\nExtracted data:")
        print(f"  user_id: {user_id} (type: {type(user_id)})")
        print(f"  email: {email}")
        print(f"  role: {role}")
        
        if user_id is None:
            print("ERROR: user_id is None!")
            return None
            
        return {
            "user_id": user_id,
            "email": email,
            "role": role
        }
        
    except jwt.ExpiredSignatureError:
        print("ERROR: Token has expired!")
        return None
    except jwt.InvalidTokenError as e:
        print(f"ERROR: JWT verification failed: {type(e).__name__}: {e}")
        return None

# Test with a sample token
print("=== Testing Token Verification Logic ===\n")

# First, let's create a test token to understand the format
test_payload = {
    "sub": 3,
    "email": "demo@hoistscout.com",
    "role": "viewer",
    "exp": int(datetime.now().timestamp()) + 1800,
    "type": "access"
}

test_token = jwt.encode(test_payload, SECRET_KEY, algorithm="HS256")
print(f"Test token created: {test_token[:50]}...\n")

result = verify_token_like_api(test_token)
print(f"\nVerification result: {result}")

print("\n=== Potential Issues ===")
print("1. Check if 'type' field is included in token payload")
print("2. Verify user_id is an integer in the database")
print("3. Ensure TokenData class in schemas/auth.py matches expected fields")
print("4. Check if database connection is working properly")