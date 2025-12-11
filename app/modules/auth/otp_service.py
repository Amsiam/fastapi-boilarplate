"""
OTP service for email verification and password reset.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.core.security import generate_otp, hash_otp, verify_otp
from app.core.cache import (
    get_cache,
    set_cache,
    delete_cache,
    increment_cache,
    otp_key,
    rate_limit_key
)
from app.core.exceptions import ValidationError, RateLimitError
from app.core.schemas.response import ErrorCode
from app.constants.enums import OTPType
from app.core.email import EmailService


class OTPService:
    """Service for OTP generation and verification."""
    
    @staticmethod
    async def generate_otp(email: str, otp_type: OTPType) -> str:
        """
        Generate and store OTP for email verification or password reset.
        
        Args:
            email: User email
            otp_type: Type of OTP (EMAIL_VERIFICATION or PASSWORD_RESET)
            
        Returns:
            Generated OTP code
            
        Raises:
            RateLimitError: If cooldown period is active or account is locked
        """
        # Check cooldown
        cooldown_key = f"otp_cooldown:{email}:{otp_type.value}"
        if await get_cache(cooldown_key):
            raise RateLimitError(
                error_code=ErrorCode.OTP_COOLDOWN,
                message=f"Please wait {settings.OTP_RESEND_COOLDOWN_SECONDS} seconds before requesting another OTP",
                retry_after=settings.OTP_RESEND_COOLDOWN_SECONDS
            )
        
        # Check lockout (5 requests in 1 hour = 24 hour lockout)
        lockout_key = rate_limit_key(email, f"otp_generation:{otp_type.value}")
        attempts = await get_cache(lockout_key) or 0
        
        if attempts >= 5:
            raise RateLimitError(
                error_code=ErrorCode.OTP_LOCKED,
                message="Too many OTP requests. Account locked for 24 hours.",
                retry_after=86400  # 24 hours
            )
        
        # Generate OTP
        otp_code = generate_otp()
        otp_hash = hash_otp(otp_code)
        
        # Store in Redis with expiry
        cache_key = otp_key(email, otp_type.value)
        otp_data = {
            "hash": otp_hash,
            "attempts": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await set_cache(
            cache_key,
            otp_data,
            expire=settings.OTP_EXPIRE_MINUTES * 60
        )
        
        # Set cooldown
        await set_cache(
            cooldown_key,
            "1",  # Redis needs string, not boolean
            expire=settings.OTP_RESEND_COOLDOWN_SECONDS
        )
        
        # Send OTP via email
        purpose_map = {
            OTPType.EMAIL_VERIFICATION: "email verification",
            OTPType.PASSWORD_RESET: "password reset"
        }
        purpose = purpose_map.get(otp_type, "verification")
        
        await EmailService.send_otp_email(email, otp_code, purpose)
        
        # Increment generation attempts (1 hour expiry)
        await increment_cache(lockout_key, 1)
        from app.core.cache import get_redis_client
        client = get_redis_client()
        await client.expire(lockout_key, 3600)  # 1 hour
        
        return otp_code
    
    @staticmethod
    async def verify_otp(email: str, otp_code: str, otp_type: OTPType) -> bool:
        """
        Verify OTP code.
        
        Args:
            email: User email
            otp_code: OTP code to verify
            otp_type: Type of OTP
            
        Returns:
            True if OTP is valid
            
        Raises:
            ValidationError: If OTP is invalid, expired, or max attempts exceeded
        """
        cache_key = otp_key(email, otp_type.value)
        otp_data = await get_cache(cache_key)
        
        if not otp_data:
            raise ValidationError(
                error_code=ErrorCode.OTP_EXPIRED,
                message="OTP has expired or does not exist",
                field="otp_code"
            )
        
        # Check attempts
        if otp_data["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            await delete_cache(cache_key)
            raise ValidationError(
                error_code=ErrorCode.OTP_MAX_ATTEMPTS,
                message="Maximum OTP verification attempts exceeded",
                field="otp_code"
            )
        
        # Verify OTP
        is_valid = verify_otp(otp_code, otp_data["hash"])
        
        if not is_valid:
            # Increment attempts
            otp_data["attempts"] += 1
            await set_cache(
                cache_key,
                otp_data,
                expire=settings.OTP_EXPIRE_MINUTES * 60
            )
            
            remaining = settings.OTP_MAX_ATTEMPTS - otp_data["attempts"]
            raise ValidationError(
                error_code=ErrorCode.OTP_INVALID,
                message=f"Invalid OTP. {remaining} attempts remaining.",
                field="otp_code"
            )
        
        # Valid OTP - delete it (single use)
        await delete_cache(cache_key)
        return True
    
    @staticmethod
    async def clear_otp(email: str, otp_type: OTPType) -> None:
        """
        Clear OTP from cache.
        
        Args:
            email: User email
            otp_type: Type of OTP
        """
        cache_key = otp_key(email, otp_type.value)
        await delete_cache(cache_key)
