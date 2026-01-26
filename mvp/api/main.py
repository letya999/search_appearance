from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import shutil
import os
import uuid
from mvp.storage.db import PhotoDatabase
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker
from mvp.annotator.client import VLMClient
from mvp.annotator.batch_process import process_file
from mvp.schema.models import PhotoProfile

app = FastAPI(title="Visual Dating Search API")

# Initialize components
# Ensure data directory exists
os.makedirs("data/uploads", exist_ok=True)
db = PhotoDatabase(db_path="data/db.json")

# We defer VLM client init to when needed or keep global if it's lightweight (it is)
try:
    vlm_client = VLMClient()
except Exception as e:
    print(f"Warning: VLM Client not initialized (Env var missing?): {e}")
    vlm_client = None

aggregator = ProfileAggregator()
ranker = Ranker()

class SearchRequest(BaseModel):
    positive_ids: List[str]
    negative_ids: List[str] = []
    limit: int = 20
    weights: Dict[str, float] = None
    hard_filters: Dict[str, Any] = None

class SearchResponseItem(BaseModel):
    id: str
    score: float
    image_path: str
    attributes: Dict[str, Any] # Simplified attributes for frontend

@app.post("/index-photo", response_model=PhotoProfile)
async def index_photo(file: UploadFile = File(...)):
    if not vlm_client:
        raise HTTPException(status_code=503, detail="VLM Client not available")

    # Save temp file
    file_ext = os.path.splitext(file.filename)[1]
    temp_filename = f"{uuid.uuid4()}{file_ext}"
    temp_path = os.path.join("data/uploads", temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Analyze
        # process_file expects client and path
        # It returns a dict compatible with PhotoProfile
        # It also generates a UUID for ID. We might want to use our temp_filename as a base or just use the one generated.
        
        # Note: process_file logic:
        # profile_data = { "id": str(uuid.uuid4()), "image_path": absolute_path, ... }
        
        # We want to ensure image_path is accessible.
        abs_path = os.path.abspath(temp_path)
        
        # We essentially re-implement process_file wrapper to ensure we control the path storage if needed,
        # but calling it is fine.
        profile_dict = process_file(vlm_client, abs_path)
        
        # Ensure ID is unique or track it.
        profile = PhotoProfile(**profile_dict)
        
        # Save to DB
        db.add_profile(profile)
        
        return profile

    except Exception as e:
        # Cleanup if failed
        if os.path.exists(temp_path):
            # os.remove(temp_path) # Maybe keep for debugging?
            pass
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResponseItem])
async def search_profiles(req: SearchRequest):
    all_profiles = db.get_all_profiles()
    
    positives = [db.get_profile(pid) for pid in req.positive_ids if db.get_profile(pid)]
    negatives = [db.get_profile(nid) for nid in req.negative_ids if db.get_profile(nid)]
    
    if not positives:
         # If no positives, maybe return random or top rated? 
         # For now error.
         raise HTTPException(status_code=400, detail="At least one valid positive ID is required")

    target_profile = aggregator.build_target_profile(positives, negatives)
    
    negative_target_profile = None
    if negatives:
        negative_target_profile = aggregator.build_target_profile(negatives, [])
    
    # Apply hard filters if any
    candidates = all_profiles
    if req.hard_filters:
        candidates = ranker.filter_candidates(candidates, req.hard_filters)
        
    # Score
    scored_results = []
    for cand in candidates:
        if cand.id in req.positive_ids or cand.id in req.negative_ids:
            continue
            
        score = ranker.score_candidate(target_profile, cand, weights=req.weights, negative_target=negative_target_profile)
        scored_results.append((cand, score))
        
    # Sort
    scored_results.sort(key=lambda x: x[1], reverse=True)
    top_results = scored_results[:req.limit]
    
    # Format response
    response = []
    for p, s in top_results:
        response.append(SearchResponseItem(
            id=p.id,
            score=s,
            image_path=p.image_path,
            attributes=p.model_dump()
        ))
        
    return response

@app.get("/profiles", response_model=List[PhotoProfile])
async def list_profiles(limit: int = 100):
    profiles = db.get_all_profiles()
    return profiles[:limit]
