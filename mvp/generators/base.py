from abc import ABC, abstractmethod

class ImageGenerator(ABC):
    """Abstract base class for image generators."""
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> str:
        """
        Generate an image from a prompt.
        
        Args:
            prompt: Text prompt
            **kwargs: Generator specific parameters
            
        Returns:
            Path to the saved generated image or URL
        """
        pass
