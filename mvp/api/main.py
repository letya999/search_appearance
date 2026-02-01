import os
# Disable progress bars for cleaner logs
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TQDM_DISABLE"] = "1"

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("accelerate").setLevel(logging.ERROR)

import json
import asyncio
from typing import List, Optional
from pathlib import Path
from contextlib import asynccontextmanager


from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import datetime

from mvp.schema.models import PhotoProfile
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker
from mvp.core.embedder import ImageEmbedder
from mvp.core.face_recognition import FaceVerifier

from mvp.storage.database import create_db_and_tables
from mvp.api.routes.collections import router as collections_router
from mvp.core.state import state

# Configuration
DATA_DIR = Path("data")
METADATA_FILE = DATA_DIR / "wiki_1000_metadata.json"
BLACKLIST_FILE = DATA_DIR / "blacklist_embeddings.json"
IMAGES_DIR = DATA_DIR / "raw_1000"

async def init_models():
    """Background initialization of heavy models."""
    print("Background Init: Starting heavy model loading...", flush=True)
    loop = asyncio.get_running_loop()

    # Init Embedder with warmup
    try:
        print("Initializing Image Embedder (loading CLIP model)...")
        # Run in thread executor to avoid blocking loop
        state.embedder = await loop.run_in_executor(None, ImageEmbedder)
        
        # Warmup
        print("Warming up CLIP model...")
        import tempfile
        import numpy as np
        from PIL import Image
        
        dummy_img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            dummy_img.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            await loop.run_in_executor(None, state.embedder.encode_image, tmp_path)
        finally:
             if os.path.exists(tmp_path):
                 os.unlink(tmp_path)
        
        print("Image Embedder initialized and warmed up.")
    except Exception as e:
        print(f"WARNING: Embedder failed to init: {e}")
        
    # Init Face Verifier
    try:
        print("Initializing Face Verifier...")
        state.face_verifier = await loop.run_in_executor(None, FaceVerifier)
        
        if not state.face_verifier.disabled:
             await loop.run_in_executor(None, state.face_verifier.warmup)
        print("Face Verifier initialized.")
    except Exception as e:
        print(f"WARNING: Face Verifier failed to init: {e}")
        
    # Init Ranker
    try:
        state.ranker = Ranker()
        print("Ranker initialized.")
    except Exception as e:
        print(f"WARNING: Ranker failed to init: {e}")

    # Init Aggregator
    try:
        state.aggregator = ProfileAggregator()
        print("ProfileAggregator initialized.")
    except Exception as e:
        print(f"WARNING: Aggregator failed to init: {e}")

    # Mark as ready
    state.ready = True
    print("✓ Background initialization complete. API is fully ready!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50, flush=True)
    print("   SEARCH APPEARANCE API STARTING (UPDATED)", flush=True)
    print("="*50 + "\n", flush=True)

    # Startup: Load DB and Init Client
    print("Initializing Database...")
    create_db_and_tables()
    
    # Imports for DB seeding
    from sqlmodel import Session, select
    from mvp.storage.database import engine, get_session
    from mvp.storage.models import PhotoCollection, StoredPhoto, SearchSession
    from uuid import UUID
    
    print("Loading database...")
    valid_profiles = []
    
    # Load Blacklist
    if BLACKLIST_FILE.exists():
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                state.blacklist_embeddings = json.load(f)
            print(f"Loaded {len(state.blacklist_embeddings)} blacklisted embeddings.")
        except Exception as e:
            print(f"Failed to load blacklist: {e}")
    else:
        print("No blacklist file found.")
    
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
            # 1. Load into Memory (for Image Search)
            for item in raw_data:
                try:
                    p = PhotoProfile(**item)
                    valid_profiles.append(p)
                except Exception as e:
                    print(f"Skipping profile {item.get('id', '?')}: {e}")
            
            state.db_profiles = valid_profiles
            print(f"Loaded {len(state.db_profiles)} profiles into memory.")
            
            # 2. Sync to SQL DB (for Text Search)
            with Session(engine) as session:
                photo_count = session.exec(select(StoredPhoto)).all()
                if len(photo_count) == 0:
                    print("SQL Database is empty. Seeding from metadata...")
                    
                    # Create Collection
                    col = PhotoCollection(
                        user_id=UUID("00000000-0000-0000-0000-000000000000"),
                        name="Wiki 1000",
                        description="Auto-imported from metadata",
                        photo_count=0
                    )
                    session.add(col)
                    session.commit()
                    session.refresh(col)
                    
                    count = 0
                    for item in raw_data:
                        # Construct StoredPhoto
                        # fix path sep
                        img_path = item.get("image_path", "").replace("\\", "/")
                        
                        # Only add if file exists? Or just trust metadata? 
                        # User wants fallback "simply take from folder".
                        # Let's trust metadata path but ensure filename is correct relative to our /images mount?
                        # Actually text search route reads p.image_path.
                        # Frontend expects /images/filename.
                        # If we store absolute path, frontend gets absolute path which it can't load.
                        # We should probably normalize existing profiles too if we can.
                        # But for SQL, let's store absolute path as that's what backend uses to open file.
                        
                        # Fix UUID/ID
                        try:
                            # PhotoProfile might have 'id' as string, StoredPhoto uses uuid?
                             # StoredPhoto model: id is UUID.
                            p_id = item.get("id")
                            if not p_id: continue
                            
                            # Prepare profile dict (excluding id/image_path)
                            profile_dict = {
                                "basic": item.get("basic"),
                                "face": item.get("face"),
                                "hair": item.get("hair"),
                                "extra": item.get("extra"),
                                "vibe": item.get("vibe")
                            }
                            
                            photo = StoredPhoto(
                                id=UUID(p_id),
                                collection_id=col.id,
                                image_path=img_path,
                                profile=profile_dict
                            )
                            session.add(photo)
                            count += 1
                        except Exception as e:
                            print(f"Failed to seed photo {item.get('id')}: {e}")
                            
                    col.photo_count = count
                    session.add(col)
                    session.commit()
                    print(f"Seeded {count} photos into SQL Database.")
                else:
                    print(f"SQL Database has {len(photo_count)} photos. Skipping seed.")

    else:
        print("WARNING: Metadata file not found. Database is empty.")

    # Init VLM Client
    try:
        state.vlm_client = VLMClient()
        print("VLM Client initialized.")
    except Exception as e:
        print(f"WARNING: VLM Client failed to init: {e}")

    # Start Heavy Init in Background
    asyncio.create_task(init_models())


    # API is accessible, but heavy models are loading
    print("✓ API started. Heavy models initializing in background...")

    yield
    # Shutdown
    state.ready = False


app = FastAPI(lifespan=lifespan)
from mvp.api.routes.search import router as search_router
from mvp.api.websocket import router as ws_router

from mvp.api.routes.history import router as history_router
from mvp.api.routes.batch import router as batch_router
from mvp.api.routes.validate import router as validate_router

app.include_router(collections_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(ws_router)
app.include_router(history_router, prefix="/api")
app.include_router(batch_router, prefix="/api")
app.include_router(validate_router, prefix="/api")

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

# --- Schemas ---

import time
from datetime import datetime
from sqlmodel import Session, select
from fastapi import Depends
from mvp.storage.database import get_session
from mvp.storage.models import SearchSession, PhotoCollection
from mvp.api.routes.collections import get_current_user_id
from mvp.api.schemas import SearchResponse, SearchResult

# --- Endpoints ---

@app.get("/api/health")
def health():
    return {
        "status": "ok" if state.ready else "initializing",
        "ready": state.ready,
        "db_size": len(state.db_profiles)
    }

async def analyze_upload(file: UploadFile, session_embeddings: List, session_face_embeddings: List = []) -> PhotoProfile:
    """
    Process a single upload: save, embed, check duplicates (CLIP + Face), analyze (VLM).
    """
    # Ensure filename is safe
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"])
    temp_path = DATA_DIR / f"temp_{safe_filename}"
    
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
        print(f"DEBUG: START PROCESSING {file.filename} (Size: {len(content)} bytes)", flush=True)
        
    try:
        # 1. Calculate Embedding & Check Duplicates (Fast/Cheap)
        embedding: Optional[List[float]] = None
        if state.embedder:
            embedding = state.embedder.encode_image(str(temp_path))
            
            if embedding:
                # Check Blacklist
                if state.blacklist_embeddings:
                     for bl_emb in state.blacklist_embeddings:
                         sim = state.embedder.cosine_similarity(embedding, bl_emb)
                         if sim > 0.85: # Strong strict check for blocked people
                             print(f"Blocked person detected: {file.filename} (similarity: {sim:.4f})")
                             raise HTTPException(status_code=400, detail="This photo contains a restricted individual and cannot be used.")

                # Check Session Duplicates
                print(f"DEBUG: Checking {file.filename} against {len(session_embeddings)} existing session items.", flush=True)
                for existing_id, existing_emb in session_embeddings:
                    sim = state.embedder.cosine_similarity(embedding, existing_emb)
                    print(f"DEBUG: Sim({file.filename}, {existing_id}) = {sim}", flush=True)
                    if sim > 0.85: # Strengthened from 0.9 to 0.85 for stricter duplicate/same-person check
                        print(f"Duplicate/Same person detected: {file.filename} is similar to {existing_id} (similarity: {sim:.4f})")
                        raise HTTPException(status_code=400, detail=f"Duplicate or same person detected (similarity: {sim:.2f}). Please upload unique photos of different people/angles.")

        # 1b. Check Face Identity (Strict same-person check)
        face_embedding: Optional[List[float]] = None
        if state.face_verifier and not state.face_verifier.disabled:
             print(f"DEBUG: Checking face identity for {file.filename}...", flush=True)
             face_embedding = state.face_verifier.get_face_embedding(str(temp_path))
             
             if face_embedding is not None:
                 print(f"DEBUG: Face detected in {file.filename}. Checking against {len(session_face_embeddings)} faces.", flush=True)
                 for existing_id, existing_face_emb in session_face_embeddings:
                     is_match, dist = state.face_verifier.is_match(face_embedding, existing_face_emb, threshold=0.6)
                     print(f"DEBUG: FaceDist({file.filename}, {existing_id}) = {dist:.4f}", flush=True)
                     
                     if is_match:
                          print(f"Duplicate Face detected: {file.filename} matches {existing_id} (dist: {dist:.4f})")
                          raise HTTPException(status_code=400, detail=f"Same person detected (Face Match). Please upload photos of different people.")
             else:
                 print(f"DEBUG: No face detected in {file.filename} (or detection failed).", flush=True)

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
            session_embeddings.append((data["id"], embedding))
        
        if face_embedding is not None:
             session_face_embeddings.append((data["id"], face_embedding))
        
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
    negatives: List[UploadFile] = File(default=[]),
    session_id: Optional[str] = Form(None),
    db_session: Session = Depends(get_session)
):
    from mvp.api.websocket import manager
    
    # Load VLM Client
    if not state.vlm_client:
        if session_id:
             await manager.send_update(session_id, {"stage": "error", "message": "VLM Client not available"})
        raise HTTPException(status_code=503, detail="VLM Client not available")

    local_session_embeddings = [] 
    local_face_embeddings = []
    
    if session_id:
        await manager.send_update(session_id, {"stage": "analyzing", "progress": 0.05, "message": f"Analyzing {len(positives) + len(negatives)} images..."})

    # 1. Analyze Uploads (Concurrently)
    # Note: OpenAI client is sync by default unless we use AsyncOpenAI.
    # The wrapper VLMClient uses sync OpenAI. Running in threadpool via asyncio.to_thread?
    # For now, let's run sequential or simple loop to avoid complexity, 
    # as we only have 10 max images.
    
    start_time = time.time()
    total_files = len(positives) + len(negatives)
    processed_count = 0

    analyzed_pos = []
    for f in positives:
        try:
             # Rewind file if needed? UploadFile is workable.
             p = await analyze_upload(f, local_session_embeddings, local_face_embeddings)
             analyzed_pos.append(p)
        except HTTPException: # Explicitly catch and re-raise validation errors
             raise
        except Exception as e:
             print(f"Error analyzing {f.filename}: {e}")
        
        processed_count += 1
        if session_id:
             await manager.send_update(session_id, {"stage": "analyzing", "progress": 0.05 + (0.8 * (processed_count / total_files)), "message": f"Analyzed {processed_count}/{total_files}..."})

    analyzed_neg = []
    for f in negatives:
        if f.size > 0: # Check if empty file passed
             try:
                 p = await analyze_upload(f, local_session_embeddings, local_face_embeddings)
                 analyzed_neg.append(p)
             except HTTPException: # Explicitly catch and re-raise validation errors
                 raise
             except Exception as e:
                 print(f"Error analyzing {f.filename}: {e}")
             
             processed_count += 1
             if session_id:
                 await manager.send_update(session_id, {"stage": "analyzing", "progress": 0.05 + (0.8 * (processed_count / total_files))})

    if session_id:
        await manager.send_update(session_id, {"stage": "analyzing", "progress": 1.0, "status": "completed"})
        await manager.send_update(session_id, {"stage": "ranking", "progress": 0.0, "message": "Ranking profiles..."})

    # 2. Build Target
    if not state.aggregator:
         state.aggregator = ProfileAggregator()
    target = state.aggregator.build_target_profile(analyzed_pos, analyzed_neg)
    
    # 3. Score Database
    scored_results = []
    # No need to aggregated negatives again as target is already adjusted
    
    if not state.ranker:
         # Fallback
         state.ranker = Ranker()
    
    candidate_count = len(state.db_profiles)
    for i, candidate in enumerate(state.db_profiles):
        score = state.ranker.score_candidate(target, candidate)
        scored_results.append((candidate, score))
        
        if session_id and i % 50 == 0 and candidate_count > 0:
             await manager.send_update(session_id, {"stage": "ranking", "progress": (i / candidate_count)})
        
    if session_id:
        await manager.send_update(session_id, {"stage": "ranking", "progress": 1.0, "status": "completed"})

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
    
    if session_id:
        await manager.send_update(session_id, {"stage": "completed", "progress": 1.0, "results_count": len(formatted_results)})

    # NEW: Save History
    try:
        user_id = UUID(get_current_user_id())
        
        # Determine collection (default to first one)
        col = db_session.exec(select(PhotoCollection).where(PhotoCollection.user_id == user_id)).first()
        
        if col and session_id:
             # Ensure session ID is valid UUID
             try:
                 sess_uuid = UUID(session_id)
                 
                 # Check if exists (should not, but safe check)
                 existing = db_session.get(SearchSession, sess_uuid)
                 if not existing:
                     new_session = SearchSession(
                         id=sess_uuid,
                         user_id=user_id,
                         collection_id=col.id,
                         positives=[p.filename for p in positives],
                         negatives=[n.filename for n in negatives],
                         started_at=datetime.utcnow(), # Approximate start
                         completed_at=datetime.utcnow(),
                         results=[{"id": str(r.profile.id), "score": r.score} for r in formatted_results]
                     )
                     db_session.add(new_session)
                     db_session.commit()
             except ValueError:
                 print(f"Invalid session ID format: {session_id}")
    except Exception as e:
        print(f"Failed to save history: {e}")

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
