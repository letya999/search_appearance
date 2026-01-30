import os
import sys
import json
import shutil
from pathlib import Path
from uuid import UUID

# Add project root to path
sys.path.append(os.getcwd())

from sqlmodel import Session, select, create_engine
from mvp.storage.models import PhotoCollection, StoredPhoto, User
from mvp.core.hasher import ImageHasher

# Params
METADATA_PATH = "data/wiki_1000_metadata.json"
RAW_DIR = Path("data/raw_1000")
DB_PATH = "data/database.db"

def main():
    if not os.path.exists(METADATA_PATH):
        print(f"Metadata not found at {METADATA_PATH}")
        return

    print(f"Loading metadata from {METADATA_PATH}...")
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Found {len(data)} entries.")
    
    sqlite_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(sqlite_url)
    
    with Session(engine) as session:
        # Get/Create Collection
        col = session.exec(select(PhotoCollection).where(PhotoCollection.name == "Wiki 1000")).first()
        if not col:
            print("Creating 'Wiki 1000' collection...")
            col = PhotoCollection(
                user_id=UUID("00000000-0000-0000-0000-000000000000"),
                name="Wiki 1000",
                description="Imported from wiki_1000_metadata.json",
                photo_count=0
            )
            session.add(col)
            session.commit()
            session.refresh(col)
            
        print(f"Target Collection: {col.name} ({col.id})")
        
        # Prepare upload dir for this collection (conceptually, though we might leave in place or copy)
        # To avoid duplication, let's copy to data/uploads/{col_id} as per app standard
        col_dir = Path(f"data/uploads/{col.id}")
        col_dir.mkdir(parents=True, exist_ok=True)
        
        count = 0
        skipped = 0
        
        for entry in data:
            # 1. Resolve File
            json_path = entry.get("image_path", "")
            filename = os.path.basename(json_path)
            
            # Try finding the file in RAW_DIR
            local_path = RAW_DIR / filename
            
            if not local_path.exists():
                # Fallback: try using the absolute path from JSON if valid
                if os.path.exists(json_path):
                     local_path = Path(json_path)
                else:
                     # print(f"Missing file: {filename}")
                     skipped += 1
                     continue
            
            # 2. Copy to collection folder (renaming not needed usually, but good practice for unique IDs)
            # Check if already exists in DB by hash or name
            # Calculate hash?
            
            dest_path = col_dir / filename
            
            if not dest_path.exists():
                shutil.copy2(local_path, dest_path)
            
            # 3. Create DB Entry
            # Check existance by path
            existing = session.exec(select(StoredPhoto).where(StoredPhoto.image_path == str(dest_path))).first()
            
            if existing:
                # Update profile
                profile_data = {
                    "basic": entry.get("basic"),
                    "face": entry.get("face"),
                    "hair": entry.get("hair"),
                    "extra": entry.get("extra"),
                    "vibe": entry.get("vibe")
                }
                existing.profile = profile_data
                session.add(existing)
            else:
                profile_data = {
                    "basic": entry.get("basic"),
                    "face": entry.get("face"),
                    "hair": entry.get("hair"),
                    "extra": entry.get("extra"),
                    "vibe": entry.get("vibe")
                }
                
                photo = StoredPhoto(
                    collection_id=col.id,
                    image_path=str(dest_path),
                    profile=profile_data
                )
                session.add(photo)
                count += 1
                
            if count % 100 == 0:
                print(f"Processed {count}...")
                session.commit() # Commit batch
        
        # Update Stats
        col.photo_count += count
        session.add(col)
        session.commit()
        
        print(f"Done. Imported {count} new photos. Skipped {skipped} missing files.")

if __name__ == "__main__":
    main()
