"""
Provider Registry with auto-detection, fallback chain, rate limiting, and health checks.
"""
import asyncio
import time
from typing import Optional, List, Dict, Type
from collections import defaultdict
from datetime import datetime, timedelta

from mvp.providers.base import VLMProvider, VLMResponse
from mvp.providers.openai_provider import OpenAIProvider
from mvp.providers.anthropic_provider import AnthropicProvider
from mvp.providers.gemini_provider import GeminiProvider
from mvp.providers.openrouter_provider import OpenRouterProvider
from mvp.providers.ollama_provider import OllamaProvider
from mvp.core.config import settings, ProviderConfig


class RateLimiter:
    """Simple rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests: List[datetime] = []
    
    async def acquire(self):
        """Wait if necessary to respect rate limit."""
        if self.requests_per_minute is None:
            return  # No rate limit
        
        now = datetime.now()
        # Remove requests older than 1 minute
        self.requests = [r for r in self.requests if now - r < timedelta(minutes=1)]
        
        if len(self.requests) >= self.requests_per_minute:
            # Calculate wait time
            oldest = self.requests[0]
            wait_until = oldest + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                print(f"Rate limit reached, waiting {wait_seconds:.1f}s...")
                await asyncio.sleep(wait_seconds)
                # Retry acquire after waiting
                return await self.acquire()
        
        self.requests.append(now)


class ProviderRegistry:
    """
    Registry for managing multiple VLM providers with:
    - Auto-detection based on API keys
    - Fallback chain when providers fail
    - Rate limiting per provider
    - Health checks
    """
    
    # Map provider names to classes
    PROVIDER_CLASSES: Dict[str, Type[VLMProvider]] = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'gemini': GeminiProvider,
        'openrouter': OpenRouterProvider,
        'ollama': OllamaProvider,
    }
    
    def __init__(self):
        self.providers: Dict[str, VLMProvider] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.health_status: Dict[str, bool] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self.health_check_interval = timedelta(minutes=5)
        
        # Statistics
        self.stats = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_latency_ms': 0,
            'total_tokens': 0
        })
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize providers from configuration."""
        enabled_providers = settings.get_enabled_providers()
        
        print(f"Initializing {len(enabled_providers)} VLM providers...")
        
        for config in enabled_providers:
            try:
                provider_class = self.PROVIDER_CLASSES.get(config.name)
                if not provider_class:
                    print(f"Unknown provider: {config.name}")
                    continue
                
                # Initialize provider
                provider = provider_class(
                    api_key=config.api_key,
                    model=config.default_model,
                    base_url=config.base_url,
                    max_retries=config.max_retries,
                    timeout=config.timeout
                )
                
                self.providers[config.name] = provider
                
                # Setup rate limiter
                if config.rate_limit_rpm:
                    self.rate_limiters[config.name] = RateLimiter(config.rate_limit_rpm)
                
                # Initialize health status
                self.health_status[config.name] = True  # Assume healthy initially
                
                print(f"  ✓ {config.name}: {config.default_model} (priority: {config.priority})")
                
            except Exception as e:
                print(f"  ✗ Failed to initialize {config.name}: {e}")
    
    async def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        **kwargs
    ) -> VLMResponse:
        """
        Analyze image with automatic provider fallback.
        
        Args:
            image_path: Path to image file
            system_prompt: System prompt with instructions
            user_prompt: Optional user prompt
            preferred_provider: Optional preferred provider name
            **kwargs: Additional parameters for VLM
            
        Returns:
            VLMResponse from successful provider
            
        Raises:
            Exception: If all providers fail
        """
        # Get provider order (preferred first, then by priority)
        provider_order = self._get_provider_order(preferred_provider)
        
        if not provider_order:
            raise Exception("No VLM providers available")
        
        last_exception = None
        
        for provider_name in provider_order:
            provider = self.providers[provider_name]
            
            # Check health
            if not await self._check_health(provider_name):
                print(f"Skipping unhealthy provider: {provider_name}")
                continue
            
            try:
                # Respect rate limit
                if provider_name in self.rate_limiters:
                    await self.rate_limiters[provider_name].acquire()
                
                # Track request
                self.stats[provider_name]['requests'] += 1
                
                print(f"Attempting analysis with {provider_name}...")
                
                # Analyze
                response = await provider.analyze_image(
                    image_path=image_path,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    **kwargs
                )
                
                # Update stats
                self.stats[provider_name]['successes'] += 1
                if response.latency_ms:
                    self.stats[provider_name]['total_latency_ms'] += response.latency_ms
                if response.tokens_used:
                    self.stats[provider_name]['total_tokens'] += response.tokens_used
                
                print(f"✓ Success with {provider_name} ({response.latency_ms:.0f}ms)")
                
                return response
                
            except Exception as e:
                print(f"✗ {provider_name} failed: {e}")
                self.stats[provider_name]['failures'] += 1
                self.health_status[provider_name] = False  # Mark as unhealthy
                last_exception = e
                continue
        
        # All providers failed
        raise last_exception or Exception("All VLM providers failed")
    
    def _get_provider_order(self, preferred: Optional[str] = None) -> List[str]:
        """Get provider order for fallback chain."""
        # Get enabled providers sorted by priority
        enabled_configs = settings.get_enabled_providers()
        provider_names = [c.name for c in enabled_configs if c.name in self.providers]
        
        # Move preferred to front if specified
        if preferred and preferred in provider_names:
            provider_names.remove(preferred)
            provider_names.insert(0, preferred)
        
        return provider_names
    
    async def _check_health(self, provider_name: str) -> bool:
        """Check provider health with caching."""
        now = datetime.now()
        
        # Check if we need to refresh health status
        last_check = self.last_health_check.get(provider_name)
        if last_check and now - last_check < self.health_check_interval:
            # Use cached status
            return self.health_status.get(provider_name, False)
        
        # Perform health check
        provider = self.providers[provider_name]
        try:
            is_healthy = await provider.health_check()
            self.health_status[provider_name] = is_healthy
            self.last_health_check[provider_name] = now
            return is_healthy
        except Exception as e:
            print(f"Health check failed for {provider_name}: {e}")
            self.health_status[provider_name] = False
            self.last_health_check[provider_name] = now
            return False
    
    async def check_all_health(self) -> Dict[str, bool]:
        """Check health of all providers."""
        results = {}
        for provider_name in self.providers:
            results[provider_name] = await self._check_health(provider_name)
        return results
    
    def get_stats(self) -> Dict[str, dict]:
        """Get usage statistics for all providers."""
        stats_copy = {}
        for provider_name, stats in self.stats.items():
            stats_copy[provider_name] = {
                **stats,
                'success_rate': (
                    stats['successes'] / stats['requests']
                    if stats['requests'] > 0 else 0
                ),
                'avg_latency_ms': (
                    stats['total_latency_ms'] / stats['successes']
                    if stats['successes'] > 0 else 0
                ),
                'avg_tokens': (
                    stats['total_tokens'] / stats['successes']
                    if stats['successes'] > 0 else 0
                )
            }
        return stats_copy
    
    def get_provider(self, name: str) -> Optional[VLMProvider]:
        """Get a specific provider by name."""
        return self.providers.get(name)
    
    def list_providers(self) -> List[str]:
        """List all available provider names."""
        return list(self.providers.keys())


# Global registry instance
registry = ProviderRegistry()
