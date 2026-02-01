
import shutil
import tempfile
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from mvp.core.state import state

router = APIRouter()
DATA_DIR = Path("data")

@router.post("/validate/face")
async def validate_face(file: UploadFile = File(...)):
    """
    Validates a single face image and returns its embedding.
    Used for client-side duplicate detection before batch search.
    """
    if not state.face_verifier or state.face_verifier.disabled:
        return {"embedding": None, "status": "disabled"}

    # Save to temp file
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    suffix = Path(file.filename).suffix or ".jpg"
    # Use standard tempfile but inside our data dir for safety if needed, 
    # or just system temp. Using system temp is cleaner usually, but faces 
    # might need to be read by models that prefer paths.
    # Logic from main.py uses DATA_DIR/temp_...
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=DATA_DIR) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        # Detect face and get embedding
        # Note: get_face_embedding returns List[float] or None
        embedding = state.face_verifier.get_face_embedding(str(tmp_path))
        return {"embedding": embedding, "status": "ok"}
    except Exception as e:
        print(f"Error validating face: {e}")
        return {"embedding": None, "status": "error", "detail": str(e)}
    finally:
        # Cleanup
        if tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
