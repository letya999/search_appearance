# Quick Start Guide - VLM Provider System

## Installation

1. **Install dependencies:**
```bash
uv sync
```

2. **Configure API keys in `.env`:**
```env
# At least one of these is required:
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...
```

## Basic Usage

### Using the Provider Registry (Recommended)

The provider registry automatically handles fallback, rate limiting, and health checks:

```python
from mvp.providers.registry import registry
from mvp.annotator.prompts import SYSTEM_PROMPT

# Analyze an image
response = await registry.analyze_image(
    image_path="path/to/image.jpg",
    system_prompt=SYSTEM_PROMPT
)

# Access the parsed profile
profile = response.profile

# Check metadata
print(f"Provider: {response.provider}")
print(f"Model: {response.model}")
print(f"Latency: {response.latency_ms}ms")
print(f"Tokens: {response.tokens_used}")
```

### Specifying a Preferred Provider

```python
# Try OpenAI first, fallback to others if it fails
response = await registry.analyze_image(
    image_path="path/to/image.jpg",
    system_prompt=SYSTEM_PROMPT,
    preferred_provider="openai"
)
```

### Using a Specific Provider Directly

```python
from mvp.providers.openai_provider import OpenAIProvider

provider = OpenAIProvider(
    api_key="sk-...",
    model="gpt-4o"
)

response = await provider.analyze_image(
    image_path="path/to/image.jpg",
    system_prompt=SYSTEM_PROMPT
)
```

## Health Checks

```python
# Check all providers
health = await registry.check_all_health()
for provider, is_healthy in health.items():
    print(f"{provider}: {'✓' if is_healthy else '✗'}")

# Check specific provider
from mvp.providers.anthropic_provider import AnthropicProvider
provider = AnthropicProvider(api_key="...", model="claude-3-5-sonnet-20241022")
is_healthy = await provider.health_check()
```

## Statistics

```python
# Get usage statistics
stats = registry.get_stats()

for provider, data in stats.items():
    print(f"{provider}:")
    print(f"  Requests: {data['requests']}")
    print(f"  Success Rate: {data['success_rate']:.1%}")
    print(f"  Avg Latency: {data['avg_latency_ms']:.0f}ms")
    print(f"  Avg Tokens: {data['avg_tokens']:.0f}")
```

## Configuration

### Environment Variables

```env
# Provider API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
OPENROUTER_API_KEY=sk-or-...

# General Settings
ENVIRONMENT=development
DEBUG=false

# Search Settings
SEARCH_DEFAULT_TOP_K=20
SEARCH_DUPLICATE_THRESHOLD=0.9
```

### YAML Configuration (`config/providers.yaml`)

```yaml
providers:
  openai:
    enabled: true
    default_model: "gpt-4o"
    max_retries: 3
    timeout: 60
    rate_limit_rpm: 500
    priority: 100
    
  anthropic:
    enabled: true
    default_model: "claude-3-5-sonnet-20241022"
    priority: 90
```

## Testing

Run the test script to verify everything is working:

```bash
python test_providers.py
```

This will:
1. Check provider initialization
2. Run health checks on all providers
3. Test image analysis (if test images available)
4. Display usage statistics

## Available Providers

| Provider | Models | Priority | Rate Limit |
|----------|--------|----------|------------|
| OpenAI | GPT-4o, GPT-4V | 100 | 500 RPM |
| Anthropic | Claude 3.5 Sonnet/Opus | 90 | 50 RPM |
| Gemini | Gemini 2.0 Flash | 80 | 60 RPM |
| OpenRouter | Multiple models | 70 | 20 RPM |
| Ollama | LLaVA, Qwen-VL (local) | 60 | No limit |

## Fallback Behavior

The registry tries providers in priority order:
1. If `preferred_provider` is specified, try it first
2. Otherwise, try providers in priority order (highest first)
3. Skip unhealthy providers
4. Respect rate limits (wait if necessary)
5. If a provider fails, try the next one
6. If all providers fail, raise an exception

## Advanced Usage

### Custom Provider Configuration

```python
from mvp.core.config import settings, ProviderConfig

# Add a custom provider configuration
settings.providers['custom'] = ProviderConfig(
    name='custom',
    api_key='...',
    base_url='https://custom-api.com/v1',
    default_model='custom-model',
    priority=95
)

# Reinitialize registry
from mvp.providers.registry import ProviderRegistry
registry = ProviderRegistry()
```

### Custom System Prompts

```python
custom_prompt = """
Analyze this image and return JSON with:
{
  "custom_field": "value",
  "another_field": 123
}
"""

response = await registry.analyze_image(
    image_path="image.jpg",
    system_prompt=custom_prompt
)
```

## Troubleshooting

### No providers available
- Make sure at least one API key is set in `.env`
- Check that the provider is enabled in `config/providers.yaml`

### All providers unhealthy
- Verify API keys are correct
- Check internet connectivity
- Look for error messages in console output

### Rate limit errors
- Adjust `rate_limit_rpm` in `config/providers.yaml`
- Use multiple providers to distribute load
- Consider upgrading API tier for higher limits

## Next Steps

See `STAGE_0_1_IMPLEMENTATION.md` for:
- Detailed implementation notes
- Migration guide from old VLMClient
- Full API reference
- Integration examples
