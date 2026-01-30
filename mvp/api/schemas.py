from typing import List, Optional
from pydantic import BaseModel
from mvp.schema.models import PhotoProfile

class SearchResult(BaseModel):
    profile: PhotoProfile
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    analyzed_positives: List[PhotoProfile]
    analyzed_negatives: List[PhotoProfile]
    target_profile: Optional[PhotoProfile] = None
    generated_image: Optional[str] = None
    execution_time: Optional[float] = None
