from typing import Dict, Any, Type
from mvp.schema.attributes import (
    AgeGroup, Height, HairColor, Ethnicity, BodyType, Gender,
    FaceShape, EyeColor, EyeShape, Nose, Lips, Jawline,
    HairLength, HairTexture, FacialHair, SkinTone, Glasses, Tattoos,
    Style, Vibe
)

class MatrixRegistry:
    _matrices: Dict[Type[Any], Dict[str, Dict[str, float]]] = {}

    @classmethod
    def get_matrix(cls, enum_type: Type[Any]) -> Dict[str, Dict[str, float]]:
        """Returns the distance matrix for a given Enum type.
        If no custom matrix is registered, returns a default identity matrix (0 if same, 1 if different).
        """
        if enum_type in cls._matrices:
            return cls._matrices[enum_type]
        return cls._create_identity_matrix(enum_type)

    @staticmethod
    def _create_identity_matrix(enum_type: Type[Any]) -> Dict[str, Dict[str, float]]:
        """Creates a default 0/1 distance matrix."""
        matrix = {}
        members = [e.value for e in enum_type]
        for v1 in members:
            matrix[v1] = {}
            for v2 in members:
                matrix[v1][v2] = 0.0 if v1 == v2 else 1.0
        return matrix

    @classmethod
    def register(cls, enum_type: Type[Any], matrix: Dict[str, Dict[str, float]]):
        # Validate that matrix keys match enum values
        members = {e.value for e in enum_type}
        for k1, row in matrix.items():
            if k1 not in members:
                raise ValueError(f"Invalid key {k1} for enum {enum_type}")
            for k2, val in row.items():
                if k2 not in members:
                    raise ValueError(f"Invalid key {k2} for enum {enum_type}")
        
        # Fill missing with symmetry if possible or identity default? 
        # Better to assume full matrix or fill defaults.
        # Let's clean it up to ensure it's fully populated and symmetric
        full_matrix = {}
        for v1 in members:
            full_matrix[v1] = {}
            for v2 in members:
                if v1 == v2:
                    full_matrix[v1][v2] = 0.0
                elif v1 in matrix and v2 in matrix[v1]:
                    full_matrix[v1][v2] = matrix[v1][v2]
                elif v2 in matrix and v1 in matrix[v2]:
                    # Symmetry
                    full_matrix[v1][v2] = matrix[v2][v1]
                else:
                    # Default max distance
                    full_matrix[v1][v2] = 1.0
        
        cls._matrices[enum_type] = full_matrix

# --- Definitions of specific matrices ---

# 1. AgeGroup: Linear
# 18-24, 25-34, 35-44, 45-54, 55+
_AGE_DISTANCES = {
    AgeGroup.GROUP_18_24.value: {
        AgeGroup.GROUP_18_24.value: 0.0,
        AgeGroup.GROUP_25_34.value: 0.2,
        AgeGroup.GROUP_35_44.value: 0.5,
        AgeGroup.GROUP_45_54.value: 0.8,
        AgeGroup.GROUP_55_PLUS.value: 1.0
    },
    AgeGroup.GROUP_25_34.value: {
        AgeGroup.GROUP_18_24.value: 0.2,
        AgeGroup.GROUP_25_34.value: 0.0,
        AgeGroup.GROUP_35_44.value: 0.2,
        AgeGroup.GROUP_45_54.value: 0.5,
        AgeGroup.GROUP_55_PLUS.value: 0.8
    },
    AgeGroup.GROUP_35_44.value: {
        AgeGroup.GROUP_25_34.value: 0.2,
        AgeGroup.GROUP_35_44.value: 0.0,
        AgeGroup.GROUP_45_54.value: 0.2,
        AgeGroup.GROUP_55_PLUS.value: 0.5
    },
    AgeGroup.GROUP_45_54.value: {
        AgeGroup.GROUP_35_44.value: 0.2,
        AgeGroup.GROUP_45_54.value: 0.0,
        AgeGroup.GROUP_55_PLUS.value: 0.2
    },
    AgeGroup.GROUP_55_PLUS.value: {
        AgeGroup.GROUP_45_54.value: 0.2,
        AgeGroup.GROUP_55_PLUS.value: 0.0
    }
}
MatrixRegistry.register(AgeGroup, _AGE_DISTANCES)

# 2. Height: Linear
# short < medium < tall < very_tall
_HEIGHT_DISTANCES = {
    Height.SHORT.value: {
        Height.MEDIUM.value: 0.3,
        Height.TALL.value: 0.7,
        Height.VERY_TALL.value: 1.0
    },
    Height.MEDIUM.value: {
        Height.SHORT.value: 0.3,
        Height.MEDIUM.value: 0.0,
        Height.TALL.value: 0.3,
        Height.VERY_TALL.value: 0.6
    },
    Height.TALL.value: {
        Height.MEDIUM.value: 0.3,
        Height.TALL.value: 0.0,
        Height.VERY_TALL.value: 0.3
    },
    Height.VERY_TALL.value: {
        Height.TALL.value: 0.3,
        Height.VERY_TALL.value: 0.0
    }
}
MatrixRegistry.register(Height, _HEIGHT_DISTANCES)

# 3. HairColor: Semantic
# BLACK, DARK_BROWN, LIGHT_BROWN, BLONDE, RED, GREY, DYED
_HAIR_COLOR_DISTANCES = {
    HairColor.BLACK.value: {
        HairColor.DARK_BROWN.value: 0.15,
        HairColor.LIGHT_BROWN.value: 0.6,
        HairColor.BLONDE.value: 1.0,
        HairColor.GREY.value: 0.8,
        HairColor.RED.value: 0.9,
    },
    HairColor.DARK_BROWN.value: {
        HairColor.BLACK.value: 0.15,
        HairColor.DARK_BROWN.value: 0.0,
        HairColor.LIGHT_BROWN.value: 0.3,
        HairColor.BLONDE.value: 0.8,
        HairColor.RED.value: 0.7
    },
    HairColor.LIGHT_BROWN.value: {
        HairColor.DARK_BROWN.value: 0.3,
        HairColor.LIGHT_BROWN.value: 0.0,
        HairColor.BLONDE.value: 0.3, # Dark blonde / light brown overlap
        HairColor.RED.value: 0.4
    },
    HairColor.BLONDE.value: {
        HairColor.LIGHT_BROWN.value: 0.3,
        HairColor.BLONDE.value: 0.0,
        HairColor.GREY.value: 0.5,
        HairColor.RED.value: 0.6
    },
    HairColor.GREY.value: {
        HairColor.BLONDE.value: 0.5,
        HairColor.BLACK.value: 0.8,
        HairColor.GREY.value: 0.0
    },
    HairColor.RED.value: {
        HairColor.LIGHT_BROWN.value: 0.4,
        HairColor.BLONDE.value: 0.6,
        HairColor.RED.value: 0.0
    }
}
MatrixRegistry.register(HairColor, _HAIR_COLOR_DISTANCES)

# 4. BodyType: Linear/Semantic
# SLIM, ATHLETIC, AVERAGE, CURVY, PLUS_SIZE
_BODY_TYPE_DISTANCES = {
    BodyType.SLIM.value: {
        BodyType.ATHLETIC.value: 0.2,
        BodyType.AVERAGE.value: 0.4,
        BodyType.CURVY.value: 0.7,
        BodyType.PLUS_SIZE.value: 1.0
    },
    BodyType.ATHLETIC.value: {
        BodyType.SLIM.value: 0.2,
        BodyType.AVERAGE.value: 0.2,
        BodyType.CURVY.value: 0.4,
        BodyType.PLUS_SIZE.value: 0.8
    },
    BodyType.AVERAGE.value: {
        BodyType.ATHLETIC.value: 0.2,
        BodyType.SLIM.value: 0.4,
        BodyType.AVERAGE.value: 0.0,
        BodyType.CURVY.value: 0.3,
        BodyType.PLUS_SIZE.value: 0.6
    },
    BodyType.CURVY.value: {
        BodyType.AVERAGE.value: 0.3,
        BodyType.PLUS_SIZE.value: 0.3,
        BodyType.ATHLETIC.value: 0.4,
        BodyType.SLIM.value: 0.7
    },
    BodyType.PLUS_SIZE.value: {
        BodyType.CURVY.value: 0.3,
        BodyType.AVERAGE.value: 0.6,
        BodyType.SLIM.value: 1.0
    }
}
MatrixRegistry.register(BodyType, _BODY_TYPE_DISTANCES)

# 5. Ethnicity: Semantic Phenotypes
# CAUCASIAN, AFRICAN, ASIAN, LATINO, MIDDLE_EASTERN, INDIAN, OTHER
# Conservative overlap
_ETHNICITY_DISTANCES = {
    Ethnicity.CAUCASIAN.value: {
        Ethnicity.LATINO.value: 0.4,
        Ethnicity.MIDDLE_EASTERN.value: 0.5,
        Ethnicity.ASIAN.value: 1.0,
        Ethnicity.AFRICAN.value: 1.0
    },
    Ethnicity.LATINO.value: {
        Ethnicity.CAUCASIAN.value: 0.4,
        Ethnicity.MIDDLE_EASTERN.value: 0.4, # Often similar complexions
        Ethnicity.INDIAN.value: 0.6,
        Ethnicity.ASIAN.value: 0.8
    },
    Ethnicity.MIDDLE_EASTERN.value: {
        Ethnicity.CAUCASIAN.value: 0.5,
        Ethnicity.LATINO.value: 0.4,
        Ethnicity.INDIAN.value: 0.3, # Similar phenotypes often
        Ethnicity.AFRICAN.value: 0.7
    },
    Ethnicity.INDIAN.value: {
        Ethnicity.MIDDLE_EASTERN.value: 0.3,
        Ethnicity.LATINO.value: 0.6,
        Ethnicity.ASIAN.value: 0.7
    },
    Ethnicity.ASIAN.value: {
        Ethnicity.INDIAN.value: 0.7, # Geographically close but phenotypically distinct usually
        Ethnicity.LATINO.value: 0.8
    },
    Ethnicity.AFRICAN.value: {
        Ethnicity.MIDDLE_EASTERN.value: 0.7,
        Ethnicity.LATINO.value: 0.6
    }
}
MatrixRegistry.register(Ethnicity, _ETHNICITY_DISTANCES)
