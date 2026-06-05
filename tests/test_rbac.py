import sys
import os
import pytest
from datetime import timedelta
from jose import jwt

# Add root path to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.rbac import create_access_token, get_current_user, JWT_SECRET, JWT_ALGORITHM
from fastapi import HTTPException

def test_create_and_verify_token():
    """
    Verifies that a token can be encoded and decoded correctly,
    returning matching RBAC claims.
    """
    token_payload = {
        "sub": "test_user",
        "department": "Engineering",
        "clearance_level": 2
    }
    
    token = create_access_token(data=token_payload)
    assert isinstance(token, str)
    
    decoded = get_current_user(token)
    assert decoded["username"] == "test_user"
    assert decoded["department"] == "Engineering"
    assert decoded["clearance_level"] == 2

def test_missing_claims_token():
    """
    Ensures tokens lacking crucial RBAC attributes raise authorization errors.
    """
    payload = {
        "sub": "invalid_user"
        # missing department and clearance
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token)
    assert exc_info.value.status_code == 401

def test_expired_token():
    """
    Ensures expired JWT tokens are rejected.
    """
    token_payload = {
        "sub": "old_user",
        "department": "Sales",
        "clearance_level": 1
    }
    # Create token that expired 10 minutes ago
    expired_token = create_access_token(data=token_payload, expires_delta=timedelta(minutes=-10))
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(expired_token)
    assert exc_info.value.status_code == 401

def test_tampered_token():
    """
    Ensures tokens signed with invalid keys are rejected.
    """
    token_payload = {
        "sub": "attacker",
        "department": "HR",
        "clearance_level": 3
    }
    tampered_token = jwt.encode(token_payload, "wrongsecretkey", algorithm=JWT_ALGORITHM)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(tampered_token)
    assert exc_info.value.status_code == 401
