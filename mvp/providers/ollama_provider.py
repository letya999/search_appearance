"""
Ollama VLM Provider (Local LLaVA, Qwen-VL).
"""
import json
import time
import asyncio
from typing import Optional
from openai import AsyncOpenAI

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.schema.models import PhotoProfile


class OllamaProvider(VLMProvider):
    """Ollama local VLM provider (LLaVA, Qwen-VL, etc.)."""
    
    def __init__(
        self,
        api_key: str = "not-needed",
        model: str = "llava:13b",
        base_url: str = "http://localhost:11434/v1",
        **kwargs
    ):
        super().__init__(api_key=api_key, model=model, base_url=base_url, **kwargs)
        # Ollama provides OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=self.api_key,  # Not actually needed for Ollama
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    async def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> VLMResponse:
        """Analyze image using local Ollama model."""
        if user_prompt is None:
            user_prompt = "Analyze this person based on the instructions. Return ONLY valid JSON."
        
        image_url = self.get_image_data_url(image_path)
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": user_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_url
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=kwargs.get("temperature", 0.1),
                    # Note: Ollama might not support all OpenAI parameters
                )
                
                latency_ms = (time.time() - start_time) * 1000
                raw_text = response.choices[0].message.content
                
                # Parse to profile
                profile = await self.parse_text_to_profile(raw_text)
                
                return VLMResponse(
                    raw_text=raw_text,
                    profile=profile,
                    provider="ollama",
                    model=self.model,
                    tokens_used=None,  # Ollama might not provide token counts
                    latency_ms=latency_ms,
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                    }
                )
                
            except Exception as e:
                print(f"Ollama attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_exception or Exception("Failed to analyze image after retries")
    
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """Parse Ollama JSON response to PhotoProfile."""
        # Clean potential markdown code blocks
        cleaned = text.replace("```json", "").replace("```", "").strip()
        
        # Local models might be less reliable, try to extract JSON
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            cleaned = cleaned[start:end]
        
        try:
            data = json.loads(cleaned)
            return PhotoProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse Ollama response: {e}\nText: {text[:200]}")
    
    async def health_check(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            # Try to list models
            await self.client.models.list()
            return True
        except Exception as e:
            print(f"Ollama health check failed: {e}")
            return False
