import asyncio
import sys
import httpx
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
API_URL = "http://localhost:8000/api/v1"
EMAIL = "admin@example.com"
PASSWORD = "Admin@123456"

async def verify_superuser():
    async with httpx.AsyncClient() as client:
        print(f"🔄 Attempting login for {EMAIL}...")
        
        # 1. Login
        try:
            response = await client.post(
                f"{API_URL}/auth/login",
                json={
                    "username": EMAIL,
                    "password": PASSWORD
                }
            )
            
            if response.status_code != 200:
                print(f"❌ Login failed: {response.text}")
                return False
                
            data = response.json()
            token = data["data"]["access_token"]
            print("✅ Login successful!")
            
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return False

        # 2. Verify /auth/me
        print("\n🔄 Verifying /auth/me...")
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(f"{API_URL}/auth/me", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to get user info: {response.text}")
            return False
            
        user_data = response.json()["data"]
        print(f"✅ User info retrieved: {user_data['email']} (Role: {user_data['role']})")
        if 'role_name' in user_data:
            print(f"   - RBAC Role: {user_data['role_name']}")
        if 'permissions' in user_data:
            print(f"   - Permissions: {len(user_data['permissions'])} permissions")
            print(f"     {user_data['permissions']}")
        
        # 3. Verify Admin Access (RBAC)
        print("\n🔄 Verifying Admin Access (GET /admin/roles)...")
        response = await client.get(f"{API_URL}/admin/roles", headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Failed to access admin endpoint: {response.text}")
            return False
            
        roles = response.json()["data"]
        print(f"✅ Admin access confirmed! Found {len(roles)} roles.")
        for role in roles:
            print(f"   - {role['name']}: {role.get('permission_count', 0)} permissions")
            
        print("\n" + "="*50)
        print("🎉 SUPERUSER VERIFICATION SUCCESSFUL!")
        print("="*50)
        return True

if __name__ == "__main__":
    asyncio.run(verify_superuser())
