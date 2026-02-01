"""
Test script for the new VLM provider system.
Run this to verify that the provider registry is working correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mvp.providers.registry import registry
from mvp.core.config import settings


async def test_provider_initialization():
    """Test that providers are initialized correctly."""
    print("=" * 60)
    print("VLM PROVIDER SYSTEM TEST")
    print("=" * 60)
    print()
    
    # Check configuration
    print("📋 Configuration:")
    print(f"  Environment: {settings.environment}")
    print(f"  Debug: {settings.debug}")
    print()
    
    # List available providers
    providers = registry.list_providers()
    print(f"🔌 Available Providers: {len(providers)}")
    for provider_name in providers:
        provider = registry.get_provider(provider_name)
        print(f"  ✓ {provider_name}: {provider.model}")
    print()
    
    # Check health of all providers
    print("🏥 Health Checks:")
    health_status = await registry.check_all_health()
    
    healthy_count = 0
    for provider_name, is_healthy in health_status.items():
        status = "✓ Healthy" if is_healthy else "✗ Unhealthy"
        print(f"  {provider_name}: {status}")
        if is_healthy:
            healthy_count += 1
    
    print()
    print(f"Summary: {healthy_count}/{len(providers)} providers are healthy")
    print()
    
    if healthy_count == 0:
        print("⚠️  WARNING: No healthy providers found!")
        print("   Make sure you have set at least one API key in .env:")
        print("   - OPENAI_API_KEY")
        print("   - ANTHROPIC_API_KEY")
        print("   - GOOGLE_API_KEY")
        print("   - OPENROUTER_API_KEY")
        return False
    
    return True


async def test_image_analysis():
    """Test image analysis with the provider registry."""
    print("=" * 60)
    print("IMAGE ANALYSIS TEST")
    print("=" * 60)
    print()
    
    # Find a test image
    test_images = [
        Path("data/raw_1000"),
        Path("data"),
    ]
    
    test_image = None
    for img_dir in test_images:
        if img_dir.exists():
            images = list(img_dir.glob("*.jpg")) + list(img_dir.glob("*.jpeg")) + list(img_dir.glob("*.png"))
            if images:
                test_image = images[0]
                break
    
    if not test_image:
        print("⚠️  No test images found. Skipping analysis test.")
        print("   Place a test image in data/ or data/raw_1000/")
        return
    
    print(f"📸 Test Image: {test_image.name}")
    print()
    
    # Simple test prompt
    system_prompt = """You are analyzing a photo. Return a JSON object with:
{
  "description": "Brief description of what you see",
  "confidence": 0.95
}"""
    
    try:
        print("🔄 Analyzing image (this may take a few seconds)...")
        response = await registry.analyze_image(
            image_path=str(test_image),
            system_prompt=system_prompt,
            user_prompt="Describe this image briefly."
        )
        
        print(f"✓ Success!")
        print(f"  Provider: {response.provider}")
        print(f"  Model: {response.model}")
        print(f"  Latency: {response.latency_ms:.0f}ms")
        if response.tokens_used:
            print(f"  Tokens: {response.tokens_used}")
        print()
        print(f"  Response: {response.raw_text[:200]}...")
        print()
        
    except Exception as e:
        print(f"✗ Analysis failed: {e}")
        print()


async def test_statistics():
    """Display provider statistics."""
    print("=" * 60)
    print("PROVIDER STATISTICS")
    print("=" * 60)
    print()
    
    stats = registry.get_stats()
    
    if not stats:
        print("No statistics available yet.")
        return
    
    for provider_name, provider_stats in stats.items():
        print(f"📊 {provider_name}:")
        print(f"  Requests: {provider_stats['requests']}")
        print(f"  Successes: {provider_stats['successes']}")
        print(f"  Failures: {provider_stats['failures']}")
        print(f"  Success Rate: {provider_stats['success_rate']:.1%}")
        if provider_stats['avg_latency_ms'] > 0:
            print(f"  Avg Latency: {provider_stats['avg_latency_ms']:.0f}ms")
        if provider_stats['avg_tokens'] > 0:
            print(f"  Avg Tokens: {provider_stats['avg_tokens']:.0f}")
        print()


async def main():
    """Run all tests."""
    try:
        # Test 1: Initialization and health
        healthy = await test_provider_initialization()
        
        if not healthy:
            print("⚠️  Skipping further tests due to no healthy providers.")
            return
        
        # Test 2: Image analysis (optional)
        await test_image_analysis()
        
        # Test 3: Statistics
        await test_statistics()
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
