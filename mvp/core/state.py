from typing import List, Optional, Any
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
    face_verifier: Any = None # FaceVerifier instance
    ready: bool = False  # Track if API is fully initialized
    # Store session/active embeddings to prevent duplicates.
    # List of (id, embedding)
    session_embeddings: List[tuple] = []
    # Store blacklist embeddings to prevent searching for specific people
    blacklist_embeddings: List[List[float]] = []

# Global state instance
state = AppState()
