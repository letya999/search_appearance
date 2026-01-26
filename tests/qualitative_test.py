
import pytest
from mvp.schema.models import PhotoProfile, BasicAttributesModel, HairAttributesModel, AttributeScore, FaceAttributesModel, Gender, Ethnicity, HairColor, AgeGroup, Height, BodyType
from mvp.search.aggregator import ProfileAggregator
from mvp.search.ranker import Ranker

def create_profile(id, ethnicity=None, hair_color=None):
    basic_args = {}
    if ethnicity:
        basic_args["ethnicity"] = AttributeScore(value=ethnicity, confidence=1.0)
    
    hair_args = {}
    if hair_color:
        hair_args["color"] = AttributeScore(value=hair_color, confidence=1.0)
        
    return PhotoProfile(
        id=id,
        image_path=f"path/{id}.jpg",
        basic=BasicAttributesModel(**basic_args),
        hair=HairAttributesModel(**hair_args)
    )

def test_ethnicity_focus():
    candidates = [
        create_profile("asian_1", Ethnicity.ASIAN, HairColor.BLACK),
        create_profile("caucasian_1", Ethnicity.CAUCASIAN, HairColor.BLONDE),
        create_profile("african_1", Ethnicity.AFRICAN, HairColor.BLACK),
    ]
    
    # Target: Asian
    positives = [create_profile("target", Ethnicity.ASIAN, HairColor.BLACK)]
    
    aggregator = ProfileAggregator()
    target_profile = aggregator.build_target_profile(positives, [])
    
    ranker = Ranker()
    ranked = []
    for c in candidates:
        score = ranker.score_candidate(target_profile, c)
        ranked.append((c.id, score))
        
    ranked.sort(key=lambda x: x[1], reverse=True)
    
    print("\n--- Ethnicity Test Results ---")
    for r in ranked:
        print(r)
        
    assert ranked[0][0] == "asian_1", "Asian profile should rank highest for Asian target"

def test_negative_impact():
    print("\n--- Negative Logic Test ---")
    # Scenario: User has mixed feelings.
    # Positives: One Dark Brown, One Black.
    # Without negative, Black might be picked or they differ slightly.
    # With Negative=Black, Dark Brown should decisively win the Target construction.
    
    positives = [
        create_profile("pos_db", Ethnicity.CAUCASIAN, HairColor.DARK_BROWN),
        create_profile("pos_blk", Ethnicity.CAUCASIAN, HairColor.BLACK)
    ]
    
    # Case A: No negatives
    aggregator = ProfileAggregator()
    target_A = aggregator.build_target_profile(positives, [])
    print(f"Target A (No Neg) Hair: {target_A.hair.color.value}")
    
    # Case B: Negative = Black
    negatives = [create_profile("neg_blk", Ethnicity.CAUCASIAN, HairColor.BLACK)]
    target_B = aggregator.build_target_profile(positives, negatives)
    print(f"Target B (With Neg) Hair: {target_B.hair.color.value}")
    
    assert target_B.hair.color.value == HairColor.DARK_BROWN
    
    # Now let's see ranking against a Black Candidate
    candidate_black = create_profile("cand_black", Ethnicity.CAUCASIAN, HairColor.BLACK)
    
    # Negative Target for Case B
    neg_target_B = aggregator.build_target_profile(negatives, [])

    ranker = Ranker()
    score_A = ranker.score_candidate(target_A, candidate_black)
    score_B = ranker.score_candidate(target_B, candidate_black, negative_target=neg_target_B)
    
    print(f"Score against Target A (Mixed): {score_A}")
    print(f"Score against Target B (Neg Black) + Negative Penalty: {score_B}")
    
    # We expect Score B to be significantly lower than Score A
    # Calculation prediction:
    # Target B is DarkBrown. Cand is Black. Sim = 0.85 approx. Mean ~ 0.925.
    # NegTarget B is Black. Cand is Black. Sim = 1.0. 
    # Penalty = 1.0 * 0.5 = 0.5.
    # Result ~ 0.925 - 0.5 = 0.425.
    
    assert score_B < score_A - 0.3, "Score should drop significantly with negative penalty"
    assert target_B.hair.color.value != HairColor.BLACK

if __name__ == "__main__":
    test_ethnicity_focus()
    test_negative_impact()
