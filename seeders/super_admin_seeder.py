"""
Super Admin Seeder - Creates the default super admin user.
"""
from sqlmodel import select
from seeders.base import BaseSeeder
from app.models.user import User, Admin
from app.models.role import Role
from app.constants.enums import UserType
from app.core.security import get_password_hash
from app.core.config import settings


class SuperAdminSeeder(BaseSeeder):
    """Seed the default super admin user."""
    
    order = 30  # After roles
    
    async def should_run(self) -> bool:
        """Check if super admin needs to be created."""
        result = await self.session.execute(
            select(Admin).where(Admin.is_super_admin == True)
        )
        return result.first() is None
    
    async def run(self) -> None:
        """Create the super admin user."""
        # Get SUPER_ADMIN role
        result = await self.session.execute(
            select(Role).where(Role.name == "SUPER_ADMIN")
        )
        role = result.scalar_one_or_none()
        
        if not role:
            print("  ❌ SUPER_ADMIN role not found. Run RolesSeeder first.")
            return
        
        # Check if user with this email exists
        email = getattr(settings, 'SUPER_ADMIN_EMAIL', 'admin@example.com')
        password = getattr(settings, 'SUPER_ADMIN_PASSWORD', 'Admin@123')
        
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        if result.first():
            print(f"  ⚠️  User with email {email} already exists")
            return
        
        # Create user
        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            user_type=UserType.ADMIN,
            is_active=True,
            is_verified=True
        )
        self.session.add(user)
        await self.session.flush()
        
        # Create admin profile
        admin = Admin(
            user_id=user.id,
            username="superadmin",
            role_id=role.id,
            is_super_admin=True
        )
        self.session.add(admin)
        await self.session.commit()
        
        print(f"  ✅ Created super admin: {email}")
