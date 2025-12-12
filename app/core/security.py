"""
Core security utilities for authentication and authorization.
"""
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# Alias for backward compatibility
hash_password = get_password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add unique identifier to ensure token uniqueness even within same second
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_otp() -> str:
    """
    Generate a random OTP code.
    
    Returns:
        OTP code as string
    """
    return ''.join([str(secrets.randbelow(10)) for _ in range(settings.OTP_LENGTH)])


def hash_otp(otp: str) -> str:
    """
    Hash an OTP for secure storage.
    
    Args:
        otp: OTP code to hash
        
    Returns:
        Hashed OTP
    """
    return get_password_hash(otp)


def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """
    Verify an OTP against its hash.
    
    Args:
        plain_otp: Plain OTP code
        hashed_otp: Hashed OTP from storage
        
    Returns:
        True if OTP matches, False otherwise
    """
    return verify_password(plain_otp, hashed_otp)


def generate_token_hash(token: str) -> str:
    """
    Generate a hash of a token for storage.
    Uses SHA256 instead of bcrypt because tokens can be >72 bytes.
    
    Args:
        token: Token to hash
        
    Returns:
        Hashed token (hex string)
    """
    import hashlib
    return hashlib.sha256(token.encode('utf-8')).hexdigest()
