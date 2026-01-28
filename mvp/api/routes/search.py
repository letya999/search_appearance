from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from sqlmodel import Session, select

from mvp.storage.database import get_session
from mvp.storage.models import StoredPhoto
from mvp.schema.models import PhotoProfile
from mvp.text_search.prompt_parser import PromptParser
from mvp.search.ranker import Ranker

router = APIRouter(prefix="/search", tags=["search"])

class TextSearchRequest(BaseModel):
    prompt: str
    collection_id: UUID
    top_k: int = 20

# Initialize services
parser = PromptParser()
ranker = Ranker()

@router.post("/text")
async def search_by_text(
    request: TextSearchRequest,
    session: Session = Depends(get_session)
):
    """
    Search for photos in a collection matching a text description.
    """
    # 1. Parse prompt into a target profile
    try:
        target_profile = await parser.parse_prompt(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse prompt: {str(e)}")
    
    # 2. Get photos from collection
    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == request.collection_id)
    photos = session.exec(stmt).all()
    
    if not photos:
        return {"results": [], "parsed_profile": target_profile}
        
    # 3. Prepare candidates
    candidates = []
    
    for p in photos:
        try:
            # profile is stored as dict JSON column
            if not p.profile:
                continue
                
            prof_obj = PhotoProfile(**p.profile)
            # Ensure ID matches for reference if needed
            prof_obj.id = str(p.id)
            prof_obj.image_path = p.image_path
            candidates.append(prof_obj)
        except Exception as e:
            print(f"Skipping malformed profile {p.id}: {e}")
            continue
            
    # 4. Rank candidates against target
    scored_results = []
    for cand in candidates:
        # Score similarity (0.0 - 1.0)
        score = ranker.score_candidate(target_profile, cand)
        
        # Only include relevant matches
        if score > 0.0:
            scored_results.append({
                "photo_id": str(cand.id),
                "score": score,
                "image_path": cand.image_path,
                "profile": cand.dict()
            })
            
    
    # 5. Sort by score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "results": scored_results[:request.top_k],
        "parsed_profile": target_profile
    }

# --- Generation ---
from mvp.generators.dalle_generator import DalleGenerator
from mvp.annotator.client import VLMClient
from mvp.annotator.prompts import SYSTEM_PROMPT
import asyncio
import json

class GenerateSearchRequest(BaseModel):
    prompt: str
    collection_id: UUID
    generator: str = "dalle"
    top_k: int = 20

@router.post("/generate")
async def generate_and_search(
    request: GenerateSearchRequest,
    session: Session = Depends(get_session)
):
    """
    Generate an image from prompt, analyze it, and search for similar photos.
    """
    # 1. Generate Image
    try:
        # TODO: Factory for generators
        if request.generator != "dalle":
            raise HTTPException(status_code=400, detail="Only 'dalle' generator is currently supported")
            
        generator = DalleGenerator()
        image_path = await generator.generate_image(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")
        
    # 2. Analyze Image (VLM)
    try:
        vlm_client = VLMClient()
        # Run sync method in thread
        json_str = await asyncio.to_thread(vlm_client.analyze_image, image_path, SYSTEM_PROMPT)
        
        # Clean JSON
        cleaned = json_str.replace("```json", "").replace("```", "").strip()
        if "{" in cleaned and "}" in cleaned:
             start = cleaned.find("{")
             end = cleaned.rfind("}") + 1
             cleaned = cleaned[start:end]
             
        data = json.loads(cleaned)
        target_profile = PhotoProfile(**data)
        
        # We need to serve this generated image. 
        # API should probably map it to a static URL if it's in data/generated
        # Assuming DalleGenerator saves to data/generated
        
        # Convert path to accessible URL (relative to API root for serving)
        # e.g. /images/generated/filename.png
        # For now, just pass the absolute path, knowing UI might need help
        target_profile.image_path = image_path
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

    # 3. Search
    # Reuse logic? We can just copy paste for now to avoid large refactor risks in one step
    stmt = select(StoredPhoto).where(StoredPhoto.collection_id == request.collection_id)
    photos = session.exec(stmt).all()
    
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
    for cand in candidates:
        score = ranker.score_candidate(target_profile, cand)
        if score > 0.0:
            scored_results.append({
                "photo_id": str(cand.id),
                "score": score,
                "image_path": cand.image_path,
                "profile": cand.dict()
            })
            
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "results": scored_results[:request.top_k],
        "generated_image": image_path,
        "parsed_profile": target_profile
    }
