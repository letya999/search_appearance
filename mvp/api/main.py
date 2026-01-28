import os
import json
import asyncio
from typing import List, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mvp.schema.models import PhotoProfile
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker
from mvp.search.ranker import Ranker
from mvp.core.embedder import ImageEmbedder

from mvp.storage.database import create_db_and_tables
from mvp.api.routes.collections import router as collections_router

# Configuration
DATA_DIR = Path("data")
METADATA_FILE = DATA_DIR / "wiki_1000_metadata.json"
IMAGES_DIR = DATA_DIR / "raw_1000"

# Global State
class AppState:
    db_profiles: List[PhotoProfile] = []
    vlm_client: Optional[VLMClient] = None
    ranker: Ranker = Ranker()
    aggregator: ProfileAggregator = ProfileAggregator()
    embedder: Optional[ImageEmbedder] = None
    # Store session/active embeddings to prevent duplicates.
    # List of (id, embedding)
    session_embeddings: List[tuple] = []

state = AppState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load DB and Init Client
    print("Initializing Database...")
    create_db_and_tables()
    
    print("Loading database...")
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            raw_data = json.load(f)
            # Create PhotoProfile objects
            # Handle potential partial data failures gently
            valid_profiles = []
            for item in raw_data:
                try:
                    # Fix image path to be served via URL if needed, 
                    # but for now we keep absolute path for internal use, usually.
                    # Actually, for the UI to show it, we need a filename we can serve.
                    # Let's ensure 'image_path' is preserved or we extract filename.
                    p = PhotoProfile(**item)
                    valid_profiles.append(p)
                except Exception as e:
                    print(f"Skipping profile {item.get('id', '?')}: {e}")
            
            state.db_profiles = valid_profiles
            print(f"Loaded {len(state.db_profiles)} profiles.")
    else:
        print("WARNING: Metadata file not found. Database is empty.")

    # Init VLM Client
    try:
        state.vlm_client = VLMClient()
        print("VLM Client initialized.")
    except Exception as e:
        print(f"WARNING: VLM Client failed to init: {e}")

    # Init Embedder
    try:
        state.embedder = ImageEmbedder()
        print("Image Embedder initialized.")
    except Exception as e:
        print(f"WARNING: Embedder failed to init: {e}")

    yield
    # Shutdown
    pass

app = FastAPI(lifespan=lifespan)
from mvp.api.routes.search import router as search_router

app.include_router(collections_router, prefix="/api")
app.include_router(search_router, prefix="/api")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files for Images
# Mount /images -> data/raw_1000
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Mount /temp_images -> data (for uploads)
if DATA_DIR.exists():
    app.mount("/temp_images", StaticFiles(directory=DATA_DIR), name="temp_images")

# --- Schemas ---

import time

class SearchResult(BaseModel):
    profile: PhotoProfile
    score: float
    # We might want to add explanation text here later
    
class SearchResponse(BaseModel):
    results: List[SearchResult]
    analyzed_positives: List[PhotoProfile]
    analyzed_negatives: List[PhotoProfile]
    target_profile: PhotoProfile
    execution_time: Optional[float] = None

# --- Endpoints ---

@app.get("/health")
def health():
    return {"status": "ok", "db_size": len(state.db_profiles)}

async def analyze_upload(file: UploadFile) -> PhotoProfile:
    # Save temp file
    # Ensure filename is safe
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"])
    temp_path = DATA_DIR / f"temp_{safe_filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    try:
        # 1. Calculate Embedding & Check Duplicates (Fast/Cheap)
        embedding: Optional[List[float]] = None
        if state.embedder:
            embedding = state.embedder.encode_image(str(temp_path))
            
            if embedding:
                for existing_id, existing_emb in state.session_embeddings:
                    sim = state.embedder.cosine_similarity(embedding, existing_emb)
                    if sim > 0.9:
                        print(f"Duplicate detected: {file.filename} is similar to {existing_id} ({sim:.4f})")
                        raise HTTPException(status_code=400, detail=f"Duplicate image detected (similarity: {sim:.2f}). Please upload unique photos.")

        # 2. VLM Analysis (Slow/Expensive)
        print(f"Analyzing {file.filename}...", flush=True)
        json_str = state.vlm_client.analyze_image(str(temp_path), SYSTEM_PROMPT)
        
        # Clean
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(json_str)
        
        # Add ID/Path
        data["id"] = f"upload_{safe_filename}"
        
        filename = temp_path.name
        data["image_path"] = f"/temp_images/{filename}"
        data["embedding"] = embedding
        
        # Add to session (for this run)
        if embedding:
            state.session_embeddings.append((data["id"], embedding))
        
        print(f"DEBUG: Analyzed {file.filename} -> image_path set to: {data['image_path']}", flush=True)
        
        return PhotoProfile(**data)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis failed for {file.filename}: {e}", flush=True)
        # In a real app we might return an error or a dummy profile
        raise HTTPException(status_code=500, detail=f"VLM Analysis Failed: {e}")
    finally:
        # Cleanup temp? Maybe keep for debugging for now.
        pass

@app.post("/api/search", response_model=SearchResponse)
async def search(
    positives: List[UploadFile] = File(...),
    negatives: List[UploadFile] = File(default=[])
):
    # Clear session embeddings at start of search to allow "fresh" check
    # Or keep them? User said "uploading identical photos". Maybe per request?
    # Usually duplicates matter within the request.
    state.session_embeddings = [] 
    
    if not state.vlm_client:
        raise HTTPException(status_code=503, detail="VLM Client not available")
        
    # 1. Analyze Uploads (Concurrently)
    # Note: OpenAI client is sync by default unless we use AsyncOpenAI.
    # The wrapper VLMClient uses sync OpenAI. Running in threadpool via asyncio.to_thread?
    # For now, let's run sequential or simple loop to avoid complexity, 
    # as we only have 10 max images.
    
    start_time = time.time()

    analyzed_pos = []
    for f in positives:
        # Rewind file if needed? UploadFile is workable.
        p = await analyze_upload(f)
        analyzed_pos.append(p)
        
    analyzed_neg = []
    for f in negatives:
        if f.size > 0: # Check if empty file passed
             p = await analyze_upload(f)
             analyzed_neg.append(p)
             
    # 2. Build Target
    target = state.aggregator.build_target_profile(analyzed_pos, analyzed_neg)
    
    # 3. Score Database
    scored_results = []
    # No need to aggregated negatives again as target is already adjusted
    
    for candidate in state.db_profiles:
        score = state.ranker.score_candidate(target, candidate)
        scored_results.append((candidate, score))
        
    # 4. Sort and Cull
    scored_results.sort(key=lambda x: x[1], reverse=True)
    top_5 = scored_results[:5]
    
    # Format results
    # We need to ensure the profile image_path is converted to a serve-able URL
    formatted_results = []
    for prof, score in top_5:
        # Create a copy to not mutate DB state
        p_copy = prof.model_copy()
        
        # FIX: Handle Windows paths on Linux (Docker)
        # 10049200...jpg or C:\...\10049200...jpg
        raw_path = str(p_copy.image_path)
        filename = raw_path.replace("\\", "/").split("/")[-1]
        
        # Debugging
        print(f"DEBUG: Processing path '{raw_path}' -> filename '{filename}'", flush=True)
        
        # Set to URL
        p_copy.image_path = f"/images/{filename}"
        formatted_results.append(SearchResult(profile=p_copy, score=score))
        
    execution_time = time.time() - start_time

    return SearchResponse(
        results=formatted_results,
        analyzed_positives=analyzed_pos,
        analyzed_negatives=analyzed_neg,
        target_profile=target,
        execution_time=execution_time
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mvp.api.main:app", host="0.0.0.0", port=8000, reload=True)
