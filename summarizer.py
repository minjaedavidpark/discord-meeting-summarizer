import os
import logging
from openai import AsyncOpenAI
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))


SUMMARY_PROMPT = """You are an expert meeting note-taker for a startup called PontiFi. 

Analyze the following meeting transcript and provide a comprehensive summary with the following sections:

1. **Meeting Overview**: A brief 2-3 sentence summary of the meeting
2. **Key Discussion Points**: Main topics discussed (bullet points)
3. **Decisions Made**: Important decisions or conclusions reached
4. **Action Items**: Specific tasks assigned, with person responsible if mentioned
5. **Blockers/Issues**: Any obstacles or concerns raised
6. **Next Steps**: What needs to happen next

Keep the summary concise but informative. Focus on actionable insights.

Transcript:
{transcript}
"""


async def summarize_transcript(transcript: str) -> str:
    """
    Generate a structured summary of the meeting transcript
    
    Args:
        transcript: The full meeting transcript
        
    Returns:
        Formatted summary string
    """
    try:
        logger.info(f"Starting summarization of {len(transcript)} character transcript")
        
        if not transcript or len(transcript.strip()) < 50:
            logger.warning("Transcript too short to summarize")
            return "Meeting was too short or no speech detected."
        
        # Generate summary using GPT-4
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Use gpt-4o-mini for cost efficiency, or "gpt-4" for better quality
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at summarizing startup meetings and extracting action items."
                },
                {
                    "role": "user",
                    "content": SUMMARY_PROMPT.format(transcript=transcript)
                }
            ],
            temperature=0.3,  # Lower temperature for more focused, consistent summaries
            max_tokens=1500
        )
        
        summary = response.choices[0].message.content
        
        # Add metadata
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_summary = f"""
Meeting Summary - {timestamp}
{'=' * 60}

{summary}

{'=' * 60}
Transcript Length: {len(transcript)} characters
"""
        
        logger.info("Summarization complete")
        return formatted_summary.strip()
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}", exc_info=True)
        return f"Error generating summary: {str(e)}"


async def extract_action_items(transcript: str) -> list[dict]:
    """
    Extract structured action items from transcript
    
    Args:
        transcript: The meeting transcript
        
    Returns:
        List of action items with assignee and description
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract action items from meeting transcripts. Return as JSON array with 'assignee' and 'task' fields."
                },
                {
                    "role": "user",
                    "content": f"Extract all action items from this transcript:\n\n{transcript}"
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        import json
        action_items = json.loads(response.choices[0].message.content)
        return action_items.get('action_items', [])
        
    except Exception as e:
        logger.error(f"Error extracting action items: {e}", exc_info=True)
        return []

