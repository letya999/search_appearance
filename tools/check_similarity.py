
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path.cwd()))

from mvp.core.state import state
from mvp.core.config import config

async def check_files(file1_path, file2_path):
    print(f"Loading embedder...")
    # Initialize embedder manually if not loaded (this is lighter than full app startup)
    from mvp.models.embedder import ClipEmbedder
    embedder = ClipEmbedder()
    
    print(f"Calculating similarity between:\n1: {file1_path}\n2: {file2_path}")
    
    emb1 = embedder.encode_image(file1_path)
    emb2 = embedder.encode_image(file2_path)
    
    if not emb1 or not emb2:
        print("Error: Could not generate embeddings.")
        return

    sim = embedder.cosine_similarity(emb1, emb2)
    print(f"\nSimilarity Score: {sim:.5f}")
    
    if sim > 0.85:
        print("Result: WOULD BE BLOCKED (Duplicate detected)")
    else:
        print("Result: WOULD BE ACCEPTED (Too different)")

if __name__ == "__main__":
    f1 = r"c:\Users\User\a_projects\search_appearance\images (24).jpg"
    f2 = r"c:\Users\User\a_projects\search_appearance\images (25).jpg"
    
    asyncio.run(check_files(f1, f2))
