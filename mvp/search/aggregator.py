from typing import List, Dict, Any, Type
from collections import defaultdict
from pydantic import BaseModel
from mvp.schema.models import (
    PhotoProfile, AttributeScore, 
    BasicAttributesModel, FaceAttributesModel, 
    HairAttributesModel, ExtraAttributesModel, VibeAttributesModel
)

class ProfileAggregator:
    CATEGORIES = {
        "basic": BasicAttributesModel, 
        "face": FaceAttributesModel, 
        "hair": HairAttributesModel, 
        "extra": ExtraAttributesModel, 
        "vibe": VibeAttributesModel
    }

    @staticmethod
    def _aggregate_attribute(
        positives: List[PhotoProfile], 
        negatives: List[PhotoProfile], 
        category: str, 
        field: str
    ) -> AttributeScore:
        scores = defaultdict(float)
        
        # Add weights from positives
        for p in positives:
            cat_obj = getattr(p, category, None)
            if not cat_obj: continue
            attr = getattr(cat_obj, field, None)
            if attr and attr.value:
                # Use raw string value for aggregation
                val = attr.value.value if hasattr(attr.value, 'value') else attr.value
                scores[val] += attr.confidence

        # Subtract weights from negatives
        for n in negatives:
            cat_obj = getattr(n, category, None)
            if not cat_obj: continue
            attr = getattr(cat_obj, field, None)
            if attr and attr.value:
                val = attr.value.value if hasattr(attr.value, 'value') else attr.value
                # Penalize, but don't let it go below zero too easily if it was strong positive
                # Penalty weight 0.5 implies negatives are half as strong 'votes' against
                scores[val] -= (attr.confidence * 0.8)

        if not scores:
            return None

        # Filter out negative scores and find max
        valid_scores = {k: v for k, v in scores.items() if v > 0}
        if not valid_scores:
            # Fallback to the raw max even if negative, or just return None?
            # If everything is negative, we probably shouldn't search for it.
            # But let's pick the "least negative" or just the top one.
            best_val = max(scores.items(), key=lambda x: x[1])[0]
        else:
            best_val = max(valid_scores.items(), key=lambda x: x[1])[0]

        # Return constructed score. 
        # We set confidence to 1.0 for the Target Profile to indicate "This is what we want".
        return AttributeScore(value=best_val, confidence=1.0)

    def build_target_profile(self, positives: List[PhotoProfile], negatives: List[PhotoProfile]) -> PhotoProfile:
        result_data = {
            "id": "target_aggregated",
            "image_path": "aggregated",
        }

        # Iterate over each category and field
        for cat_name, cat_model in self.CATEGORIES.items():
            cat_data = {}
            # Inspect fields of the Pydantic model
            for field_name in cat_model.model_fields.keys():
                score = self._aggregate_attribute(positives, negatives, cat_name, field_name)
                if score:
                    cat_data[field_name] = score
            
            result_data[cat_name] = cat_model(**cat_data)

        return PhotoProfile(**result_data)
