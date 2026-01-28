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
    "gender": {"value": "male" | "female", "confidence": 0.9},
    "age_group": {"value": "child" | "teen" | "young_adult" | "adult" | "middle_aged" | "senior", "confidence": 0.8},
    "ethnicity": {"value": "...", "confidence": 0.8},
    "body_type": {"value": "...", "confidence": 0.8}
  },
  "hair": {
    "color": {"value": "...", "confidence": 0.9},
    "length": {"value": "...", "confidence": 0.9},
    "texture": {"value": "...", "confidence": 0.9}
  },
  "face": {
    # Include only if mentioned
    "eye_color": {"value": "...", "confidence": 0.9},
    "facial_hair": {"value": "...", "confidence": 0.9}
  },
  "vibe": {
    "style": {"value": "...", "confidence": 0.9},
    "vibe": {"value": "...", "confidence": 0.9}
  }
}

Rules:
1. ONLY include attributes explicitly mentioned or strongly implied by the description.
2. For attributes not mentioned, DO NOT include them in the JSON (or leave them null).
3. "confidence" should reflect how certain you are based on the text (0.5 - 1.0).
4. Use standard values for enums:
   - Gender: male, female
   - Age: child, teen, young_adult (18-30), adult (30-50), middle_aged (50-65), senior (65+)
   - Hair Color: black, brown, blonde, red, gray, white, unnatural
   - Hair Length: bald, short, medium, long
   - Body Type: slim, athletic, average, plus_size, muscular
   - Eye Color: brown, blue, green, hazel, gray
5. Return ONLY the JSON object. No markdown, no explanations.
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
        # Get formatted schema for better context (optional, but using simplified prompting above)
        # Using the simplified system prompt is usually more robust for "search" 
        # because we only want to match what the user asked for.
        
        try:
            # Use the registry to get a working provider
            # We prefer 'openai' or 'anthropic' for complex instruction following
            preferred_provider = None
            if 'openai' in self.registry.providers:
                preferred_provider = 'openai'
            elif 'anthropic' in self.registry.providers:
                preferred_provider = 'anthropic'
            
            # Use registry logic to find available provider
            provider_names = self.registry._get_provider_order(preferred_provider)
            
            for provider_name in provider_names:
                provider = self.registry.get_provider(provider_name)
                if not provider:
                    continue
                
                try:
                    logger.info(f"Parsing prompt with {provider_name}...")
                    
                    response_text = await provider.generate_text(
                        prompt=text,
                        system_prompt=self.SYSTEM_PROMPT,
                        temperature=0.1,  # Low temp for deterministic extraction
                        response_format={"type": "json_object"} if provider_name == 'openai' else None
                    )
                    
                    # Clean and parse
                    cleaned = response_text.replace("```json", "").replace("```", "").strip()
                    if "{" in cleaned and "}" in cleaned:
                         # Extract outermost JSON if extra text exists
                        start = cleaned.find("{")
                        end = cleaned.rfind("}") + 1
                        cleaned = cleaned[start:end]
                    
                    data = json.loads(cleaned)
                    
                    # Convert to PhotoProfile
                    # We accept partial data, Pydantic defaults handle the rest
                    return PhotoProfile(**data)
                    
                except Exception as e:
                    logger.warning(f"Provider {provider_name} failed to parse prompt: {e}")
                    continue
            
            raise Exception("All providers failed to parse prompt")
            
        except Exception as e:
            logger.error(f"Error parsing prompt '{text}': {e}")
            # Return empty profile on failure? Or raise?
            # Raising allows API to handle error
            raise e
