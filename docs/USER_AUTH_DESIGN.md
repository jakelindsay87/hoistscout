# User Authentication System Design for HoistScraper

## Overview

This document outlines the design for implementing a comprehensive user authentication and authorization system for HoistScraper.

## Architecture

### 1. Authentication Method: JWT (JSON Web Tokens)

**Why JWT?**
- Stateless authentication suitable for distributed systems
- Works well with React/Next.js frontend
- Can include user roles and permissions in token
- Easy to implement with FastAPI

### 2. User Roles

```python
class UserRole(str, Enum):
    ADMIN = "admin"          # Full system access
    EDITOR = "editor"        # Can create/edit websites and opportunities
    REVIEWER = "reviewer"    # Can review opportunities
    VIEWER = "viewer"        # Read-only access
    API_USER = "api_user"    # Programmatic access only
```

### 3. Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP
);

-- User sessions (for refresh tokens)
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- API keys for programmatic access
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    permissions JSONB,
    last_used TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

-- Audit log
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INT,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Implementation Plan

### Phase 1: Core Authentication (Week 1)

#### 1.1 User Model
```python
# backend/hoistscraper/models/user.py
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from pydantic import EmailStr, validator
import bcrypt

class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True, min_length=3, max_length=50)
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    is_active: bool = True
    is_verified: bool = False

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
    
    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

class UserCreate(SQLModel):
    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        # Add password complexity requirements
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

#### 1.2 JWT Token Management
```python
# backend/hoistscraper/auth/jwt_auth.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: Dict[str, Any]):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    session: Session = Depends(get_session)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
            
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Inactive user")
            
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

#### 1.3 Authentication Endpoints
```python
# backend/hoistscraper/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.post("/register")
async def register(
    user_create: UserCreate,
    session: Session = Depends(get_session)
):
    # Check if user exists
    existing = session.exec(
        select(User).where(
            (User.email == user_create.email) | 
            (User.username == user_create.username)
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user
    user = User(
        email=user_create.email,
        username=user_create.username,
        full_name=user_create.full_name,
        password_hash=User.hash_password(user_create.password)
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    # Log registration
    audit_log(session, user.id, "user_registered", "user", user.id)
    
    return {"message": "User created successfully", "user_id": user.id}

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
    request: Request = None
):
    # Find user
    user = session.exec(
        select(User).where(
            (User.email == form_data.username) | 
            (User.username == form_data.username)
        )
    ).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(status_code=401, detail="Account locked")
    
    # Verify password
    if not user.verify_password(form_data.password):
        # Increment failed attempts
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
        session.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Reset failed attempts
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    session.commit()
    
    # Create tokens
    access_token = create_access_token({"sub": user.id, "role": user.role})
    refresh_token = create_refresh_token({"sub": user.id})
    
    # Store refresh token
    session_record = UserSession(
        user_id=user.id,
        refresh_token=refresh_token,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent")
    )
    session.add(session_record)
    session.commit()
    
    # Log login
    audit_log(session, user.id, "user_login", "user", user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name
        }
    }

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    session: Session = Depends(get_session)
):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("sub")
        
        # Verify refresh token exists and is valid
        session_record = session.exec(
            select(UserSession).where(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session_record:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user
        user = session.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Create new access token
        access_token = create_access_token({"sub": user.id, "role": user.role})
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Invalidate all user sessions
    session.exec(
        select(UserSession).where(UserSession.user_id == current_user.id)
    ).delete()
    session.commit()
    
    audit_log(session, current_user.id, "user_logout", "user", current_user.id)
    
    return {"message": "Logged out successfully"}
```

### Phase 2: Authorization System (Week 2)

#### 2.1 Permission Decorators
```python
# backend/hoistscraper/auth/permissions.py
from functools import wraps
from typing import List
from fastapi import HTTPException, Depends

def require_role(allowed_roles: List[UserRole]):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permissions. Required roles: {allowed_roles}"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage example
@router.post("/api/websites")
@require_role([UserRole.ADMIN, UserRole.EDITOR])
async def create_website(
    website: WebsiteCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Implementation
    pass
```

#### 2.2 Resource-Based Permissions
```python
class Permission(str, Enum):
    WEBSITE_CREATE = "website:create"
    WEBSITE_READ = "website:read"
    WEBSITE_UPDATE = "website:update"
    WEBSITE_DELETE = "website:delete"
    OPPORTUNITY_REVIEW = "opportunity:review"
    ADMIN_ACCESS = "admin:access"

ROLE_PERMISSIONS = {
    UserRole.ADMIN: [Permission.ADMIN_ACCESS, Permission.WEBSITE_CREATE, ...],
    UserRole.EDITOR: [Permission.WEBSITE_CREATE, Permission.WEBSITE_UPDATE, ...],
    UserRole.REVIEWER: [Permission.OPPORTUNITY_REVIEW, Permission.WEBSITE_READ, ...],
    UserRole.VIEWER: [Permission.WEBSITE_READ, ...]
}

def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, [])
```

### Phase 3: Frontend Integration (Week 3)

#### 3.1 Auth Context
```typescript
// frontend/src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '@/lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  role: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for stored token and validate
    const token = localStorage.getItem('access_token');
    if (token) {
      validateToken(token);
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (username: string, password: string) => {
    const response = await api.post('/auth/login', 
      new URLSearchParams({ username, password }),
      { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
    );
    
    localStorage.setItem('access_token', response.access_token);
    localStorage.setItem('refresh_token', response.refresh_token);
    setUser(response.user);
  };

  const logout = async () => {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

#### 3.2 Protected Routes
```typescript
// frontend/src/components/ProtectedRoute.tsx
import { useAuth } from '@/contexts/AuthContext';
import { Navigate } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export function ProtectedRoute({ children, requiredRoles = [] }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" />;
  }

  if (requiredRoles.length > 0 && !requiredRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" />;
  }

  return <>{children}</>;
}
```

### Phase 4: Security Features (Week 4)

#### 4.1 Two-Factor Authentication (Optional)
```python
# Using pyotp for TOTP
import pyotp

class User(UserBase, table=True):
    # ... existing fields ...
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    
    def generate_totp_secret(self):
        return pyotp.random_base32()
    
    def verify_totp(self, token: str) -> bool:
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)
```

#### 4.2 Session Management
- Implement session timeout
- Single device login option
- Session invalidation on password change
- Activity tracking

#### 4.3 Security Enhancements
- Rate limiting per user
- IP whitelisting for admin users
- Email verification for new accounts
- Password reset functionality
- Account recovery process

## Migration Strategy

1. **Phase 1**: Deploy basic auth without breaking existing functionality
   - Add auth endpoints
   - Make auth optional initially
   - Test with small group

2. **Phase 2**: Gradual enforcement
   - Enable auth for write operations
   - Keep read operations open initially
   - Monitor for issues

3. **Phase 3**: Full enforcement
   - Require auth for all operations
   - Migrate existing API keys to user accounts
   - Deprecate old auth methods

## Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=<random-256-bit-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Password Policy
MIN_PASSWORD_LENGTH=8
REQUIRE_UPPERCASE=true
REQUIRE_LOWERCASE=true
REQUIRE_DIGITS=true
REQUIRE_SPECIAL_CHARS=true

# Security Settings
MAX_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30
SESSION_TIMEOUT_MINUTES=60
ENABLE_2FA=false

# Email Configuration (for verification/reset)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@hoistscraper.com
```

## Testing Strategy

1. **Unit Tests**
   - Password hashing/verification
   - Token generation/validation
   - Permission checking

2. **Integration Tests**
   - Full auth flow
   - Token refresh
   - Session management
   - Rate limiting

3. **E2E Tests**
   - Login flow
   - Protected routes
   - Role-based access
   - Session timeout

## Monitoring

1. **Metrics to Track**
   - Failed login attempts
   - Token refresh rate
   - Session duration
   - API key usage

2. **Alerts**
   - Brute force attempts
   - Unusual login patterns
   - Expired token usage
   - Permission violations

## Documentation

1. **API Documentation**
   - Auth endpoints
   - Required headers
   - Error responses
   - Rate limits

2. **User Guide**
   - How to register
   - Password requirements
   - 2FA setup
   - API key management

3. **Admin Guide**
   - User management
   - Role assignment
   - Audit log review
   - Security settings

This comprehensive authentication system will provide secure, scalable user management for HoistScraper while maintaining flexibility for future enhancements.