"""
Abstract base class for VLM (Vision Language Model) providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pathlib import Path
import base64
from pydantic import BaseModel

from mvp.schema.models import PhotoProfile


class VLMResponse(BaseModel):
    """Standardized response from VLM analysis."""
    raw_text: str
    profile: Optional[PhotoProfile] = None
    metadata: Dict[str, Any] = {}
    provider: str
    model: str
    tokens_used: Optional[int] = None
    latency_ms: Optional[float] = None


class VLMProvider(ABC):
    """
    Abstract base class for Vision Language Model providers.
    
    All VLM providers must implement:
    1. analyze_image() - Analyze an image and return structured data
    2. parse_text_to_profile() - Parse VLM text response into PhotoProfile
    3. health_check() - Check if provider is available
    """
    
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 60,
        **kwargs
    ):
        """
        Initialize VLM provider.
        
        Args:
            api_key: API key for the provider
            model: Model identifier to use
            base_url: Optional custom base URL
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.config = kwargs
        
    @abstractmethod
    async def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        **kwargs
    ) -> VLMResponse:
        """
        Analyze an image using the VLM.
        
        Args:
            image_path: Path to the image file
            system_prompt: System prompt with instructions
            user_prompt: Optional user prompt (defaults to generic analysis request)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            VLMResponse with analysis results
            
        Raises:
            Exception: If analysis fails after all retries
        """
        pass
    
    @abstractmethod
    async def parse_text_to_profile(self, text: str) -> PhotoProfile:
        """
        Parse VLM text response into a PhotoProfile.
        
        Args:
            text: Raw text response from VLM
            
        Returns:
            PhotoProfile object
            
        Raises:
            ValueError: If parsing fails
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and available.
        
        Returns:
            True if provider is available, False otherwise
        """
        pass
    
    def encode_image_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def get_image_data_url(self, image_path: str) -> str:
        """
        Get data URL for image.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Data URL string (data:image/jpeg;base64,...)
        """
        base64_image = self.encode_image_base64(image_path)
        # Detect image type from extension
        ext = Path(image_path).suffix.lower()
        mime_type = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }.get(ext, 'image/jpeg')
        
        return f"data:{mime_type};base64,{base64_image}"
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace("Provider", "").lower()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"
