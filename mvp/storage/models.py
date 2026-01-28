from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON

# User model
class User(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(index=True, unique=True)
    api_keys: Dict[str, str] = Field(default={}, sa_column=Column(JSON))
    
    collections: List["PhotoCollection"] = Relationship(back_populates="user")
    sessions: List["SearchSession"] = Relationship(back_populates="user")

# Photo Collection model
class PhotoCollection(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    name: str
    description: Optional[str] = None
    photo_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional[User] = Relationship(back_populates="collections")
    photos: List["StoredPhoto"] = Relationship(back_populates="collection")

# Stored Photo model
class StoredPhoto(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    collection_id: UUID = Field(foreign_key="photocollection.id")
    image_path: str
    profile: Dict[str, Any] = Field(default={}, sa_column=Column(JSON))  # Serialized PhotoProfile
    embedding: Optional[bytes] = None  # Serialized numpy array
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    collection: Optional[PhotoCollection] = Relationship(back_populates="photos")

# Search Session model
class SearchSession(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id")
    collection_id: UUID = Field(foreign_key="photocollection.id")
    positives: List[str] = Field(default=[], sa_column=Column(JSON))  # List of UUID strings
    negatives: List[str] = Field(default=[], sa_column=Column(JSON))  # List of UUID strings
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    results: List[Dict[str, Any]] = Field(default=[], sa_column=Column(JSON)) # Serialized results
    
    user: Optional[User] = Relationship(back_populates="sessions")
