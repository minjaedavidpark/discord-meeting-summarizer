#!/usr/bin/env python3
"""
Test configuration and verify all required credentials are set up correctly.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv


def test_env_file():
    """Check if .env file exists"""
    if not Path('.env').exists():
        print("❌ .env file not found!")
        print("   Run: cp .env.example .env")
        return False
    print("✅ .env file exists")
    return True


def test_discord_token():
    """Test Discord bot token"""
    load_dotenv()
    token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not token:
        print("❌ DISCORD_BOT_TOKEN not set in .env")
        return False
    
    if len(token) < 50:
        print("⚠️  DISCORD_BOT_TOKEN seems too short")
        return False
    
    print(f"✅ Discord bot token configured ({len(token)} chars)")
    return True


def test_openai_key():
    """Test OpenAI API key"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("❌ OPENAI_API_KEY not set in .env")
        return False
    
    if not api_key.startswith('sk-'):
        print("⚠️  OPENAI_API_KEY format looks incorrect (should start with 'sk-')")
        return False
    
    print(f"✅ OpenAI API key configured")
    return True


def test_optional_config():
    """Check optional configuration"""
    guild_id = os.getenv('DISCORD_GUILD_ID')
    channel_id = os.getenv('DISCORD_VOICE_CHANNEL_ID')
    meeting_time = os.getenv('MEETING_TIME')
    
    if not guild_id or not channel_id:
        print("⚠️  Optional: DISCORD_GUILD_ID and DISCORD_VOICE_CHANNEL_ID not set")
        print("   Scheduled recordings won't work without these")
    else:
        print("✅ Discord IDs configured for scheduled recordings")
    
    if meeting_time:
        print(f"✅ Scheduled recording time: {meeting_time}")
    else:
        print("⚠️  Optional: MEETING_TIME not set (manual recording only)")
    
    return True


def test_dependencies():
    """Test required dependencies"""
    try:
        import discord
        print(f"✅ discord.py installed (version {discord.__version__})")
    except ImportError:
        print("❌ discord.py not installed")
        print("   Run: pip install -r requirements.txt")
        return False
    
    try:
        import openai
        print(f"✅ openai installed")
    except ImportError:
        print("❌ openai not installed")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True


def test_recordings_dir():
    """Check recordings directory"""
    recordings_dir = Path('recordings')
    if not recordings_dir.exists():
        print("⚠️  Creating recordings directory...")
        recordings_dir.mkdir(exist_ok=True)
    print("✅ Recordings directory ready")
    return True


def main():
    """Run all tests"""
    print("🔍 Testing Discord Meeting Summarizer configuration...\n")
    
    tests = [
        ("Environment File", test_env_file),
        ("Discord Token", test_discord_token),
        ("OpenAI API Key", test_openai_key),
        ("Optional Config", test_optional_config),
        ("Dependencies", test_dependencies),
        ("Recordings Directory", test_recordings_dir),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(False)
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed! ({passed}/{total})")
        print("\n🚀 You're ready to run the bot!")
        print("   Run: python bot.py")
        return 0
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("\n⚠️  Please fix the issues above before running the bot")
        return 1


if __name__ == '__main__':
    sys.exit(main())

