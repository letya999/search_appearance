import sys
import json
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mvp.core.embedder import ImageEmbedder

DATA_DIR = Path("data")
BLACKLIST_FILE = DATA_DIR / "blacklist_embeddings.json"

def add_to_blacklist(image_path):
    print(f"Initializing Embedder...")
    embedder = ImageEmbedder()
    
    print(f"Generating embedding for {image_path}...")
    embedding = embedder.encode_image(image_path)
    
    if not embedding:
        print("Failed to generate embedding.")
        return

    # Load existing
    blacklist = []
    if BLACKLIST_FILE.exists():
        with open(BLACKLIST_FILE, "r") as f:
            try:
                blacklist = json.load(f)
            except json.JSONDecodeError:
                pass
    
    blacklist.append(embedding)
    
    with open(BLACKLIST_FILE, "w") as f:
        json.dump(blacklist, f)
        
    print(f"Successfully added {image_path} to blacklist. Total entries: {len(blacklist)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/manage_blacklist.py <path_to_image>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    add_to_blacklist(image_path)
