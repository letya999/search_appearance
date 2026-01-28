import logging
from typing import List, Optional, Union
from PIL import Image
try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

logger = logging.getLogger(__name__)

class ImageEmbedder:
    def __init__(self, model_name: str = "clip-ViT-B-32"):
        self.model_name = model_name
        self.model = None
        if SentenceTransformer:
            try:
                logger.info(f"Loading embedding model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                logger.info("Embedding model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load embedding model {model_name}: {e}")
        else:
            logger.warning("sentence-transformers not installed. Image embeddings disabled.")

    def encode_image(self, image_path: str) -> Optional[List[float]]:
        if not self.model:
            return None
        
        try:
            img = Image.open(image_path)
            # SentenceTransformer handles image preprocessing
            embedding = self.model.encode(img)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error encoding image {image_path}: {e}")
            return None

    @staticmethod
    def cosine_similarity(emb1: List[float], emb2: List[float]) -> float:
        if not util or not emb1 or not emb2:
            return 0.0
        return float(util.cos_sim(emb1, emb2)[0][0])
