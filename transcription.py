import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))


async def transcribe_audio(audio_file_path: str) -> str:
    """
    Transcribe audio file using OpenAI Whisper API
    
    Args:
        audio_file_path: Path to the audio file
        
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
            logger.warning("Audio file too large, may need to split")
            # TODO: Implement file splitting for large files
        
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

