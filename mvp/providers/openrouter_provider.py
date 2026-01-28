"""
OpenRouter VLM Provider (Multi-model aggregator).
"""
import json
import time
import asyncio
from typing import Optional
from openai import AsyncOpenAI

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.schema.models import PhotoProfile


class OpenRouterProvider(VLMProvider):
    """OpenRouter multi-model provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen-2.5-vl-72b-instruct:free",
        base_url: str = "https://openrouter.ai/api/v1",
        **kwargs
    ):
        super().__init__(api_key=api_key, model=model, base_url=base_url, **kwargs)
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
        """Analyze image using OpenRouter."""
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
                    # OpenRouter-specific headers can be added via extra_headers
                )
                
                latency_ms = (time.time() - start_time) * 1000
                raw_text = response.choices[0].message.content
                
                # Parse to profile
                profile = await self.parse_text_to_profile(raw_text)
                
                return VLMResponse(
                    raw_text=raw_text,
                    profile=profile,
                    provider="openrouter",
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
                print(f"OpenRouter attempt {attempt + 1}/{self.max_retries} failed: {e}")
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
        """Generate text using OpenRouter."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 2000),
                    response_format=kwargs.get("response_format", None)
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                print(f"OpenRouter text generation attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise last_exception or Exception("Failed to generate text after retries")
    
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """Parse OpenRouter JSON response to PhotoProfile."""
        # Clean potential markdown code blocks
        cleaned = text.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(cleaned)
            return PhotoProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse OpenRouter response: {e}\nText: {text[:200]}")
    
    async def health_check(self) -> bool:
        """Check if OpenRouter API is accessible."""
        try:
            # Simple models list call to check connectivity
            await self.client.models.list()
            return True
        except Exception as e:
            print(f"OpenRouter health check failed: {e}")
            return False
