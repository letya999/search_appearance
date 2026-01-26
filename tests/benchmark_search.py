import time
import random
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from typing import List
from mvp.schema.models import PhotoProfile, BasicAttributesModel, AttributeScore
from mvp.schema.attributes import Gender, AgeGroup, Ethnicity, Height, BodyType
from mvp.search.ranker import Ranker

def generate_random_profile(id_str: str) -> PhotoProfile:
    # Minimal generation for speed test
    basic = BasicAttributesModel(
        gender=AttributeScore(value=random.choice(list(Gender)), confidence=0.9),
        age_group=AttributeScore(value=random.choice(list(AgeGroup)), confidence=0.8),
        ethnicity=AttributeScore(value=random.choice(list(Ethnicity)), confidence=0.9),
        height=AttributeScore(value=random.choice(list(Height)), confidence=0.7),
        body_type=AttributeScore(value=random.choice(list(BodyType)), confidence=0.6)
    )
    return PhotoProfile(
        id=id_str,
        image_path=f"/tmp/{id_str}.jpg",
        basic=basic
    )

def benchmark():
    print("Generating 10,000 candidate profiles...")
    candidates = [generate_random_profile(str(i)) for i in range(10000)]
    target = generate_random_profile("target")
    ranker = Ranker()
    
    print("Starting ranking...")
    start_time = time.time()
    
    # Simulate search
    scores = []
    for cand in candidates:
        s = ranker.score_candidate(target, cand)
        scores.append((cand.id, s))
        
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Ranked 10,000 profiles in {duration:.4f} seconds.")
    print(f"Speed: {10000/duration:.2f} profiles/sec")
    
    # Sort top 5 just to use the result
    scores.sort(key=lambda x: x[1], reverse=True)
    print("Top 5 matches:", scores[:5])

if __name__ == "__main__":
    benchmark()
