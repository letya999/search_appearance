from typing import List, Optional, Literal, Tuple
from pydantic import BaseModel

class CustomAttribute(BaseModel):
    name: str
    type: Literal["enum", "scale", "boolean", "text"]
    values: Optional[List[str]] = None # For enum
    range: Optional[Tuple[float, float]] = None # For scale
    prompt_hint: str # How to describe looking for this to a VLM

class CustomSchema(BaseModel):
    name: str # e.g. "Real Estate", "Dogs"
    attributes: List[CustomAttribute]
    base_prompt: str # System prompt base
    
    def generate_system_prompt(self) -> str:
        prompt = self.base_prompt + "\n\nAnalyze the image for the following attributes:\n"
        for attr in self.attributes:
            prompt += f"- {attr.name}: {attr.prompt_hint}"
            if attr.type == "enum":
                if attr.values:
                     prompt += f" (Possible values: {', '.join(attr.values)})"
            elif attr.type == "scale":
                if attr.range:
                    prompt += f" (Scale from {attr.range[0]} to {attr.range[1]})"
            elif attr.type == "boolean":
                prompt += " (Yes/No)"
            prompt += "\n"
        
        prompt += "\nProvide output in JSON format with keys matching attribute names."
        return prompt
