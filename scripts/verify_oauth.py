"""
Verify OAuth endpoints and configuration.
"""
import asyncio
import sys
from pathlib import Path
import httpx

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

BASE_URL = "http://localhost:8000" + settings.API_V1_STR

async def verify_oauth():
    """Verify OAuth endpoints."""
    print("🔍 Verifying OAuth Integration...\n")
    
    async with httpx.AsyncClient() as client:
        # 1. List Providers
        print("1️⃣  Testing GET /auth/oauth/providers...")
        response = await client.get(f"{BASE_URL}/auth/oauth/providers")
        
        if response.status_code == 200:
            data = response.json()["data"]
            print(f"✅ Success! Found {len(data)} providers:")
            for p in data:
                print(f"   - {p['display_name']} ({p['name']}) -> {p['login_url']}")
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(response.text)
            return

        # 2. Get Login URL
        print("\n2️⃣  Testing GET /auth/oauth/login/google...")
        response = await client.get(f"{BASE_URL}/auth/oauth/login/google", params={"redirect_uri": "http://localhost:3000/callback"})
        
        if response.status_code == 200:
            url = response.json()["data"]["url"]
            print(f"✅ Success! Generated URL:")
            print(f"   {url}")
            
            # Verify URL params
            if "client_id" in url and "redirect_uri" in url and "state" in url:
                print("   - URL contains required parameters")
            else:
                print("   ❌ URL missing parameters")
        else:
            print(f"❌ Failed! Status: {response.status_code}")
            print(response.text)

    print("\n==================================================")
    print("🎉 OAUTH VERIFICATION COMPLETED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(verify_oauth())
