"""Quick test to check if .env is loading correctly."""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Enable debug
os.environ["DEBUG_CONFIG"] = "1"

print("=" * 60)
print("CONFIGURATION DEBUG TEST")
print("=" * 60)
print()

# Check .env file directly
env_file = Path(__file__).parent / ".env"
print(f"📁 .env file: {env_file}")
print(f"   Exists: {env_file.exists()}")
print(f"   Absolute path: {env_file.absolute()}")
print()

if env_file.exists():
    print("📄 .env contents:")
    with open(env_file, 'r') as f:
        for i, line in enumerate(f, 1):
            # Don't print full API keys
            if '=' in line:
                key, value = line.split('=', 1)
                value_preview = value[:20] + "..." if len(value) > 20 else value
                print(f"   {i}: {key}={value_preview.strip()}")
            else:
                print(f"   {i}: {line.strip()}")
    print()

# Now try to load config
print("🔧 Loading Settings...")
try:
    from mvp.core.config import settings, ENV_FILE
    
    print(f"✓ Settings loaded successfully")
    print(f"  ENV_FILE used: {ENV_FILE}")
    print(f"  ENV_FILE exists: {ENV_FILE.exists()}")
    print()
    
    print("🔑 API Keys found:")
    print(f"  OPENAI_API_KEY: {'✓ ' + settings.openai_api_key[:20] + '...' if settings.openai_api_key else '✗ Not found'}")
    print(f"  ANTHROPIC_API_KEY: {'✓ Found' if settings.anthropic_api_key else '✗ Not found'}")
    print(f"  GOOGLE_API_KEY: {'✓ Found' if settings.google_api_key else '✗ Not found'}")
    print(f"  OPENROUTER_API_KEY: {'✓ Found' if settings.openrouter_api_key else '✗ Not found'}")
    print()
    
    print("🔌 Providers configured:")
    for name, provider in settings.providers.items():
        has_key = "✓" if provider.api_key else "✗"
        print(f"  {name}: {provider.default_model} (priority: {provider.priority}) - API key: {has_key}")
    print()
    
    print("✅ Enabled providers (with API keys):")
    enabled = settings.get_enabled_providers()
    if enabled:
        for provider in enabled:
            print(f"  {provider.name}: {provider.default_model} (priority: {provider.priority})")
    else:
        print("  None!")
    print()
    
    if not settings.providers:
        print("⚠️  No providers configured!")
        print("   This means API keys were not loaded from .env")
        
except Exception as e:
    print(f"✗ Failed to load settings: {e}")
    import traceback
    traceback.print_exc()
