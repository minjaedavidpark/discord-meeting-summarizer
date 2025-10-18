#!/usr/bin/env python3
"""
Manually process a saved recording file
Usage: python process_recording.py <audio_file_path>
"""

import asyncio
import sys
from pathlib import Path
from transcription import transcribe_audio
from summarizer import summarize_transcript


async def process_recording(audio_file_path: str):
    """Process a recording file and save transcript and summary"""
    
    print(f"🎙️ Processing: {audio_file_path}")
    
    # Progress callback for terminal output
    async def show_progress(current: int, total: int, status: str):
        progress_bar = "▓" * current + "░" * (total - current)
        print(f"\r🎙️ Transcribing... [{progress_bar}] {current}/{total} chunks - {status}", end="", flush=True)
    
    # Transcribe
    print("Starting transcription...")
    transcript = await transcribe_audio(audio_file_path, progress_callback=show_progress)
    print()  # New line after progress
    
    if not transcript or not transcript.strip():
        print("❌ Transcription failed!")
        return
    
    # Save transcript
    base_name = Path(audio_file_path).stem
    transcript_path = f"recordings/{base_name}_transcript.txt"
    with open(transcript_path, 'w', encoding='utf-8') as f:
        f.write(transcript)
    print(f"✅ Transcript saved to: {transcript_path}")
    print(f"   ({len(transcript)} characters)")
    
    # Generate summary
    print("\n📝 Generating summary...")
    summary = await summarize_transcript(transcript)
    
    if not summary or not summary.strip():
        print("❌ Summary generation failed!")
        return
    
    # Save summary
    summary_path = f"recordings/{base_name}_summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)
    print(f"✅ Summary saved to: {summary_path}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("📊 MEETING SUMMARY")
    print("="*80)
    print(summary)
    print("="*80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python process_recording.py <audio_file_path>")
        print("\nExample:")
        print("  python process_recording.py recordings/meeting_20251010_124319.wav")
        sys.exit(1)
    
    audio_file = sys.argv[1]
    
    if not Path(audio_file).exists():
        print(f"❌ File not found: {audio_file}")
        sys.exit(1)
    
    # Run async processing
    asyncio.run(process_recording(audio_file))


if __name__ == "__main__":
    main()

