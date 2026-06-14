from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError

SECRET_KEY = "enterprise-secret"
ALGORITHM = "HS256"

# Role mapping configuration
ROLE_CLEARANCE_MAP = {
    "HR_Director": 3,
    "Engineering_Lead": 3,
    "Marketing_Manager": 2,
    "Marketing_Intern": 1,
    "Finance_Analyst": 2
}

ROLE_DEPARTMENT_MAP = {
    "HR_Director": "HR",
    "Engineering_Lead": "Engineering",
    "Marketing_Manager": "Marketing",
    "Marketing_Intern": "Marketing",
    "Finance_Analyst": "Finance"
}

class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude common system/utility paths
        if request.url.path in ["/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"}
            )
            
        token = auth_header.split(" ")[1]
        try:
            # Decode JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            role = payload.get("role")
            department = payload.get("department")
            
            if not role or not department:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token payload: missing role or department"}
                )
                
            if role not in ROLE_CLEARANCE_MAP:
                return JSONResponse(
                    status_code=401,
                    content={"detail": f"Unauthorized role: {role}"}
                )
                
            # Map role to clearance level dynamically as per requirements
            clearance_level = ROLE_CLEARANCE_MAP[role]
            
            # Attach rbac_context to request.state
            request.state.rbac_context = {
                "department": department,
                "clearance_level": clearance_level
            }
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"}
            )
            
        return await call_next(request)

def generate_mock_token(role: str) -> str:
    """
    Generates a valid mock JWT token for a given role with its associated department and clearance level.
    """
    dep = ROLE_DEPARTMENT_MAP.get(role, "Engineering")
    clearance = ROLE_CLEARANCE_MAP.get(role, 1)
    
    payload = {
        "role": role,
        "department": dep,
        "clearance_level": clearance
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
