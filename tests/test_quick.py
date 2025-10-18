#!/usr/bin/env python3
"""
Quick test - create a 1-minute sample and test chunking + transcription
"""
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transcription import transcribe_audio

async def test_quick():
    """Create a 1-minute sample and test the pipeline"""
    
    test_file = "recordings/meeting_20251009_125235.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Original file: {test_file}")
    original_size = os.path.getsize(test_file)
    print(f"📊 Original size: {original_size / 1024 / 1024:.2f} MB")
    
    # Create a 1-minute sample for quick testing
    sample_file = "recordings/test_sample_1min.wav"
    print(f"\n🔄 Creating 1-minute sample for quick test...")
    
    cmd = [
        'ffmpeg', '-i', test_file,
        '-t', '60',  # 1 minute
        '-c', 'copy',
        sample_file,
        '-y'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ FFmpeg error: {result.stderr}")
        return
    
    sample_size = os.path.getsize(sample_file)
    print(f"✅ Sample created: {sample_size / 1024 / 1024:.2f} MB")
    
    # Test transcription of the sample
    print(f"\n🔄 Testing transcription of 1-minute sample...")
    print("This should take ~30-60 seconds...")
    
    try:
        transcript = await transcribe_audio(sample_file)
        
        if transcript and transcript.strip():
            print(f"✅ Transcription successful!")
            print(f"📝 Transcript length: {len(transcript)} characters")
            print(f"\n📄 Sample transcript:")
            print("-" * 50)
            print(transcript)
            print("-" * 50)
            
            # Save result
            with open("recordings/test_sample_transcript.txt", 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"💾 Saved to: recordings/test_sample_transcript.txt")
            
        else:
            print("❌ Transcription failed - empty result")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up sample file
    try:
        os.remove(sample_file)
        print(f"🧹 Cleaned up sample file")
    except:
        pass

if __name__ == "__main__":
    print("🧪 Quick Test - 1 Minute Sample")
    print("=" * 40)
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is available")
        else:
            print("❌ FFmpeg not working properly")
    except FileNotFoundError:
        print("❌ FFmpeg not found")
        sys.exit(1)
    
    print()
    asyncio.run(test_quick())

