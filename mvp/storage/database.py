import os
from sqlmodel import SQLModel, create_engine, Session
# Import models to ensure they are registered with SQLModel.metadata
from .models import User, PhotoCollection, StoredPhoto, SearchSession 

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///data/{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
