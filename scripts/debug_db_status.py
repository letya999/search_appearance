import os
import sys
from sqlmodel import Session, select, create_engine
from mvp.storage.models import PhotoCollection, StoredPhoto

# Ensure we can import modules from current directory
sys.path.append(os.getcwd())

def check_db():
    db_path = "data/database.db"
    if not os.path.exists(db_path):
        print(f"ERROR: Database file not found at {db_path}")
        return

    sqlite_url = f"sqlite:///{db_path}"
    engine = create_engine(sqlite_url)

    print(f"--- Database Status Core: {db_path} ---")
    
    with Session(engine) as session:
        # Check Collections
        collections = session.exec(select(PhotoCollection)).all()
        print(f"Collections Found: {len(collections)}")
        
        if not collections:
            print("WARNING: No collections found!")
        
        for col in collections:
            count = session.exec(select(StoredPhoto).where(StoredPhoto.collection_id == col.id)).all()
            print(f" - ID: {col.id}")
            print(f"   Name: {col.name}")
            print(f"   Photo Count: {len(count)}")
            
            # Print sample photo
            if count:
                 sample = count[0]
                 print(f"   Sample Photo[0]: ID={sample.id}, Path={sample.image_path}")
                 if sample.profile:
                     print(f"   Has Profile Data: Yes (Keys: {sample.profile.keys() if isinstance(sample.profile, dict) else 'Not Dict'})")
                 else:
                     print(f"   Has Profile Data: NO")

        # Total Photos
        total = session.exec(select(StoredPhoto)).all()
        print(f"Total Photos in DB: {len(total)}")

if __name__ == "__main__":
    check_db()
