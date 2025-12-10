
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.openapi.utils import get_openapi
from app.main import app

def debug_openapi():
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    
    paths = openapi_schema.get("paths", {})
    print("Available paths:")
    for path in paths.keys():
        print(f" - {path}")
        
    # Check /auth/oauth/callback request body
    callback_path = next((p for p in paths if "callback" in p), None)
    if callback_path:
        print(f"\nRequest Body for {callback_path}:")
        request_body = paths[callback_path].get("post", {}).get("requestBody", {})
        print(json.dumps(request_body, indent=2))

if __name__ == "__main__":
    debug_openapi()
