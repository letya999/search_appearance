"""
Google Gemini VLM Provider (Gemini 2.0 Flash).
"""
import json
import time
import asyncio
from typing import Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.schema.models import PhotoProfile


class GeminiProvider(VLMProvider):
    """Google Gemini 2.0 Flash provider."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp", **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)
        genai.configure(api_key=self.api_key)
        
        # Configure generation settings
        self.generation_config = {
            "temperature": kwargs.get("temperature", 0.1),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 40),
            "max_output_tokens": kwargs.get("max_tokens", 2048),
            "response_mime_type": "application/json",
        }
        
        # Safety settings - be permissive for appearance analysis
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        self.model_instance = genai.GenerativeModel(
            model_name=self.model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
    
    async def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> VLMResponse:
        """Analyze image using Gemini 2.0 Flash."""
        if user_prompt is None:
            user_prompt = "Analyze this person based on the instructions. Return ONLY valid JSON."
        
        # Load image
        from PIL import Image
        image = Image.open(image_path)
        
        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                # Gemini API is sync, run in executor
                response = await asyncio.to_thread(
                    self.model_instance.generate_content,
                    [full_prompt, image]
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract text
                raw_text = response.text
                
                # Parse to profile
                profile = await self.parse_text_to_profile(raw_text)
                
                # Extract token usage if available
                tokens_used = None
                if hasattr(response, 'usage_metadata'):
                    tokens_used = (
                        response.usage_metadata.prompt_token_count +
                        response.usage_metadata.candidates_token_count
                    )
                
                return VLMResponse(
                    raw_text=raw_text,
                    profile=profile,
                    provider="gemini",
                    model=self.model,
                    tokens_used=tokens_used,
                    latency_ms=latency_ms,
                    metadata={
                        "finish_reason": response.candidates[0].finish_reason.name if response.candidates else None,
                        "prompt_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else None,
                        "completion_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else None
                    }
                )
                
            except Exception as e:
                print(f"Gemini attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_exception or Exception("Failed to analyze image after retries")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate text using Gemini."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model_instance.generate_content,
                    full_prompt
                )
                return response.text
                
            except Exception as e:
                print(f"Gemini text generation attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise last_exception or Exception("Failed to generate text after retries")
    
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """Parse Gemini JSON response to PhotoProfile."""
        # Clean potential markdown code blocks
        cleaned = text.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(cleaned)
            return PhotoProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse Gemini response: {e}\nText: {text[:200]}")
    
    async def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            # List models to check connectivity
            await asyncio.to_thread(genai.list_models)
            return True
        except Exception as e:
            print(f"Gemini health check failed: {e}")
            return False
