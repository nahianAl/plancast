#!/usr/bin/env python3
"""
Test Claude API integration
"""
import os
import sys

def test_claude_api():
    print("🔍 Testing Claude API integration...")
    
    # Check for API key
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('CLAUDE_API_KEY')
    if api_key:
        print(f"✅ API key found: {api_key[:8]}...")
    else:
        print("❌ No API key found in environment variables")
        print("   Set ANTHROPIC_API_KEY or CLAUDE_API_KEY")
        return False
    
    # Test basic import
    try:
        import anthropic
        print(f"✅ Anthropic SDK imported: {anthropic.__version__}")
    except ImportError:
        print("❌ Anthropic SDK not installed")
        print("   Run: pip install anthropic")
        return False
    
    # Test API connection
    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Claude client created successfully")
        
        # Simple test message
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Hello from Claude API!'"}]
        )
        
        print(f"✅ API response received: {response.content[0].text}")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_claude_api()
    sys.exit(0 if success else 1)
