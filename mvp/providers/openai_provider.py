"""
OpenAI VLM Provider (GPT-4o, GPT-4V).
"""
import json
import time
from typing import Optional
from openai import AsyncOpenAI

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.schema.models import PhotoProfile


class OpenAIProvider(VLMProvider):
    """OpenAI GPT-4o/GPT-4V provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o", **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.client = AsyncOpenAI(
            api_key=self.api_key,
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
        """Analyze image using OpenAI GPT-4o/GPT-4V."""
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
                    max_tokens=kwargs.get("max_tokens", 2000),
                    response_format={"type": "json_object"}
                )
                
                latency_ms = (time.time() - start_time) * 1000
                raw_text = response.choices[0].message.content
                
                # Parse to profile
                profile = await self.parse_text_to_profile(raw_text)
                
                return VLMResponse(
                    raw_text=raw_text,
                    profile=profile,
                    provider="openai",
                    model=self.model,
                    tokens_used=response.usage.total_tokens if response.usage else None,
                    latency_ms=latency_ms,
                    metadata={
                        "finish_reason": response.choices[0].finish_reason,
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                        "completion_tokens": response.usage.completion_tokens if response.usage else None
                    }
                )
                
            except Exception as e:
                print(f"OpenAI attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_exception or Exception("Failed to analyze image after retries")
    
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """Parse OpenAI JSON response to PhotoProfile."""
        # Clean potential markdown code blocks
        cleaned = text.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(cleaned)
            return PhotoProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse OpenAI response: {e}\nText: {text[:200]}")
    
    async def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        try:
            # Simple models list call to check connectivity
            await self.client.models.list()
            return True
        except Exception as e:
            print(f"OpenAI health check failed: {e}")
            return False


# For backward compatibility
import asyncio
