import sys
import os
from fastapi.routing import APIRoute

# Add project root to path
sys.path.append(os.getcwd())

try:
    from mvp.api.main import app
    print("Successfully imported app.")
    
    print("Routes:")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"{route.methods} {route.path}")
            
except Exception as e:
    print(f"Error loading app: {e}")
    import traceback
    traceback.print_exc()
