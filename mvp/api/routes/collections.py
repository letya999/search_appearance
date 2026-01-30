from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ...storage.database import get_session
from ...storage.models import PhotoCollection, StoredPhoto, User as UserModel

router = APIRouter(prefix="/collections", tags=["collections"])

# Helper to get default user for MVP (single user mode if needed)
# In real app, this comes from auth
def get_current_user_id():
    # Placeholder UUID for development
    return "00000000-0000-0000-0000-000000000000" 

@router.post("", response_model=PhotoCollection)
def create_collection(collection: PhotoCollection, session: Session = Depends(get_session)):
    # Verify user exists or create default if not
    user_id = collection.user_id
    
    # Ensure user_id is a UUID object (SQLModel sometimes leaves it as string)
    if isinstance(user_id, str):
        user_id = UUID(user_id)
        collection.user_id = user_id # Update the object too

    user = session.get(UserModel, user_id)
    if not user:
        # Create default user if it's the specific placeholder ID
        if str(user_id) == get_current_user_id():
             user = UserModel(id=UUID(get_current_user_id()), email="default@example.com")
             session.add(user)
             session.commit()
             session.refresh(user)
        else:
             raise HTTPException(status_code=404, detail="User not found")

    session.add(collection)
    session.commit()
    session.refresh(collection)
    return collection

@router.get("", response_model=List[PhotoCollection])
def list_collections(user_id: UUID = None, session: Session = Depends(get_session)):
    if not user_id:
        user_id = UUID(get_current_user_id())
    statement = select(PhotoCollection).where(PhotoCollection.user_id == user_id)
    results = session.exec(statement).all()
    return results

@router.post("/{collection_id}/photos", response_model=StoredPhoto)
def add_photo(collection_id: UUID, photo: StoredPhoto, session: Session = Depends(get_session)):
    collection = session.get(PhotoCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    photo.collection_id = collection_id
    session.add(photo)
    
    collection.photo_count += 1
    session.add(collection)
    
    session.commit()
    session.refresh(photo)
    return photo

@router.get("/{collection_id}/stats")
def get_collection_stats(collection_id: UUID, session: Session = Depends(get_session)):
    collection = session.get(PhotoCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"id": collection.id, "photo_count": collection.photo_count, "name": collection.name}

@router.delete("/{collection_id}")
def delete_collection(collection_id: UUID, session: Session = Depends(get_session)):
    collection = session.get(PhotoCollection, collection_id)
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    session.delete(collection)
    session.commit()
    return {"ok": True}
