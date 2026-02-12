"""
GVIC Engine Authentication Module
- JWT-based custom authentication (email/password)
- Google OAuth via Emergent Auth
- Role-based access control (RBAC)
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
import httpx
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7

# Roles - 내부/외부 구분
ROLES = {
    # 내부 시스템 역할
    "super_admin": {
        "level": 4, 
        "type": "internal",
        "label": "최고관리자",
        "permissions": ["*", "system_config"]
    },
    "admin": {
        "level": 3, 
        "type": "internal",
        "label": "관리자",
        "permissions": ["*"]
    },
    "operator": {
        "level": 2, 
        "type": "internal",
        "label": "오퍼레이터",
        "permissions": ["read", "write", "process", "report"]
    },
    "visitor": {
        "level": 1, 
        "type": "internal",
        "label": "방문객",
        "permissions": ["read"]
    },
    # 외부 시스템 역할 (모두 visitor와 동일한 권한)
    "ext_admin": {
        "level": 1, 
        "type": "external",
        "label": "외부관리자",
        "permissions": ["read"]
    },
    "ext_operator": {
        "level": 1, 
        "type": "external",
        "label": "외부오퍼레이터",
        "permissions": ["read"]
    },
    "ext_visitor": {
        "level": 1, 
        "type": "external",
        "label": "외부방문객",
        "permissions": ["read"]
    }
}

# 내부 관리자 역할 목록
INTERNAL_ADMIN_ROLES = ["super_admin", "admin"]

# ==================== Models ====================

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: str
    created_at: str

class GoogleSessionRequest(BaseModel):
    session_id: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)

# ==================== Helper Functions ====================

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_jwt_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None

def create_auth_router(db):
    """Create auth router with database dependency"""
    
    router = APIRouter(prefix="/auth", tags=["Authentication"])
    
    # ==================== Auth Middleware ====================
    
    async def get_current_user(request: Request) -> dict:
        """Get current user from session token (cookie) or JWT (header)"""
        # Check cookie first
        session_token = request.cookies.get("session_token")
        
        # Check Authorization header as fallback
        if not session_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                session_token = auth_header.split(" ")[1]
        
        if not session_token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Try session token (Google OAuth)
        session = await db.user_sessions.find_one(
            {"session_token": session_token},
            {"_id": 0}
        )
        
        if session:
            # Check expiry
            expires_at = session.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Session expired")
            
            user = await db.users.find_one(
                {"user_id": session["user_id"]},
                {"_id": 0}
            )
            if user:
                return user
        
        # Try JWT token
        payload = decode_jwt_token(session_token)
        if payload:
            user = await db.users.find_one(
                {"user_id": payload["sub"]},
                {"_id": 0}
            )
            if user:
                return user
        
        raise HTTPException(status_code=401, detail="Invalid session")
    
    def require_role(allowed_roles: List[str]):
        """Dependency to check user role"""
        async def role_checker(user: dict = Depends(get_current_user)):
            user_role = user["role"]
            # super_admin과 admin은 모든 내부 권한 접근 가능
            if user_role in INTERNAL_ADMIN_ROLES:
                return user
            if user_role not in allowed_roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return user
        return role_checker
    
    # ==================== Auth Endpoints ====================
    
    @router.post("/register")
    async def register(data: UserRegister, response: Response):
        """Register new user with email/password"""
        # Check if email exists
        existing = await db.users.find_one({"email": data.email}, {"_id": 0})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": data.email,
            "name": data.name,
            "password_hash": hash_password(data.password),
            "picture": None,
            "role": "visitor",  # Default role for new users
            "auth_provider": "local",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        
        # Create JWT token
        token = create_jwt_token(user_id, data.email, "visitor")
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=JWT_EXPIRY_DAYS * 24 * 60 * 60
        )
        
        return {
            "success": True,
            "user": {
                "user_id": user_id,
                "email": data.email,
                "name": data.name,
                "role": "viewer"
            },
            "token": token
        }
    
    @router.post("/login")
    async def login(data: UserLogin, response: Response):
        """Login with email/password"""
        user = await db.users.find_one({"email": data.email}, {"_id": 0})
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check password (for local auth users)
        if user.get("auth_provider") == "local":
            if not user.get("password_hash"):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            if not verify_password(data.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
        else:
            raise HTTPException(status_code=400, detail="Please use Google login for this account")
        
        # Create JWT token
        token = create_jwt_token(user["user_id"], user["email"], user["role"])
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=JWT_EXPIRY_DAYS * 24 * 60 * 60
        )
        
        return {
            "success": True,
            "user": {
                "user_id": user["user_id"],
                "email": user["email"],
                "name": user["name"],
                "picture": user.get("picture"),
                "role": user["role"]
            },
            "token": token
        }
    
    @router.post("/google/session")
    async def google_session(data: GoogleSessionRequest, response: Response):
        """
        Exchange Google OAuth session_id for user session
        REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
        """
        # Call Emergent Auth API to get user data
        try:
            async with httpx.AsyncClient() as client:
                auth_response = await client.get(
                    "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                    headers={"X-Session-ID": data.session_id},
                    timeout=10.0
                )
                
                if auth_response.status_code != 200:
                    raise HTTPException(status_code=401, detail="Invalid session ID")
                
                auth_data = auth_response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Auth service error: {str(e)}")
        
        # Check if user exists
        user = await db.users.find_one({"email": auth_data["email"]}, {"_id": 0})
        
        if user:
            # Update existing user
            await db.users.update_one(
                {"email": auth_data["email"]},
                {"$set": {
                    "name": auth_data["name"],
                    "picture": auth_data.get("picture"),
                    "last_login": datetime.now(timezone.utc).isoformat()
                }}
            )
            user_id = user["user_id"]
            role = user["role"]
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            role = "viewer"  # Default role for new users
            
            new_user = {
                "user_id": user_id,
                "email": auth_data["email"],
                "name": auth_data["name"],
                "picture": auth_data.get("picture"),
                "role": role,
                "auth_provider": "google",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(new_user)
        
        # Store session
        session_token = auth_data.get("session_token", f"session_{uuid.uuid4().hex}")
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        })
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        return {
            "success": True,
            "user": {
                "user_id": user_id,
                "email": auth_data["email"],
                "name": auth_data["name"],
                "picture": auth_data.get("picture"),
                "role": role
            }
        }
    
    @router.get("/me")
    async def get_me(user: dict = Depends(get_current_user)):
        """Get current authenticated user"""
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "picture": user.get("picture"),
            "role": user["role"],
            "created_at": user.get("created_at")
        }
    
    @router.post("/logout")
    async def logout(request: Request, response: Response):
        """Logout user and clear session"""
        session_token = request.cookies.get("session_token")
        
        if session_token:
            # Delete session from database
            await db.user_sessions.delete_many({"session_token": session_token})
        
        # Clear cookie
        response.delete_cookie(key="session_token", path="/")
        
        return {"success": True, "message": "Logged out successfully"}
    
    @router.put("/password")
    async def change_password(data: PasswordChange, user: dict = Depends(get_current_user)):
        """Change password for local auth users"""
        if user.get("auth_provider") != "local":
            raise HTTPException(status_code=400, detail="Cannot change password for Google accounts")
        
        # Get full user with password
        full_user = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0})
        
        if not verify_password(data.current_password, full_user.get("password_hash", "")):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Update password
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"password_hash": hash_password(data.new_password)}}
        )
        
        return {"success": True, "message": "Password changed successfully"}
    
    # ==================== User Management (Admin Only) ====================
    
    @router.get("/users")
    async def list_users(user: dict = Depends(require_role(["admin"]))):
        """List all users (Admin only)"""
        users = await db.users.find(
            {},
            {"_id": 0, "password_hash": 0}
        ).to_list(1000)
        
        return {"users": users, "total": len(users)}
    
    @router.get("/users/{user_id}")
    async def get_user(user_id: str, user: dict = Depends(require_role(["admin"]))):
        """Get specific user (Admin only)"""
        target_user = await db.users.find_one(
            {"user_id": user_id},
            {"_id": 0, "password_hash": 0}
        )
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return target_user
    
    @router.put("/users/{user_id}")
    async def update_user(user_id: str, data: UserUpdate, user: dict = Depends(require_role(["admin"]))):
        """Update user role or name (Admin only)"""
        target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        update_data = {}
        if data.name:
            update_data["name"] = data.name
        if data.role:
            if data.role not in ROLES:
                raise HTTPException(status_code=400, detail=f"Invalid role. Choose from: {list(ROLES.keys())}")
            update_data["role"] = data.role
        
        if update_data:
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        
        return {"success": True, "updated": update_data}
    
    @router.delete("/users/{user_id}")
    async def delete_user(user_id: str, user: dict = Depends(require_role(["admin"]))):
        """Delete user (Admin only)"""
        if user_id == user["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot delete yourself")
        
        result = await db.users.delete_one({"user_id": user_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete user sessions
        await db.user_sessions.delete_many({"user_id": user_id})
        
        return {"success": True, "deleted_user_id": user_id}
    
    @router.get("/roles")
    async def list_roles():
        """List available roles"""
        return {"roles": ROLES}
    
    # Export dependencies for use in other routers
    router.get_current_user = get_current_user
    router.require_role = require_role
    
    return router
