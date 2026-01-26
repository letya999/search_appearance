from typing import Any, List, Optional
from mvp.core.distance_matrices import MatrixRegistry

def calculate_single_sim(
    val1: Any, 
    conf1: float, 
    val2: Any, 
    conf2: float, 
    enum_type: Any
) -> float:
    """
    Calculates similarity between two single enum values.
    
    Args:
        val1: Value from first profile
        conf1: Confidence of first value
        val2: Value from second profile 
        conf2: Confidence of second value
        enum_type: The Enum class (e.g. HairColor) to lookup distance matrix
        
    Returns:
        float: Similarity score between 0.0 and 1.0, weighted by confidence.
    """
    if val1 is None or val2 is None:
        return 0.0
        
    # Get distance matrix
    matrix = MatrixRegistry.get_matrix(enum_type)
    
    # Get raw values if they are Enum members
    v1 = val1.value if hasattr(val1, 'value') else val1
    v2 = val2.value if hasattr(val2, 'value') else val2
    
    # Get distance (default 1.0 if not found)
    # We try both v1->v2 and v2->v1 just in case, though matrix should be symmetric/complete
    if v1 in matrix and v2 in matrix[v1]:
        dist = matrix[v1][v2]
    elif v2 in matrix and v1 in matrix[v2]:
        dist = matrix[v2][v1]
    else:
        dist = 1.0 if v1 != v2 else 0.0

    # Base Similarity = 1 - distance
    base_sim = 1.0 - dist
    
    # Adjust by confidence
    # Using geometric mean of confidences as weight
    weight = (conf1 * conf2) ** 0.5
    
    return max(0.0, min(base_sim * weight, 1.0))

def calculate_multi_sim(
    vals1: List[Any], 
    confs1: List[float], 
    vals2: List[Any], 
    confs2: List[float], 
    enum_type: Any
) -> float:
    """
    Calculates Fuzzy Jaccard Similarity for list-based attributes.
    (Placeholder for future use if fields become lists, e.g. Tattoos types)
    """
    if not vals1 or not vals2:
        return 0.0
        
    # Standard Jaccard would be |Intersection| / |Union|
    # Fuzzy Jaccard involves pairwise similarities
    # Sim(A, B) = sum(max_sim(a, B)) / ... (simplified)
    # For now, simplistic implementation just to exist
    
    # Convert enums to raw
    v1_raw = [v.value if hasattr(v, 'value') else v for v in vals1]
    v2_raw = [v.value if hasattr(v, 'value') else v for v in vals2]
    
    intersection = set(v1_raw).intersection(set(v2_raw))
    union = set(v1_raw).union(v2_raw)
    
    if not union:
        return 0.0
        
    return len(intersection) / len(union)
