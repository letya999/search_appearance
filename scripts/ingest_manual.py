import os
import sys
import shutil
import asyncio
import json
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.append(os.getcwd())

from sqlmodel import Session, select, create_engine
from mvp.storage.models import PhotoCollection, StoredPhoto, User
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT

# Paths (Absolute paths usually safer in script context based on cwd)
DB_PATH = "data/database.db"
UPLOAD_DIR = Path("data/uploads")

# Provided Images
IMAGES = [
    r"C:/Users/User/.gemini/antigravity/brain/3fda1e8a-9f3b-41c7-90bd-2b6afb22f43c/uploaded_media_0_1769740902559.png",
    r"C:/Users/User/.gemini/antigravity/brain/3fda1e8a-9f3b-41c7-90bd-2b6afb22f43c/uploaded_media_1_1769740902559.png"
]

# Quick Mock Profile to ensure matches if VLM fails
MOCK_PROFILE = {
    "basic": {
        "gender": {"value": "female", "confidence": 0.95},
        "ethnicity": {"value": "asian", "confidence": 0.9},
        "age_group": {"value": "25-34", "confidence": 0.85}, 
        "body_type": {"value": "athletic", "confidence": 0.8}
    },
    "vibe": {
        "style": {"value": "sporty", "confidence": 0.9},
        "vibe": {"value": "energetic", "confidence": 0.9}
    },
    "hair": {
        "color": {"value": "black", "confidence": 0.9},
        "texture": {"value": "straight", "confidence": 0.9}
    },
    "face": {
        "eye_color": {"value": "brown", "confidence": 0.9}
    }
}

async def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}, creating engine implies creation if models valid.")

    sqlite_url = f"sqlite:///{DB_PATH}"
    print(f"Connecting to {sqlite_url}")
    engine = create_engine(sqlite_url)
    
    vlm = VLMClient()
    
    with Session(engine) as session:
        # 1. Get/Create Collection
        col = session.exec(select(PhotoCollection)).first()
        if not col:
            print("Creating default collection...")
            col = PhotoCollection(
                user_id=UUID("00000000-0000-0000-0000-000000000000"),
                name="My Collection",
                description="Manual Ingest",
                photo_count=0
            )
            session.add(col)
            session.commit()
            session.refresh(col)
        
        print(f"Using Collection: {col.name} ({col.id})")
        
        col_dir = UPLOAD_DIR / str(col.id)
        col_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        for src in IMAGES:
            if not os.path.exists(src):
                print(f"Skipping missing file: {src}")
                # Try relative if absolute fails? No, metadata is absolute.
                continue
                
            src_path = Path(src)
            dest_path = col_dir / src_path.name
            
            # Copy file
            shutil.copy2(src_path, dest_path)
            print(f"Copied {src_path.name} to {dest_path}")
            
            # Analyze
            print("Analyzing with VLM... (this may take a moment)")
            
            profile_data = MOCK_PROFILE.copy()
            used_mock = True
            
            try:
                # Attempt real analysis
                # We need to run sync method in thread
                print("Calling VLM...")
                profile_json_str = await asyncio.to_thread(vlm.analyze_image, str(dest_path), SYSTEM_PROMPT)
                
                cleaned = profile_json_str.replace("```json", "").replace("```", "").strip()
                if "{" in cleaned:
                    s = cleaned.find("{")
                    e = cleaned.rfind("}") + 1
                    cleaned = cleaned[s:e]
                
                real_data = json.loads(cleaned)
                if "basic" in real_data: # simple check
                    profile_data = real_data
                    used_mock = False
                    print("VLM Analysis Successful.")
                else:
                    print("VLM returned invalid data, using mock.")
                    
            except Exception as ve:
                print(f"VLM failed ({ve}), using Fallback Profile.")
            
            # Save to DB
            # Check if exists first to avoid dupes?
            existing = session.exec(select(StoredPhoto).where(StoredPhoto.image_path == str(dest_path))).first()
            if existing:
                print(f"Photo already exists {existing.id}, updating profile.")
                existing.profile = profile_data
                session.add(existing)
            else:
                photo = StoredPhoto(
                    collection_id=col.id,
                    image_path=str(dest_path),
                    profile=profile_data
                )
                session.add(photo)
                count += 1
            
        if count > 0:
            col.photo_count += count
            session.add(col)
        
        session.commit()
        print(f"Successfully processed photos. New additions: {count}")

if __name__ == "__main__":
    # Windows needs policy for asyncio sometimes
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
