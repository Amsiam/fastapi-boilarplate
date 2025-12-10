"""
Create a superuser (admin with SUPER_ADMIN role).

This script creates a default superuser account for initial system access.
You can customize the credentials via environment variables or prompts.
"""
import asyncio
import sys
from pathlib import Path
from getpass import getpass

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import async_session_maker
from app.core.security import hash_password
from app.models.user import User, Admin
from app.models.role import Role
from app.constants.enums import UserRole


async def create_superuser(
    email: str,
    username: str,
    password: str,
    full_name: str,
    phone: str = None
):
    """
    Create a superuser with SUPER_ADMIN role.
    
    Args:
        email: Admin email
        username: Admin username
        password: Admin password
        full_name: Admin full name
        phone: Admin phone (optional)
    """
    async with async_session_maker() as session:
        # Check if user already exists
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            print(f"❌ User with email {email} already exists!")
            return False
            
        # Check if username already exists
        result = await session.execute(
            select(Admin).where(Admin.username == username)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"❌ Admin with username {username} already exists!")
            return False
        
        # Get SUPER_ADMIN role
        result = await session.execute(
            select(Role).where(Role.name == "SUPER_ADMIN")
        )
        super_admin_role = result.scalar_one_or_none()
        
        if not super_admin_role:
            print("❌ SUPER_ADMIN role not found! Run seed_data.py first.")
            return False
        
        # Create User
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            phone=phone,
            role=UserRole.ADMIN,
            is_verified=True  # Auto-verify superuser
        )
        session.add(user)
        await session.flush()  # Get user ID
        
        # Create Admin with SUPER_ADMIN role
        admin = Admin(
            user_id=user.id,
            username=username,
            role_id=super_admin_role.id,
            permission_overrides={}  # No overrides needed for superuser
        )
        session.add(admin)
        
        await session.commit()
        
        print("\n" + "="*60)
        print("✅ Superuser created successfully!")
        print("="*60)
        print(f"Email: {email}")
        print(f"Username: {username}")
        print(f"Name: {full_name}")
        print(f"Role: SUPER_ADMIN")
        print(f"Verified: Yes")
        print("="*60)
        print("\nYou can now login with these credentials.")
        print("="*60 + "\n")
        
        return True


async def main():
    """Main function with interactive prompts."""
    import os
    
    print("\n" + "="*60)
    print("🔐 SUPERUSER CREATION")
    print("="*60 + "\n")
    
    # Get credentials from environment or prompt
    email = os.getenv("SUPERUSER_EMAIL")
    username = os.getenv("SUPERUSER_USERNAME")
    password = os.getenv("SUPERUSER_PASSWORD")
    full_name = os.getenv("SUPERUSER_NAME")
    phone = os.getenv("SUPERUSER_PHONE")
    
    # Interactive prompts if not provided
    if not email:
        email = input("Email: ").strip()
        if not email:
            print("❌ Email is required!")
            sys.exit(1)
            
    if not username:
        default_username = email.split("@")[0]
        username = input(f"Username [{default_username}]: ").strip() or default_username
    
    if not password:
        password = getpass("Password: ")
        password_confirm = getpass("Confirm Password: ")
        
        if password != password_confirm:
            print("❌ Passwords don't match!")
            sys.exit(1)
        
        if len(password) < 8:
            print("❌ Password must be at least 8 characters!")
            sys.exit(1)
    
    if not full_name:
        full_name = input("Full Name: ").strip()
        if not full_name:
            print("❌ Full name is required!")
            sys.exit(1)
    
    if phone is None:
        phone = input("Phone (optional, press Enter to skip): ").strip() or None
    
    # Create superuser
    try:
        success = await create_superuser(
            email=email,
            username=username,
            password=password,
            full_name=full_name,
            phone=phone
        )
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error creating superuser: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
