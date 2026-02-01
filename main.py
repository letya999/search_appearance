import uvicorn
import os

if __name__ == "__main__":
    # Ensure raw_1000 exists or create data folder if missing
    os.makedirs("data", exist_ok=True)
    
    print("Starting Search Appearance API...")
    uvicorn.run("mvp.api.main:app", host="0.0.0.0", port=8000, reload=True)
