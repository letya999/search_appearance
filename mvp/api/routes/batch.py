import zipfile
import shutil
import os
import csv
import io
import json
from pathlib import Path
from typing import List
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException, Response
from sqlmodel import Session, select
from mvp.storage.database import get_session
from mvp.storage.models import StoredPhoto, PhotoCollection

from mvp.core.hasher import ImageHasher

router = APIRouter(prefix="/collections", tags=["batch"])

@router.post("/{collection_id}/upload_archive")
async def upload_archive(
    collection_id: UUID, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    session: Session = Depends(get_session)
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")
        
    # Save zip temporarily
    temp_zip = Path(f"data/temp_{file.filename}")
    with open(temp_zip, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    # Extract to a temp folder
    extract_dir = Path(f"data/extract_{file.filename}")
    extract_dir.mkdir(exist_ok=True, parents=True)
    
    try:
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Find images
        image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        image_files = []
        for root, dirs, files in os.walk(extract_dir):
            for f in files:
                if Path(f).suffix.lower() in image_extensions:
                    image_files.append(Path(root) / f)
        
        count = 0
        dest_dir = Path(f"data/uploads/{collection_id}")
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        for img_path in image_files:
            # Compute Hash for deduplication
            phash = ImageHasher.compute_phash(str(img_path))
            
            if phash:
                existing = session.exec(select(StoredPhoto).where(StoredPhoto.collection_id == collection_id).where(StoredPhoto.phash == phash)).first()
                if existing:
                    print(f"Skipping duplicate: {img_path.name}")
                    continue

            # Move to persistent storage
            # Ensure unique filename
            dest_path = dest_dir / img_path.name
            if dest_path.exists():
                stem = dest_path.stem
                suffix = dest_path.suffix
                dest_path = dest_dir / f"{stem}_{count}{suffix}"

            shutil.move(str(img_path), str(dest_path))
            
            # Create DB entry
            photo = StoredPhoto(
                collection_id=collection_id,
                image_path=str(dest_path),
                profile={}, # Empty profile, needs analysis later
                phash=phash
            )
            session.add(photo)
            count += 1

            
        # Update collection count
        collection = session.get(PhotoCollection, collection_id)
        if collection:
            collection.photo_count += count
            session.add(collection)
            
        session.commit()
        
        return {"processed": count, "message": "Photos uploaded. Analysis required."}
        
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid zip file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    finally:
        # Cleanup
        if temp_zip.exists():
            os.remove(temp_zip)
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

@router.get("/{collection_id}/export/json")
def export_json(collection_id: UUID, session: Session = Depends(get_session)):
    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == collection_id)
    photos = session.exec(stmt).all()
    
    data = [p.dict() for p in photos]
    return data

@router.get("/{collection_id}/export/csv")
def export_csv(collection_id: UUID, session: Session = Depends(get_session)):
    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == collection_id)
    photos = session.exec(stmt).all()
    
    if not photos:
        return Response(content="", media_type="text/csv")
        
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(["id", "image_path", "created_at", "profile"])
    
    for p in photos:
        writer.writerow([str(p.id), p.image_path, str(p.created_at), json.dumps(p.profile)])
        
    return Response(content=output.getvalue(), media_type="text/csv")
