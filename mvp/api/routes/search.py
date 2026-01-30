from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlmodel import Session, select
import asyncio
import json
import time
import os

from mvp.storage.database import get_session
from mvp.storage.models import StoredPhoto, SearchSession
from mvp.schema.models import PhotoProfile
from mvp.text_search.prompt_parser import PromptParser
from mvp.api.routes.collections import get_current_user_id
from datetime import datetime
from mvp.api.websocket import manager
from mvp.core.state import state
from mvp.api.schemas import SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])

class TextSearchRequest(BaseModel):
    prompt: str
    collection_id: UUID
    top_k: int = 5
    session_id: Optional[str] = None

# Initialize services
parser = PromptParser()

@router.post("/text", response_model=SearchResponse)
async def search_by_text(
    request: TextSearchRequest,
    session: Session = Depends(get_session)
):
    """
    Search for photos in a collection matching a text description.
    """
    if not state.ranker:
         from mvp.search.ranker import Ranker
         state.ranker = Ranker()
         
    ranker = state.ranker
    
    sess_id = request.session_id
    print(f"DEBUG: Received text search request: '{request.prompt[:50]}...' Session: {sess_id}", flush=True)

    if sess_id:
        await manager.send_update(sess_id, {"stage": "parsing", "progress": 0.1, "message": "Parsing prompt..."})

    # 1. Parse prompt into a target profile
    try:
        print("DEBUG: Calling parser.parse_prompt...", flush=True)
        target_profile = await parser.parse_prompt(request.prompt)
        print(f"DEBUG: Parsed profile: {target_profile}", flush=True)
        
        if sess_id:
            await manager.send_update(sess_id, {"stage": "parsing", "progress": 1.0, "status": "completed"})
    except Exception as e:
        print(f"ERROR: Prompt parsing failed: {e}", flush=True)
        import traceback
        traceback.print_exc()
        if sess_id:
            await manager.send_update(sess_id, {"stage": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=f"Failed to parse prompt: {str(e)}")
    
    # 2. Get photos from collection
    if sess_id:
        await manager.send_update(sess_id, {"stage": "fetching", "progress": 0.0, "message": "Fetching photos..."})
        
    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == request.collection_id)
    photos = session.exec(stmt).all()
    
    if not photos:
        if sess_id:
            await manager.send_update(sess_id, {"stage": "completed", "progress": 1.0, "results_count": 0})
        # Fix: Frontend expects "target_profile" and serialized Enums
        return {
            "results": [], 
            "target_profile": target_profile.model_dump(mode='json') if hasattr(target_profile, 'model_dump') else target_profile
        }
    
    if sess_id:
        await manager.send_update(sess_id, {"stage": "ranking", "progress": 0.0, "message": f"Ranking {len(photos)} photos..."})

    # 3. Prepare candidates
    candidates = []
    
    for p in photos:
        try:
            if not p.profile:
                continue
                
            prof_obj = PhotoProfile(**p.profile)
            prof_obj.id = str(p.id)
            prof_obj.image_path = p.image_path
            candidates.append(prof_obj)
        except Exception as e:
            # print(f"Skipping malformed profile {p.id}: {e}")
            continue
            
    # 4. Rank candidates against target
    scored_results = []
    total_candidates = len(candidates)
    
    start_time = time.time()
    
    for i, cand in enumerate(candidates):
        # Score similarity (0.0 - 1.0)
        score = ranker.score_candidate(target_profile, cand)
        
        # Only include relevant matches
        if score > 0.0:
            # Fix path for frontend
            raw_path = str(cand.image_path)
            # Normalize path for frontend (remove C:\, use /images/ mount)
            filename = raw_path.replace("\\", "/").split("/")[-1]
            
            # Create a copy or update? Update in place is fine for this scope
            cand.image_path = f"/images/{filename}"
            
            scored_results.append(SearchResult(profile=cand, score=score))
        
        # Report progress
        if sess_id and i % 10 == 0:
             await manager.send_update(sess_id, {"stage": "ranking", "progress": (i / total_candidates)})
            
    if sess_id:
        await manager.send_update(sess_id, {"stage": "ranking", "progress": 1.0, "status": "completed"})
    
    # 5. Sort by score descending
    scored_results.sort(key=lambda x: x.score, reverse=True)
    
    results = scored_results[:request.top_k]
    execution_time = time.time() - start_time
    
    if sess_id:
        await manager.send_update(sess_id, {"stage": "completed", "progress": 1.0, "results_count": len(results)})

    # Save History
    if sess_id:
        try:
            user_id = UUID(get_current_user_id())
            sess_uuid = UUID(sess_id)
            
            new_session = SearchSession(
                id=sess_uuid,
                user_id=user_id,
                collection_id=request.collection_id,
                positives=[request.prompt], # Store prompt as positive input source
                negatives=[],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                results=[{"id": str(r.profile.id), "score": r.score} for r in results]
            )
            session.add(new_session)
            session.commit()
        except Exception as e:
            print(f"Failed to save text search history: {e}")
    
    return SearchResponse(
        results=results,
        target_profile=target_profile,
        analyzed_positives=[],
        analyzed_negatives=[],
        execution_time=execution_time
    )

# --- Generation ---
from mvp.generators.dalle_generator import DalleGenerator
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT

class GenerateSearchRequest(BaseModel):
    prompt: str
    collection_id: UUID
    generator: str = "dalle"
    top_k: int = 5
    session_id: Optional[str] = None

@router.post("/generate", response_model=SearchResponse)
async def generate_and_search(
    request: GenerateSearchRequest,
    session: Session = Depends(get_session)
):
    """
    Generate an image from prompt, analyze it, and search for similar photos.
    """
    if not state.ranker:
         from mvp.search.ranker import Ranker
         state.ranker = Ranker()
    ranker = state.ranker
    
    sess_id = request.session_id
    
    # 1. Generate Image
    if sess_id:
        await manager.send_update(sess_id, {"stage": "generating", "progress": 0.0, "message": "Generating image..."})
        
    try:
        # TODO: Factory for generators
        if request.generator != "dalle":
            raise HTTPException(status_code=400, detail="Only 'dalle' generator is currently supported")
            
        generator = DalleGenerator()
        local_image_path = await generator.generate_image(request.prompt)
        
        # Create web-accessible path for frontend
        filename = os.path.basename(str(local_image_path))
        web_image_path = f"/temp_images/generated/{filename}"
        
        if sess_id:
            await manager.send_update(sess_id, {"stage": "generating", "progress": 1.0, "status": "completed", "image": web_image_path})
            
    except Exception as e:
        if sess_id:
             await manager.send_update(sess_id, {"stage": "error", "message": f"Generation failed: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
        
    # 2. Analyze Image (VLM)
    if sess_id:
        await manager.send_update(sess_id, {"stage": "analyzing", "progress": 0.0, "message": "Analyzing generated image..."})

    try:
        if not state.vlm_client: # Use shared client if available
             state.vlm_client = VLMClient()
        vlm_client = state.vlm_client
        
        # Run sync method in thread
        json_str = await asyncio.to_thread(vlm_client.analyze_image, str(local_image_path), SYSTEM_PROMPT)
        
        # Clean JSON
        cleaned = json_str.replace("```json", "").replace("```", "").strip()
        if "{" in cleaned and "}" in cleaned:
             start = cleaned.find("{")
             end = cleaned.rfind("}") + 1
             cleaned = cleaned[start:end]
             
        data = json.loads(cleaned)
        # Inject dummy ID/Path if missing to bypass strict validation if model didn't reload
        if "id" not in data:
            data["id"] = "temp_gen_id"
        if "image_path" not in data:
            data["image_path"] = web_image_path

        target_profile = PhotoProfile(**data)
        
        # Ensure correct path is set
        target_profile.image_path = web_image_path
        
        if sess_id:
            await manager.send_update(sess_id, {"stage": "analyzing", "progress": 1.0, "status": "completed"})
        
    except Exception as e:
        if sess_id:
             await manager.send_update(sess_id, {"stage": "error", "message": f"Analysis failed: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

    # 3. Search
    if sess_id:
        await manager.send_update(sess_id, {"stage": "ranking", "progress": 0.0, "message": "Searching database..."})

    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == request.collection_id)
    photos = session.exec(stmt).all()
    
    start_time = time.time()
    
    candidates = []
    for p in photos:
        try:
            if not p.profile: continue
            prof_obj = PhotoProfile(**p.profile)
            prof_obj.id = str(p.id)
            prof_obj.image_path = p.image_path
            candidates.append(prof_obj)
        except: continue
        
    scored_results = []
    total_candidates = len(candidates)
    
    for i, cand in enumerate(candidates):
        score = ranker.score_candidate(target_profile, cand)
        if score > 0.0:
            # Normalize path for frontend
            raw_path = str(cand.image_path)
            filename = raw_path.replace("\\", "/").split("/")[-1]
            cand.image_path = f"/images/{filename}"
            
            scored_results.append(SearchResult(profile=cand, score=score))
        if sess_id and i % 10 == 0:
             await manager.send_update(sess_id, {"stage": "ranking", "progress": (i / total_candidates)})
            
    scored_results.sort(key=lambda x: x.score, reverse=True)
    
    results = scored_results[:request.top_k]
    execution_time = time.time() - start_time

    if sess_id:
        await manager.send_update(sess_id, {"stage": "completed", "progress": 1.0, "results_count": len(results)})

    # Save History
    if sess_id:
        try:
            user_id = UUID(get_current_user_id())
            sess_uuid = UUID(sess_id)
            
            # For generation, we might want to store the prompt AND the generated image path?
            # Schema says positives matches JSON list of strings.
            new_session = SearchSession(
                id=sess_uuid,
                user_id=user_id,
                collection_id=request.collection_id,
                positives=[request.prompt, web_image_path], 
                negatives=[],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                results=[{"id": str(r.profile.id), "score": r.score} for r in results]
            )
            session.add(new_session)
            session.commit()
        except Exception as e:
            print(f"Failed to save generate search history: {e}")

    return SearchResponse(
        results=results,
        target_profile=target_profile,
        analyzed_positives=[],
        analyzed_negatives=[],
        generated_image=web_image_path,
        execution_time=execution_time
    )
