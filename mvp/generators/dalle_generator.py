import os
import aiohttp
import uuid
from pathlib import Path
from openai import AsyncOpenAI
from mvp.generators.base import ImageGenerator
from mvp.core.config import settings

class DalleGenerator(ImageGenerator):
    """DALL-E 3 Image Generator."""
    
    def __init__(self, api_key: str = None, output_dir: str = "data/generated"):
        if not api_key:
            api_key = settings.openai_api_key
            
        if not api_key:
            raise ValueError("OpenAI API key is required for DALL-E generator")
            
        self.client = AsyncOpenAI(api_key=api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def generate_image(self, prompt: str, **kwargs) -> str:
        """
        Generate image using DALL-E 3.
        
        Args:
            prompt: Image description
            size: Size (default 1024x1024)
            quality: Quality (standard/hd)
            
        Returns:
            Path to saved image
        """
        try:
            print(f"Generating image with DALL-E 3: {prompt[:50]}...")
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=kwargs.get("size", "1024x1024"),
                quality=kwargs.get("quality", "standard"),
                n=1,
            )
            
            image_url = response.data[0].url
            
            # Download and save
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status == 200:
                        filename = f"gen_{uuid.uuid4()}.png"
                        filepath = self.output_dir / filename
                        with open(filepath, "wb") as f:
                            f.write(await resp.read())
                        print(f"Image saved to {filepath}")
                        return str(filepath)
                    else:
                        raise Exception(f"Failed to download image: {resp.status}")
                        
        except Exception as e:
            print(f"DALL-E generation failed: {e}")
            raise e
