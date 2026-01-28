from typing import List, Optional, Generic, TypeVar, Dict
from pydantic import BaseModel, Field
from .attributes import (
    Gender, AgeGroup, Ethnicity, Height, BodyType,
    FaceShape, EyeColor, EyeShape, Nose, Lips, Jawline,
    HairColor, HairLength, HairTexture,
    FacialHair, SkinTone, Glasses, Tattoos,
    Style, Vibe
)

T = TypeVar('T')

class AttributeScore(BaseModel, Generic[T]):
    value: T
    confidence: float = Field(..., ge=0.0, le=1.0)

class BasicAttributesModel(BaseModel):
    gender: Optional[AttributeScore[Gender]] = None
    age_group: Optional[AttributeScore[AgeGroup]] = None
    ethnicity: Optional[AttributeScore[Ethnicity]] = None
    height: Optional[AttributeScore[Height]] = None
    body_type: Optional[AttributeScore[BodyType]] = None

class FaceAttributesModel(BaseModel):
    face_shape: Optional[AttributeScore[FaceShape]] = None
    eye_color: Optional[AttributeScore[EyeColor]] = None
    eye_shape: Optional[AttributeScore[EyeShape]] = None
    nose: Optional[AttributeScore[Nose]] = None
    lips: Optional[AttributeScore[Lips]] = None
    jawline: Optional[AttributeScore[Jawline]] = None

class HairAttributesModel(BaseModel):
    color: Optional[AttributeScore[HairColor]] = None
    length: Optional[AttributeScore[HairLength]] = None
    texture: Optional[AttributeScore[HairTexture]] = None

class ExtraAttributesModel(BaseModel):
    facial_hair: Optional[AttributeScore[FacialHair]] = None
    skin_tone: Optional[AttributeScore[SkinTone]] = None
    glasses: Optional[AttributeScore[Glasses]] = None
    tattoos: Optional[AttributeScore[Tattoos]] = None

class VibeAttributesModel(BaseModel):
    style: Optional[AttributeScore[Style]] = None
    vibe: Optional[AttributeScore[Vibe]] = None

class PhotoProfile(BaseModel):
    id: str
    image_path: str
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding of the image")
    basic: BasicAttributesModel = Field(default_factory=BasicAttributesModel)
    face: FaceAttributesModel = Field(default_factory=FaceAttributesModel)
    hair: HairAttributesModel = Field(default_factory=HairAttributesModel)
    extra: ExtraAttributesModel = Field(default_factory=ExtraAttributesModel)
    vibe: VibeAttributesModel = Field(default_factory=VibeAttributesModel)

class SearchQuery(BaseModel):
    positive_ids: List[str]
    negative_ids: List[str] = Field(default_factory=list)
    importance_weights: Dict[str, float] = Field(default_factory=dict) # e.g. {"hair.color": 1.5}
