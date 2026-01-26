import os
import base64
from typing import Optional
from openai import OpenAI

class VLMClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: str = "qwen/qwen-2.5-vl-72b-instruct:free"):
        # Defaulting to a high quality model on OpenRouter, but can be changed
        self.api_key = api_key or os.environ.get("VLM_API_KEY")
        self.base_url = base_url or os.environ.get("VLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = model
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def analyze_image(self, image_path: str, system_prompt: str, retries: int = 3) -> str:
        base64_image = self.encode_image(image_path)
        
        last_exception = None
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
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
                                    "text": "Analyze this person based on the instructions. Return ONLY valid JSON."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=2000,
                    response_format={"type": "json_object"} 
                )
                return response.choices[0].message.content
            except Exception as e:
                # Log error or print
                print(f"Attempt {attempt+1}/{retries} failed: {e}")
                last_exception = e
                
        raise last_exception or Exception("Failed to analyze image after retries")
