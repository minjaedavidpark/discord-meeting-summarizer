#!/usr/bin/env python3
"""
Test chunking and transcribe only the first chunk to verify pipeline works
"""
import asyncio
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from transcription import transcribe_large_file

async def test_first_chunk():
    """Test chunking and transcribe only the first chunk"""
    
    test_file = "recordings/meeting_20251009_125235.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    file_size = os.path.getsize(test_file)
    print(f"📁 Test file: {test_file}")
    print(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
    
    # Create temporary directory for chunks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        chunk_duration = 240  # 4 minutes per chunk
        
        print(f"\n🔄 Step 1: Splitting audio into ~4-minute chunks...")
        
        # Use ffmpeg to split the audio
        chunk_pattern = temp_path / "chunk_%03d.wav"
        cmd = [
            'ffmpeg', '-i', test_file,
            '-f', 'segment', '-segment_time', str(chunk_duration),
            '-c', 'copy', str(chunk_pattern),
            '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ FFmpeg error: {result.stderr}")
            return
        
        # Find all chunk files
        chunk_files = sorted(temp_path.glob("chunk_*.wav"))
        print(f"✅ Created {len(chunk_files)} chunks")
        
        if not chunk_files:
            print("❌ No chunks created")
            return
        
        # Check chunk sizes
        print(f"\n📊 Chunk sizes:")
        for i, chunk_file in enumerate(chunk_files):
            chunk_size = os.path.getsize(chunk_file)
            size_mb = chunk_size / 1024 / 1024
            status = "✅" if chunk_size < 25 * 1024 * 1024 else "❌"
            print(f"  {status} Chunk {i+1}: {size_mb:.2f} MB")
        
        # Test transcription of first chunk only
        first_chunk = chunk_files[0]
        print(f"\n🔄 Step 2: Testing transcription of first chunk only...")
        print(f"📁 Transcribing: {first_chunk.name}")
        
        try:
            from openai import AsyncOpenAI
            from dotenv import load_dotenv
            load_dotenv()
            
            client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            
            with open(first_chunk, 'rb') as audio_file:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                    language="en"
                )
            
            transcript = response if isinstance(response, str) else response.text
            
            if transcript and transcript.strip():
                print(f"✅ First chunk transcription successful!")
                print(f"📝 Transcript length: {len(transcript)} characters")
                print(f"\n📄 First chunk transcript:")
                print("-" * 50)
                print(transcript[:500])
                print("-" * 50)
                
                # Save test result
                with open("recordings/test_first_chunk.txt", 'w', encoding='utf-8') as f:
                    f.write(transcript)
                print(f"💾 Saved to: recordings/test_first_chunk.txt")
                
            else:
                print("❌ First chunk transcription failed - empty result")
                
        except Exception as e:
            print(f"❌ Error transcribing first chunk: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing Chunking + First Chunk Transcription")
    print("=" * 60)
    
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
    asyncio.run(test_first_chunk())

