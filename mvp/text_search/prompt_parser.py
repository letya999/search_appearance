"""
Text Prompt Parser for Visual Search.

Converts natural language descriptions into structured PhotoProfile objects
using the configured VLM/LLM providers.
"""
import json
import logging
from typing import Optional, Dict, Any

from mvp.schema.models import PhotoProfile
from mvp.providers.registry import registry

logger = logging.getLogger(__name__)

class PromptParser:
    """
    Parses natural language prompts into structured PhotoProfile objects.
    """
    
    SYSTEM_PROMPT = """
You are an expert visual profile analyzer.
Your task is to convert a natural language description of a person's appearance into a structured JSON profile.

The Output MUST be a valid JSON object matching the following structure (subset of full profile):

{
  "basic": {
    "gender": {"value": "male", "confidence": 0.9},
    "age_group": {"value": "25-34", "confidence": 0.8},
    "ethnicity": {"value": "caucasian", "confidence": 0.8},
    "body_type": {"value": "athletic", "confidence": 0.8}
  },
  "hair": {
    "color": {"value": "black", "confidence": 0.9},
    "length": {"value": "long", "confidence": 0.9},
    "texture": {"value": "straight", "confidence": 0.9}
  },
  "face": {
    "eye_color": {"value": "brown", "confidence": 0.9},
    "facial_hair": {"value": "none", "confidence": 0.9}
  },
  "vibe": {
    "style": {"value": "casual", "confidence": 0.9},
    "vibe": {"value": "friendly", "confidence": 0.9}
  }
}

Rules:
1. Input may be in ANY language. You MUST translate and extract attributes into ENGLISH JSON values according to the schema.
2. For attributes EXPLICITLY mentioned, use high confidence (0.8 - 1.0).
3. For attributes NOT mentioned, you MUST INFER appropriate values based on context or use relevant AVERAGES.
   - Example 1: If "Kazakh" or "Asian" is mentioned, infer Hair Color: "black", Eye Color: "brown" (unless specified otherwise).
   - Example 2: If "Sporty" is mentioned, infer Body Type: "athletic", Style: "sporty".
   - Example 3: If no specific height/weight mentioned, use "medium" / "average".
   - DO NOT leave fields null if a reasonable default or inference exists. FILL ALL FIELDS if possible.
4. "confidence" for inferred/default attributes should be lower (e.g., 0.5 - 0.7).
5. Use EXACTLY these values for enums (no others allowed):
   - Gender: male, female, other
   - Age Group: "18-24", "25-34", "35-44", "45-54", "55+"
   - Ethnicity: caucasian, african, asian, latino, middle_eastern, indian, other
   - Height: short, medium, tall, very_tall
   - Body Type: slim, athletic, average, curvy, plus_size
   - Face Shape: oval, round, square, heart, diamond, oblong
   - Eye Color: blue, green, hazel, brown, black, grey
   - Eye Shape: almond, round, monolid, hooded, downturned, upturned
   - Nose: small, average, large, straight, hooked, button
   - Lips: thin, average, full
   - Jawline: soft, defined, strong
   - Hair Color: black, dark_brown, light_brown, blonde, red, grey, dyed
   - Hair Length: bald, short, medium, long
   - Hair Texture: straight, wavy, curly, coily
   - Facial Hair: none, stubble, beard, mustache, goatee
   - Skin Tone: fair, light, medium, tan, dark
   - Glasses: none, reading, sunglasses
   - Tattoos: none, minimal, visible
   - Style: casual, formal, chic, bohemian, streetwear, vintage, edgy, sporty
   - Vibe: friendly, serious, confident, shy, energetic, calm, intellectual

6. Mappings for common terms:
   - "Young" -> "18-24" or "25-34"
   - "Middle aged" -> "45-54"
   - "Old/Senior" -> "55+"
   - "Dark skin" -> Skin Tone: "dark" (and possibly Ethnicity: "african" if implied)
   - "White" -> Ethnicity: "caucasian", Skin Tone: "light" or "fair"
   - "Average height" / "Middle height" -> Height: "medium"
   
7. Return ONLY the JSON object. No markdown, no explanations.
"""

    def __init__(self):
        self.registry = registry

    async def parse_prompt(self, text: str) -> PhotoProfile:
        """
        Parse a text description into a PhotoProfile.
        
        Args:
            text: Natural language description (e.g., "Tall blonde man with glasses")
            
        Returns:
            PhotoProfile with extracted attributes
        """
        print(f"DEBUG: PromptParser.parse_prompt called with: '{text}'", flush=True)
        
        try:
            # Use the registry to get a working provider
            preferred_provider = None
            if 'openai' in self.registry.providers:
                preferred_provider = 'openai'
            elif 'anthropic' in self.registry.providers:
                preferred_provider = 'anthropic'
            
            provider_names = self.registry._get_provider_order(preferred_provider)
            print(f"DEBUG: Available providers: {provider_names}", flush=True)
            
            if not provider_names:
                print("ERROR: No providers available! Check .env and provider config.", flush=True)
            
            for provider_name in provider_names:
                provider = self.registry.get_provider(provider_name)
                if not provider:
                    continue
                
                try:
                    logger.info(f"Parsing prompt with {provider_name}...")
                    print(f"DEBUG: Using provider {provider_name}...", flush=True)
                    
                    response_text = await provider.generate_text(
                        prompt=text,
                        system_prompt=self.SYSTEM_PROMPT,
                        temperature=0.1,  # Low temp for deterministic extraction
                        response_format={"type": "json_object"} if provider_name == 'openai' else None
                    )
                    
                    print(f"DEBUG: Provider response (len={len(response_text)})", flush=True)
                    
                    # Clean and parse
                    cleaned = response_text.replace("```json", "").replace("```", "").strip()
                    if "{" in cleaned and "}" in cleaned:
                         # Extract outermost JSON if extra text exists
                        start = cleaned.find("{")
                        end = cleaned.rfind("}") + 1
                        cleaned = cleaned[start:end]
                    
                    data = json.loads(cleaned)
                    
                    # Inject dummy ID/Path to fix validation errors
                    if "id" not in data:
                        data["id"] = "temp_text_id"
                    if "image_path" not in data:
                        data["image_path"] = "placeholder.jpg"

                    # Convert to PhotoProfile
                    # We accept partial data, Pydantic defaults handle the rest
                    profile = PhotoProfile(**data)
                    
                    # Fill defaults as requested
                    profile = self._fill_defaults(profile)
                    
                    return profile
                    
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed to parse prompt: {e}")
                    print(f"WARNING: Provider {provider_name} failed: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    continue
            
            raise Exception("All providers failed to parse prompt")
            
        except Exception as e:
            logger.error(f"Error parsing prompt '{text}': {e}")
            print(f"ERROR: parse_prompt failed: {e}", flush=True)
            raise e

    def _fill_defaults(self, profile: PhotoProfile) -> PhotoProfile:
        """
        Fill missing attributes with reasonable defaults.
        """
        from mvp.schema.attributes import (
            Gender, AgeGroup, Ethnicity, Height, BodyType,
            FaceShape, EyeColor, EyeShape, Nose, Lips, Jawline,
            HairColor, HairLength, HairTexture,
            FacialHair, SkinTone, Glasses, Tattoos,
            Style, Vibe
        )
        from mvp.schema.models import AttributeScore

        def ensure(obj, field, default_enum, confidence=0.5):
            if getattr(obj, field) is None:
                setattr(obj, field, AttributeScore(value=default_enum, confidence=confidence))

        # Basic
        # Gender/Ethnicity usually detected, but if not:
        ensure(profile.basic, 'gender', Gender.OTHER) # Fallback
        ensure(profile.basic, 'age_group', AgeGroup.GROUP_25_34) # Most common
        ensure(profile.basic, 'ethnicity', Ethnicity.OTHER)
        ensure(profile.basic, 'height', Height.MEDIUM)
        ensure(profile.basic, 'body_type', BodyType.AVERAGE)

        # Hair
        ensure(profile.hair, 'color', HairColor.BLACK) # Most common global
        ensure(profile.hair, 'length', HairLength.MEDIUM)
        ensure(profile.hair, 'texture', HairTexture.STRAIGHT)

        # Face
        ensure(profile.face, 'face_shape', FaceShape.OVAL)
        ensure(profile.face, 'eye_color', EyeColor.BROWN)
        ensure(profile.face, 'eye_shape', EyeShape.ALMOND)
        ensure(profile.face, 'nose', Nose.AVERAGE)
        ensure(profile.face, 'lips', Lips.AVERAGE)
        ensure(profile.face, 'jawline', Jawline.DEFINED)

        # Extra
        ensure(profile.extra, 'facial_hair', FacialHair.NONE)
        ensure(profile.extra, 'skin_tone', SkinTone.MEDIUM)
        ensure(profile.extra, 'glasses', Glasses.NONE)
        ensure(profile.extra, 'tattoos', Tattoos.NONE)

        # Vibe
        ensure(profile.vibe, 'style', Style.CASUAL)
        ensure(profile.vibe, 'vibe', Vibe.FRIENDLY)

        return profile

