#!/usr/bin/env python3
"""
Generate summary from an existing transcript file
Usage: python summarize_transcript.py <transcript_file_path>
"""

import asyncio
import sys
from pathlib import Path
from summarizer import summarize_transcript


async def summarize_file(transcript_path: str):
    """Read transcript file and generate summary"""
    
    print(f"📄 Reading transcript: {transcript_path}")
    
    # Read transcript
    try:
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    if not transcript or len(transcript.strip()) < 50:
        print("❌ Transcript is too short or empty!")
        return
    
    print(f"📝 Transcript loaded: {len(transcript)} characters")
    print(f"📊 Generating summary...")
    
    # Generate summary
    summary = await summarize_transcript(transcript)
    
    if not summary or not summary.strip():
        print("❌ Summary generation failed!")
        return
    
    # Save summary
    base_name = Path(transcript_path).stem
    # Remove _transcript suffix if present
    if base_name.endswith('_transcript'):
        base_name = base_name[:-11]
    
    summary_path = f"recordings/{base_name}_summary.txt"
    
    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"✅ Summary saved to: {summary_path}")
    except Exception as e:
        print(f"⚠️ Could not save summary: {e}")
        print("Summary generated but not saved.")
    
    # Print summary to console
    print("\n" + "="*80)
    print(summary)
    print("="*80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python summarize_transcript.py <transcript_file_path>")
        print("\nExample:")
        print("  python summarize_transcript.py recordings/transcript_20251010_124319.txt")
        print("\nNote: This script only generates summaries from existing transcripts.")
        print("      Use process_recording.py if you need to transcribe audio first.")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    
    if not Path(transcript_file).exists():
        print(f"❌ File not found: {transcript_file}")
        sys.exit(1)
    
    # Run async summarization
    asyncio.run(summarize_file(transcript_file))


if __name__ == "__main__":
    main()

