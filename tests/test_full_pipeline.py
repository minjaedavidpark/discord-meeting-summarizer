#!/usr/bin/env python3
"""
Test the full chunking and transcription pipeline
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transcription import transcribe_audio

async def test_full_pipeline():
    """Test chunking + transcription with the large WAV file"""
    
    test_file = "recordings/meeting_20251009_125235.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    file_size = os.path.getsize(test_file)
    print(f"📁 Test file: {test_file}")
    print(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
    
    print(f"\n🔄 Testing full pipeline (chunking + transcription)...")
    print("⚠️  This will transcribe the entire 25+ minute meeting - it may take 10-15 minutes")
    print("Press Ctrl+C to cancel if you don't want to wait")
    
    try:
        # Test the main transcribe_audio function (which will chunk automatically)
        print("\n" + "="*50)
        print("Starting transcription...")
        print("="*50)
        
        transcript = await transcribe_audio(test_file)
        
        if transcript:
            print(f"\n✅ Full pipeline successful!")
            print(f"📝 Total transcript length: {len(transcript)} characters")
            
            # Show first and last parts
            print(f"\n📄 First 300 characters:")
            print("-" * 40)
            print(transcript[:300])
            print("-" * 40)
            
            print(f"\n📄 Last 300 characters:")
            print("-" * 40)
            print(transcript[-300:])
            print("-" * 40)
            
            # Count chunks in transcript
            chunk_count = transcript.count("[Chunk")
            print(f"\n📊 Found {chunk_count} chunks in transcript")
            
            # Save full transcript
            output_file = "recordings/test_full_transcript.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
            print(f"💾 Full transcript saved to: {output_file}")
            
        else:
            print("❌ Pipeline failed - no transcript returned")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test cancelled by user")
    except Exception as e:
        print(f"❌ Error during pipeline test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Full Chunking + Transcription Pipeline")
    print("=" * 60)
    
    # Check if FFmpeg is available
    import subprocess
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg is available")
        else:
            print("❌ FFmpeg not working properly")
    except FileNotFoundError:
        print("❌ FFmpeg not found - please install it first")
        sys.exit(1)
    
    print()
    
    # Run the test
    asyncio.run(test_full_pipeline())

