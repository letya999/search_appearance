from typing import List, Optional
from mvp.schema.models import PhotoProfile
from mvp.annotator.client import VLMClient
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker
from mvp.core.embedder import ImageEmbedder

class AppState:
    db_profiles: List[PhotoProfile] = []
    vlm_client: Optional[VLMClient] = None
    ranker: Optional[Ranker] = None
    aggregator: Optional[ProfileAggregator] = None
    embedder: Optional[ImageEmbedder] = None
    ready: bool = False  # Track if API is fully initialized
    # Store session/active embeddings to prevent duplicates.
    # List of (id, embedding)
    session_embeddings: List[tuple] = []

# Global state instance
state = AppState()
