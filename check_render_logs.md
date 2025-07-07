# Check Render Logs for Database Issues

The authentication is failing at the database lookup stage. Here's what's happening:

1. ✅ Login works (user exists, password correct)
2. ✅ JWT token is created correctly with all fields
3. ✅ Token can be decoded with the new SECRET_KEY
4. ❌ Database lookup for user by ID fails

## Most Likely Cause: Database Connection Issue

The `get_current_user` function is failing at this line:
```python
stmt = select(User).where(User.id == token_data.user_id)
result = await db.execute(stmt)
user = result.scalar_one_or_none()
```

## Check These in Render Dashboard:

1. **API Service Logs** - Look for:
   - Database connection errors
   - "Connection refused" or "Connection timeout"
   - SQLAlchemy errors
   - PostgreSQL connection pool exhausted

2. **Environment Variables** - Verify:
   - `DATABASE_URL` is set correctly
   - Format: `postgresql+asyncpg://user:password@host:port/database`
   - The database is accessible from Render

3. **Database Service** - Check if:
   - PostgreSQL service is running
   - Connection limit not exceeded
   - Database migrations completed

## Quick Fix to Test:

Add this environment variable to force new connections:
```
SQLALCHEMY_POOL_SIZE=5
SQLALCHEMY_MAX_OVERFLOW=10
SQLALCHEMY_POOL_TIMEOUT=30
```

## The Real Issue:

The async database session might be failing silently. The registration works because it creates a new session, but the authentication reuses a pooled connection that might be stale.

## Immediate Action:

1. Restart the API service in Render
2. Check the logs immediately after restart
3. Look for database connection initialization messages

The fact that registration works but authentication fails points to a connection pool issue with async SQLAlchemy sessions.