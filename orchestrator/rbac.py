import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkeyforzerotrustragpipelinethatshouldbelong")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Generates a JWT access token containing security claims.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str) -> dict:
    """
    Decodes the JWT token and extracts user permissions (department, clearance_level).
    Raises HTTPException (401 Unauthorized) if token validation fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        department: str = payload.get("department")
        clearance_level: int = payload.get("clearance_level")
        
        if username is None or department is None or clearance_level is None:
            raise credentials_exception
            
        return {
            "username": username,
            "department": department,
            "clearance_level": clearance_level
        }
    except JWTError:
        raise credentials_exception
