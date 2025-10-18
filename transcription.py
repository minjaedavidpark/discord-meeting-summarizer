import os
import logging
import subprocess
import tempfile
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))


async def transcribe_audio(audio_file_path: str, progress_callback=None) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file_path: Path to the audio file
        progress_callback: Optional async callback function(current, total, status_msg)
        
    Returns:
        Transcribed text
    """
    try:
        logger.info(f"Starting transcription of {audio_file_path}")
        
        # Check file exists and size
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found: {audio_file_path}")
            return ""
        
        file_size = os.path.getsize(audio_file_path)
        logger.info(f"Audio file size: {file_size / 1024 / 1024:.2f} MB")
        
        # OpenAI Whisper has a 25MB limit
        if file_size > 25 * 1024 * 1024:
            logger.info("Audio file too large, splitting into chunks...")
            return await transcribe_large_file(audio_file_path, progress_callback)
        
        # Transcribe using Whisper
        with open(audio_file_path, 'rb') as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                language="en"  # Change if your meetings are in another language
            )
        
        transcript = response if isinstance(response, str) else response.text
        
        logger.info(f"Transcription complete: {len(transcript)} characters")
        return transcript
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}", exc_info=True)
        return ""


async def transcribe_large_file(audio_file_path: str, progress_callback=None) -> str:
    """
    Split large audio file into chunks and transcribe each chunk
    
    Args:
        audio_file_path: Path to the large audio file
        progress_callback: Optional async callback function(current, total, status_msg)
        
    Returns:
        Combined transcribed text from all chunks
    """
    try:
        # Create temporary directory for chunks
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Split audio into smaller chunks - use 2 minutes for better reliability
            # For 48kHz stereo WAV: 2 minutes ≈ 10-11MB (safer margin under 25MB limit)
            chunk_duration = 120  # 2 minutes per chunk
            
            logger.info(f"Splitting audio into ~2-minute chunks...")
            
            # Use ffmpeg to split the audio
            chunk_pattern = temp_path / "chunk_%03d.wav"
            cmd = [
                'ffmpeg', '-i', audio_file_path,
                '-f', 'segment', '-segment_time', str(chunk_duration),
                '-c', 'copy', str(chunk_pattern),
                '-y'  # Overwrite output files
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return ""
            
            # Find all chunk files
            chunk_files = sorted(temp_path.glob("chunk_*.wav"))
            logger.info(f"Created {len(chunk_files)} chunks")
            
            if not chunk_files:
                logger.error("No chunks created")
                return ""
            
            # Transcribe each chunk with retry logic
            all_transcripts = []
            for i, chunk_file in enumerate(chunk_files):
                chunk_size = os.path.getsize(chunk_file)
                logger.info(f"Transcribing chunk {i+1}/{len(chunk_files)}: {chunk_file.name} ({chunk_size / 1024 / 1024:.2f} MB)")
                
                if progress_callback:
                    try:
                        await progress_callback(i+1, len(chunk_files), f"Processing chunk {i+1}/{len(chunk_files)}...")
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
                
                # Double-check chunk size before sending to OpenAI
                if chunk_size > 25 * 1024 * 1024:
                    logger.warning(f"Chunk {i+1} is still too large ({chunk_size / 1024 / 1024:.2f} MB), skipping...")
                    continue
                
                # Retry logic for each chunk
                max_retries = 3
                retry_delay = 5
                
                for attempt in range(max_retries):
                    try:
                        # Add timeout to prevent hanging
                        import asyncio
                        
                        async def transcribe_chunk():
                            with open(chunk_file, 'rb') as audio_file:
                                response = await client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    response_format="text",
                                    language="en",
                                    timeout=300.0  # 5 minute timeout per chunk
                                )
                            return response
                        
                        # Run with timeout
                        response = await asyncio.wait_for(transcribe_chunk(), timeout=360.0)  # 6 min total timeout
                        
                        chunk_transcript = response if isinstance(response, str) else response.text
                        if chunk_transcript.strip():
                            all_transcripts.append(chunk_transcript.strip())
                            logger.info(f"Chunk {i+1} transcribed: {len(chunk_transcript)} characters")
                            break  # Success, exit retry loop
                        else:
                            logger.warning(f"Chunk {i+1} produced empty transcript")
                            if attempt < max_retries - 1:
                                logger.info(f"Retrying chunk {i+1} (attempt {attempt + 2}/{max_retries})...")
                                await asyncio.sleep(retry_delay)
                            
                    except asyncio.TimeoutError:
                        logger.error(f"Timeout transcribing chunk {i+1} (attempt {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying chunk {i+1} after timeout...")
                            await asyncio.sleep(retry_delay)
                        else:
                            logger.error(f"Chunk {i+1} failed after {max_retries} attempts")
                            
                    except Exception as e:
                        logger.error(f"Error transcribing chunk {i+1} (attempt {attempt + 1}/{max_retries}): {e}")
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying chunk {i+1}...")
                            await asyncio.sleep(retry_delay)
                        else:
                            logger.error(f"Chunk {i+1} failed after {max_retries} attempts")
            
            if not all_transcripts:
                logger.error("No chunks were successfully transcribed")
                return ""
            
            # Combine all transcripts (removed chunk markers for cleaner output)
            combined_transcript = "\n\n".join(all_transcripts)
            logger.info(f"Combined transcription complete: {len(combined_transcript)} characters from {len(all_transcripts)}/{len(chunk_files)} chunks")
            return combined_transcript
            
    except Exception as e:
        logger.error(f"Error in large file transcription: {e}", exc_info=True)
        return ""


async def transcribe_with_timestamps(audio_file_path: str) -> dict:
    """
    Transcribe audio with timestamps for more detailed analysis
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Dict with detailed transcription data including timestamps
    """
    try:
        logger.info(f"Starting timestamped transcription of {audio_file_path}")
        
        with open(audio_file_path, 'rb') as audio_file:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                language="en",
                timestamp_granularities=["segment"]
            )
        
        logger.info(f"Timestamped transcription complete")
        return response
        
    except Exception as e:
        logger.error(f"Error in timestamped transcription: {e}", exc_info=True)
        return {}

