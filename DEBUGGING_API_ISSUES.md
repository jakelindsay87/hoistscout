# HoistScout API Connection Issues - Comprehensive Debugging Report

## CRITICAL ISSUE: JWT Token Verification Failure

The main issue is that JWT tokens issued by the API cannot be verified because the SECRET_KEY on Render differs from the expected value.

### Evidence:
1. Login works and returns tokens
2. Token structure is valid (header, payload, signature)
3. Token cannot be decoded with any expected secret key
4. All authenticated endpoints return 401

## Complete List of 20 Potential Issues

### 1. ❌ **SECRET_KEY Mismatch** (CONFIRMED)
- **Problem**: Production API uses different SECRET_KEY than default
- **Fix**: Set SECRET_KEY environment variable in Render to match expected value
- **Test**: `jwt.decode(token, "your-secret-key", algorithms=["HS256"])`

### 2. ❌ **Frontend Username/Email Mismatch** (CONFIRMED)
- **Problem**: Frontend login form uses "username" field, backend expects email in OAuth2 format
- **Fix**: Update frontend to use email field or update backend to accept username
- **Current**: OAuth2 standard requires 'username' parameter even for email login

### 3. ❌ **Missing Health Endpoint** (CONFIRMED)
- **Problem**: /health returns 404, should be at /api/health
- **Fix**: Add health endpoint to API routes in main.py

### 4. ❌ **JWT Token Validation Failing** (CONFIRMED)
- **Problem**: verify_token() in auth.py fails due to SECRET_KEY mismatch
- **Fix**: Ensure consistent SECRET_KEY across all services

### 5. ⚠️ **CORS Preflight Issues**
- **Problem**: CORS headers present but may not cover all scenarios
- **Test**: Check OPTIONS requests for all endpoints
- **Fix**: Ensure CORS middleware handles all methods and headers

### 6. ⚠️ **Token Expiration Too Short**
- **Problem**: Default 30 minutes may be too short
- **Test**: Check 'exp' claim in JWT payload
- **Fix**: Increase ACCESS_TOKEN_EXPIRE_MINUTES in config

### 7. ⚠️ **Algorithm Mismatch**
- **Problem**: JWT algorithm might differ between services
- **Test**: Check 'alg' in JWT header (currently HS256)
- **Fix**: Ensure ALGORITHM="HS256" in all services

### 8. ⚠️ **Bearer Token Format**
- **Problem**: Frontend might not format Authorization header correctly
- **Test**: Ensure header is "Bearer <token>" with space
- **Fix**: Update frontend API client

### 9. ⚠️ **Database Connection Issues**
- **Problem**: User lookup might fail due to DB connection
- **Test**: Check Render logs for database errors
- **Fix**: Verify DATABASE_URL is set correctly

### 10. ⚠️ **User Model Field Mismatch**
- **Problem**: JWT contains 'sub' with user ID, but lookup might fail
- **Test**: Verify User.id exists in database
- **Fix**: Check user model and migrations

### 11. ⚠️ **Missing Authentication Middleware**
- **Problem**: Some endpoints might bypass authentication
- **Test**: Check if get_current_user dependency is applied
- **Fix**: Add Depends(get_current_user) to all protected routes

### 12. ⚠️ **Redis Session Issues**
- **Problem**: If using Redis for sessions, connection might fail
- **Test**: Check REDIS_URL configuration
- **Fix**: Ensure Redis is running and accessible

### 13. ⚠️ **Frontend API Base URL**
- **Problem**: Frontend might use wrong API URL
- **Test**: Check NEXT_PUBLIC_API_URL in frontend
- **Fix**: Set to https://hoistscout-api.onrender.com

### 14. ⚠️ **SSL/TLS Certificate Issues**
- **Problem**: HTTPS certificate validation might fail
- **Test**: Check for SSL errors in browser console
- **Fix**: Ensure valid SSL certificate on Render

### 15. ⚠️ **Rate Limiting**
- **Problem**: Render or Cloudflare might rate limit requests
- **Test**: Check response headers for rate limit info
- **Fix**: Implement retry logic with backoff

### 16. ⚠️ **Cookie vs Bearer Token Confusion**
- **Problem**: API might expect cookies instead of headers
- **Test**: Check if httponly cookies are set
- **Fix**: Standardize on Bearer token authentication

### 17. ⚠️ **Frontend State Management**
- **Problem**: Token might not persist correctly in localStorage
- **Test**: Check browser DevTools Application tab
- **Fix**: Ensure token is saved after login

### 18. ⚠️ **API Gateway/Proxy Issues**
- **Problem**: Render's proxy might strip headers
- **Test**: Log all headers received by API
- **Fix**: Use alternative header names if needed

### 19. ⚠️ **Token Payload Structure**
- **Problem**: Frontend might expect different claims in JWT
- **Test**: Decode token and check payload structure
- **Fix**: Align token payload with frontend expectations

### 20. ⚠️ **Case Sensitivity Issues**
- **Problem**: Header names or field names might have case issues
- **Test**: Check "authorization" vs "Authorization"
- **Fix**: Use consistent casing throughout

## Immediate Action Items

1. **Set SECRET_KEY in Render Dashboard**:
   ```
   SECRET_KEY=hoistscout-production-secret-key-very-long-and-random
   ```

2. **Verify Environment Variables**:
   - Check all services have same SECRET_KEY
   - Ensure ALGORITHM is consistent (HS256)
   - Verify DATABASE_URL is correct

3. **Update Frontend**:
   - Fix username/email field mismatch
   - Ensure proper Bearer token format
   - Add better error handling

4. **Add Logging**:
   - Log all authentication attempts
   - Log token verification failures
   - Log header values received

## Testing Script

```python
import httpx
import jwt
import asyncio

async def test_auth_flow():
    # Test with your actual SECRET_KEY
    SECRET_KEY = "your-secret-key-from-render"
    
    async with httpx.AsyncClient() as client:
        # Login
        resp = await client.post(
            "https://hoistscout-api.onrender.com/api/auth/login",
            data={"username": "demo@hoistscout.com", "password": "demo123"}
        )
        
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            
            # Decode token
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                print(f"Token valid! Payload: {payload}")
            except jwt.InvalidTokenError as e:
                print(f"Token invalid: {e}")
            
            # Test authenticated endpoint
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(
                "https://hoistscout-api.onrender.com/api/auth/me",
                headers=headers
            )
            print(f"Auth test: {resp.status_code}")

asyncio.run(test_auth_flow())
```

## Root Cause
The primary issue is SECRET_KEY mismatch between what the API uses for signing JWTs and what it expects for verification. This must be fixed in Render's environment variables.