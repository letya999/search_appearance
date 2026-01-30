
import sys
import os
import time
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.append(os.getcwd())

from mvp.api.main import app

def verify_history():
    print("Initialize TestClient...")
    with TestClient(app) as client:
        print("1. Checking API Health...")
        health = client.get("/api/health")
        print(f"Health: {health.json()}")
        
        # Ensure 'user_id' logic works (using default mock user from backend)
        # Fetch collections to get a valid collection_id
        print("2. Fetching Collections...")
        cols_resp = client.get("/api/collections")
        if cols_resp.status_code != 200:
            print(f"Failed to fetch collections: {cols_resp.text}")
            return
            
        cols = cols_resp.json()
        collection_id = None
        
        if not cols:
            print("No collections found, creating default...")
            new_col = client.post("/api/collections", json={
                "user_id": "00000000-0000-0000-0000-000000000000",
                "name": "Test Collection",
                "description": "For Verification"
            })
            collection_id = new_col.json()["id"]
        else:
            collection_id = cols[0]["id"]
            
        print(f"Using Collection ID: {collection_id}")
        
        # Get current history count
        print("3. Checking Initial History...")
        hist_before = client.get("/api/user/history").json()
        count_before = len(hist_before)
        print(f"History items before: {count_before}")
        
        # Perform Text Search
        import uuid
        session_id = str(uuid.uuid4())
        print(f"4. Performing Text Search with Session ID: {session_id}")
        search_payload = {
            "prompt": "Test Search Verification",
            "collection_id": collection_id,
            "session_id": session_id,
            "top_k": 1
        }
        res = client.post("/api/search/text", json=search_payload)
        
        if res.status_code != 200:
            print(f"Search failed: {res.text}")
            # If search fails (e.g. no ranker or parser), check if we can mock or if it should work.
            # The backend initializes ranker/parser on startup or first request.
            # If it fails, we can't verify history saving.
            return
            
        print("Search successful.")
        
        # Check History again
        print("5. Verifying History Update...")
        hist_after = client.get("/api/user/history").json()
        count_after = len(hist_after)
        print(f"History items after: {count_after}")
        
        if count_after > count_before:
            print("SUCCESS: History count increased!")
            latest = hist_after[0]
            print(f"Latest History Item: ID={latest['id']}, Positives={latest.get('positives')}")
        else:
            print("FAILURE: History count did not increase.")

if __name__ == "__main__":
    verify_history()
