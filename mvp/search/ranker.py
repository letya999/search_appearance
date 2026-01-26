from typing import Dict, Any, Type, List, Optional
from mvp.schema.models import PhotoProfile
from mvp.core.similarity import calculate_single_sim
# Import all enums to ensure they are registered/available if needed, 
# though we rely on the object's type.

class Ranker:
    # Default importance weights
    DEFAULT_WEIGHTS = {
        # Critical
        "basic.gender": 10.0, 
        
        # High impact
        "hair.color": 2.5,
        "basic.ethnicity": 2.5,
        "basic.age_group": 2.0,
        "face.eye_color": 1.5,
        
        # Medium
        "basic.height": 1.0,
        "basic.body_type": 1.0,
        "hair.length": 1.5,
        "hair.texture": 1.0,
        "face.face_shape": 1.0,
        "extra.glasses": 1.5,
        "extra.facial_hair": 1.5,
        
        # Low / Nuance
        "face.nose": 0.8,
        "face.lips": 0.8,
        "vibe.style": 0.5,
        "vibe.vibe": 0.5
    }

    def score_candidate(self, target: PhotoProfile, candidate: PhotoProfile, weights: Dict[str, float] = None, negative_target: Optional[PhotoProfile] = None) -> float:
        """
        Calculates a weighted similarity score between a target profile and a candidate.
        Returns visual similarity on scale 0.0 to 1.0.
        If negative_target is provided, subtracts its similarity from the score.
        """
        final_weights = self.DEFAULT_WEIGHTS.copy()
        if weights:
            final_weights.update(weights)
            
        total_score = 0.0
        total_weight = 0.0
        
        # Calculate positive similarity
        categories = ["basic", "face", "hair", "extra", "vibe"]
        
        for cat_name in categories:
            t_cat = getattr(target, cat_name, None)
            c_cat = getattr(candidate, cat_name, None)
            
            if not t_cat or not c_cat: continue
            
            # Iterate fields
            for field_name in t_cat.model_fields.keys():
                t_attr = getattr(t_cat, field_name)
                c_attr = getattr(c_cat, field_name)
                
                # Check if attributes exist and have values
                if not t_attr or not t_attr.value:
                    continue
                if not c_attr or not c_attr.value:
                    continue
                    
                # Get weight
                key = f"{cat_name}.{field_name}"
                w = final_weights.get(key, 1.0)
                
                # Determine Enum Class for Distance Matrix lookup
                enum_type = type(t_attr.value)
                
                # Calculate Similarity
                sim = calculate_single_sim(
                    t_attr.value, t_attr.confidence,
                    c_attr.value, c_attr.confidence,
                    enum_type
                )
                
                total_score += sim * w
                total_weight += w

        if total_weight == 0:
            return 0.0
            
        base_score = total_score / total_weight
        
        if not negative_target:
            return base_score
            
        # Calculate negative similarity
        neg_score_sum = 0.0
        neg_weight_sum = 0.0
        
        for cat_name in categories:
            n_cat = getattr(negative_target, cat_name, None)
            c_cat = getattr(candidate, cat_name, None)
            
            if not n_cat or not c_cat: continue
            
            for field_name in n_cat.model_fields.keys():
                n_attr = getattr(n_cat, field_name)
                c_attr = getattr(c_cat, field_name)
                
                if not n_attr or not n_attr.value: continue
                if not c_attr or not c_attr.value: continue
                
                key = f"{cat_name}.{field_name}"
                w = final_weights.get(key, 1.0)
                
                enum_type = type(n_attr.value)
                
                sim = calculate_single_sim(
                    n_attr.value, n_attr.confidence,
                    c_attr.value, c_attr.confidence,
                    enum_type
                )
                
                neg_score_sum += sim * w
                neg_weight_sum += w
        
        neg_penalty = 0.0
        if neg_weight_sum > 0:
            neg_similarity = neg_score_sum / neg_weight_sum
            # Penalty Factor: How much we punish similarity to negative.
            # 0.5 means if it's 100% like negative, we subtract 0.5 from score.
            neg_penalty = neg_similarity * 0.5 
            
        return max(0.0, base_score - neg_penalty)

    def filter_candidates(self, candidates: List[PhotoProfile], criteria: Dict[str, Any]) -> List[PhotoProfile]:
        """
        Hard filtering of candidates. 
        criteria: dict like {"basic.gender": "male", "basic.age_group": ["25-34", "35-44"]}
        """
        filtered = []
        for cand in candidates:
            match = True
            for key, required_val in criteria.items():
                # key e.g. "basic.gender"
                parts = key.split(".")
                if len(parts) != 2: continue
                
                cat_obj = getattr(cand, parts[0], None)
                if not cat_obj: 
                    match = False; break
                    
                attr = getattr(cat_obj, parts[1], None)
                if not attr or not attr.value:
                    if required_val is not None:
                        match = False; break
                    else:
                        continue

                # Check value
                val = attr.value.value if hasattr(attr.value, 'value') else attr.value
                
                if isinstance(required_val, list):
                    if val not in required_val:
                        match = False; break
                else:
                    if val != required_val:
                        match = False; break
                        
            if match:
                filtered.append(cand)
                
        return filtered
