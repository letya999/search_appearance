import pytest
from mvp.core.distance_matrices import MatrixRegistry
from mvp.core.similarity import calculate_single_sim
from mvp.schema.attributes import HairColor, Height, Ethnicity

def test_hair_color_distances():
    matrix = MatrixRegistry.get_matrix(HairColor)
    
    dist_black_brown = matrix[HairColor.BLACK.value][HairColor.DARK_BROWN.value]
    dist_black_blonde = matrix[HairColor.BLACK.value][HairColor.BLONDE.value]
    
    assert dist_black_brown < dist_black_blonde, "Black should be closer to Dark Brown than to Blonde"
    assert dist_black_brown < 0.3
    assert dist_black_blonde > 0.8

def test_height_distances():
    matrix = MatrixRegistry.get_matrix(Height)
    
    d_short_medium = matrix[Height.SHORT.value][Height.MEDIUM.value]
    d_short_tall = matrix[Height.SHORT.value][Height.TALL.value]
    
    assert d_short_medium < d_short_tall
    assert d_short_tall > 0.5

def test_similarity_calculation():
    # Test perfect match high confidence
    sim = calculate_single_sim(
        HairColor.BLACK, 1.0, 
        HairColor.BLACK, 1.0, 
        HairColor
    )
    assert sim == 1.0
    
    # Test close match high confidence
    sim = calculate_single_sim(
        HairColor.BLACK, 1.0, 
        HairColor.DARK_BROWN, 1.0, 
        HairColor
    )
    # dist is 0.15 -> sim 0.85
    assert 0.8 <= sim <= 0.9
    
    # Test far match
    sim = calculate_single_sim(
        HairColor.BLACK, 1.0, 
        HairColor.BLONDE, 1.0, 
        HairColor
    )
    # dist 1.0 -> sim 0
    assert sim == 0.0
    
    # Test confidence impact
    sim_conf = calculate_single_sim(
        HairColor.BLACK, 0.5, 
        HairColor.DARK_BROWN, 0.5, 
        HairColor
    )
    # base 0.85 * sqrt(0.25) = 0.85 * 0.5 = 0.425
    assert 0.4 < sim_conf < 0.45

def test_ethnicity_semantic():
    matrix = MatrixRegistry.get_matrix(Ethnicity)
    
    d_latino_caucasian = matrix[Ethnicity.LATINO.value][Ethnicity.CAUCASIAN.value]
    d_latino_asian = matrix[Ethnicity.LATINO.value][Ethnicity.ASIAN.value]
    
    assert d_latino_caucasian < d_latino_asian, "Latino should be closer to Caucasian than to Asian"
