
import torch
import numpy as np
from PIL import Image
from typing import Optional, Union, Tuple
from pathlib import Path

try:
    from facenet_pytorch import MTCNN, InceptionResnetV1
except ImportError:
    MTCNN = None
    InceptionResnetV1 = None
    print("WARNING: facenet-pytorch not installed. Face recognition will be disabled.")

class FaceVerifier:
    def __init__(self):
        if MTCNN is None:
            self.disabled = True
            return
            
        self.disabled = False
        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        print(f"Initializing FaceVerifier on {self.device}...")
        
        # MTCNN for face detection
        # keep_all=False returns the single largest face (best for profile pic checks)
        self.mtcnn = MTCNN(
            keep_all=False, 
            select_largest=True, 
            device=self.device,
            post_process=False,
            margin=20 # Add some margin around the face
        )
        
        # InceptionResnetV1 for embedding (Pretrained on VGGFace2)
        self.resnet = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        print("FaceVerifier initialized.")

    def get_face_embedding(self, image_path: Union[str, Path]) -> Optional[np.ndarray]:
        """
        Detects the largest face in the image and returns its 512-d embedding.
        Returns None if no face is detected.
        """
        if self.disabled:
             return None

        try:
            img = Image.open(image_path)
            # Convert to RGB if needed (e.g. RGBA or Grayscale)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get cropped face tensor directly
            face_tensor = self.mtcnn(img)
            
            if face_tensor is None:
                return None
            
            # Add batch dimension and move to device
            face_tensor = face_tensor.unsqueeze(0).to(self.device)
            
            # Generate embedding
            embedding = self.resnet(face_tensor)
            
            # Detach, move to cpu, flatten to 1D array
            return embedding.detach().cpu().numpy().flatten()
        except Exception as e:
            print(f"Error generating face embedding for {image_path}: {e}")
            return None

    def calculate_distance(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculates L2 (Euclidean) distance between two embeddings.
        Lower distance = More similar.
        Typical threshold for 'same person' is around 0.6 - 0.7.
        """
        return np.linalg.norm(emb1 - emb2)

    def is_match(self, emb1: np.ndarray, emb2: np.ndarray, threshold: float = 0.6) -> Tuple[bool, float]:
        """
        Returns (is_match, distance)
        """
        dist = self.calculate_distance(emb1, emb2)
        return dist < threshold, dist

    def warmup(self):
        """
        Runs dummy data through the models to ensure weights are loaded 
        and CUDA (if present) is initialized.
        """
        if self.disabled:
             return
             
        try:
             print("Warming up FaceVerifier models...", flush=True)
             
             # 1. Warmup Resnet (Embedding)
             # Create dummy tensor (1, 3, 160, 160)
             dummy_input = torch.randn(1, 3, 160, 160).to(self.device)
             _ = self.resnet(dummy_input)
             print(" - InceptionResnetV1 warmed up.", flush=True)

             # 2. Warmup MTCNN (Detection)
             # Create dummy image
             dummy_img = Image.new('RGB', (500, 500), color=(128, 128, 128))
             _ = self.mtcnn(dummy_img) 
             print(" - MTCNN detector warmed up.", flush=True)
             
             print("FaceVerifier warmup complete.", flush=True)
        except Exception as e:
             print(f"WARNING: FaceVerifier warmup failed: {e}", flush=True)
