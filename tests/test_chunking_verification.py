#!/usr/bin/env python3
"""
Test chunking with a 6-minute sample (should create 2 chunks)
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

async def test_chunking_verification():
    """Create a 6-minute sample to test chunking (should create 2 chunks)"""
    
    test_file = "recordings/meeting_20251009_125235.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print(f"📁 Original file: {test_file}")
    original_size = os.path.getsize(test_file)
    print(f"📊 Original size: {original_size / 1024 / 1024:.2f} MB")
    
    # Create a 6-minute sample (should create 2 chunks of ~3 minutes each)
    sample_file = "recordings/test_sample_6min.wav"
    print(f"\n🔄 Creating 6-minute sample to test chunking...")
    
    cmd = [
        'ffmpeg', '-i', test_file,
        '-t', '360',  # 6 minutes
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
    
    # This should trigger chunking since it's over 25MB
    if sample_size > 25 * 1024 * 1024:
        print(f"ℹ️  Sample is over 25MB - will test chunking")
    else:
        print(f"ℹ️  Sample is under 25MB - will use direct transcription")
    
    # Test transcription (should use chunking)
    print(f"\n🔄 Testing transcription with chunking...")
    print("This should take ~2-3 minutes...")
    
    try:
        transcript = await transcribe_audio(sample_file)
        
        if transcript and transcript.strip():
            print(f"✅ Transcription successful!")
            print(f"📝 Transcript length: {len(transcript)} characters")
            
            # Check for chunk markers
            chunk_count = transcript.count("[Chunk")
            print(f"📊 Found {chunk_count} chunks in transcript")
            
            if chunk_count > 0:
                print(f"✅ Chunking worked! Found {chunk_count} chunks")
            else:
                print(f"ℹ️  No chunk markers found - used direct transcription")
            
            print(f"\n📄 First 300 characters:")
            print("-" * 50)
            print(transcript[:300])
            print("-" * 50)
            
            # Save result
            with open("recordings/test_chunking_transcript.txt", 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"💾 Saved to: recordings/test_chunking_transcript.txt")
            
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
    print("🧪 Chunking Verification Test - 6 Minute Sample")
    print("=" * 55)
    
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
    asyncio.run(test_chunking_verification())

