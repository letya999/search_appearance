"""
Anthropic Claude VLM Provider (Claude 3.5 Sonnet/Opus).
"""
import json
import time
import asyncio
from typing import Optional
from anthropic import AsyncAnthropic

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.schema.models import PhotoProfile


class AnthropicProvider(VLMProvider):
    """Anthropic Claude 3.5 provider."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", **kwargs):
        super().__init__(api_key=api_key, model=model, **kwargs)
        self.client = AsyncAnthropic(
            api_key=self.api_key,
            timeout=self.timeout
        )
    
    async def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> VLMResponse:
        """Analyze image using Claude 3.5."""
        if user_prompt is None:
            user_prompt = "Analyze this person based on the instructions. Return ONLY valid JSON."
        
        # Claude uses base64 directly, not data URLs
        base64_image = self.encode_image_base64(image_path)
        
        # Detect media type
        from pathlib import Path
        ext = Path(image_path).suffix.lower()
        media_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(ext, 'image/jpeg')
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=kwargs.get("max_tokens", 2000),
                    temperature=kwargs.get("temperature", 0.1),
                    system=system_prompt,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": base64_image
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": user_prompt
                                }
                            ]
                        }
                    ]
                )
                
                latency_ms = (time.time() - start_time) * 1000
                
                # Extract text from response
                raw_text = ""
                for block in response.content:
                    if block.type == "text":
                        raw_text += block.text
                
                # Parse to profile
                profile = await self.parse_text_to_profile(raw_text)
                
                return VLMResponse(
                    raw_text=raw_text,
                    profile=profile,
                    provider="anthropic",
                    model=self.model,
                    tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                    latency_ms=latency_ms,
                    metadata={
                        "stop_reason": response.stop_reason,
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                )
                
            except Exception as e:
                print(f"Anthropic attempt {attempt + 1}/{self.max_retries} failed: {e}")
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
        """Generate text using Claude."""
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                # System prompt is a separate parameter in Claude API
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=kwargs.get("max_tokens", 2000),
                    temperature=kwargs.get("temperature", 0.7),
                    system=system_prompt if system_prompt else "",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
                
                # Extract text
                raw_text = ""
                for block in response.content:
                    if block.type == "text":
                        raw_text += block.text
                
                return raw_text
                
            except Exception as e:
                print(f"Anthropic text generation attempt {attempt + 1}/{self.max_retries} failed: {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        raise last_exception or Exception("Failed to generate text after retries")
    
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """Parse Claude JSON response to PhotoProfile."""
        # Claude sometimes wraps JSON in markdown
        cleaned = text.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(cleaned)
            return PhotoProfile(**data)
        except Exception as e:
            raise ValueError(f"Failed to parse Anthropic response: {e}\nText: {text[:200]}")
    
    async def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Simple message to check connectivity
            await self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            return True
        except Exception as e:
            print(f"Anthropic health check failed: {e}")
            return False
