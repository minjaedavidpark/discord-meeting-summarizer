import discord
from discord.ext import commands, tasks, voice_recv
import asyncio
import os
import wave
import io
from datetime import datetime, time
from pathlib import Path
from typing import Optional
import logging
import aiohttp
import tempfile

from audio_recorder import MeetingRecorder
from transcription import transcribe_audio
from summarizer import summarize_transcript

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# Reduce discord.py's verbosity but keep our modules at DEBUG
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('discord.gateway').setLevel(logging.INFO)
logging.getLogger('discord.ext.voice_recv').setLevel(logging.INFO)

# Load Opus library for voice recording
if not discord.opus.is_loaded():
    try:
        # Try common locations for libopus
        discord.opus.load_opus('opus')
        logger.info("Loaded opus library")
    except:
        try:
            discord.opus.load_opus('libopus.so.0')
        except:
            try:
                discord.opus.load_opus('/opt/homebrew/lib/libopus.dylib')
                logger.info("Loaded opus from homebrew")
            except Exception as e:
                logger.warning(f"Could not load opus: {e}")
                logger.warning("Voice recording may not work without opus!")

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Global state
is_recording = False
current_recorder: Optional[MeetingRecorder] = None
recording_channel = None


@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guild(s)')
    
    # Start scheduled recording task if configured
    meeting_time = os.getenv('MEETING_TIME')
    if meeting_time:
        scheduled_recording.start()
        logger.info(f'Scheduled recording enabled for {meeting_time}')


@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Debug: Log all messages from Craig to see the format
    if message.author.name == "Craig" or message.author.bot:
        logger.info(f"Bot message from {message.author.name} (ID: {message.author.id})")
        logger.info(f"Content: {message.content}")
        logger.info(f"Embeds: {len(message.embeds)}")
        if message.embeds:
            for embed in message.embeds:
                logger.info(f"Embed description: {embed.description}")
    
    # Check if it's a message from Craig with a recording
    # Craig's bot name might be different, so check content too
    is_craig = message.author.name == "Craig" or (message.author.bot and "craig" in message.author.name.lower())
    has_recording_link = "craig.chat/rec/" in message.content or "craig.horse" in message.content
    
    # Also check embeds for the link
    if message.embeds and not has_recording_link:
        for embed in message.embeds:
            if embed.description and ("craig.chat/rec/" in embed.description or "craig.horse" in embed.description):
                has_recording_link = True
                break
    
    if is_craig and has_recording_link:
        logger.info(f"✅ Detected Craig recording message!")
        
        # Extract recording ID from Craig's message
        import re
        recording_id_match = re.search(r'craig\.chat/rec/([A-Za-z0-9]+)', message.content)
        
        if recording_id_match:
            recording_id = recording_id_match.group(1)
            
            # Try to find download link in the message
            # Craig usually provides buttons/links, but we can construct the direct link
            flac_url = f"https://craig.horse/rec/{recording_id}.flac"
            
            await message.channel.send(f"🎙️ Detected Craig recording! Processing automatically...")
            
            # Create a mock context for process_url
            class MockContext:
                def __init__(self, channel):
                    self.channel = channel
                
                async def send(self, content):
                    return await self.channel.send(content)
            
            mock_ctx = MockContext(message.channel)
            processing_msg = await message.channel.send("📥 Downloading recording...")
            
            try:
                # Download and process
                recordings_dir = Path("recordings")
                recordings_dir.mkdir(exist_ok=True)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(flac_url) as response:
                        if response.status == 200:
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            audio_filename = f"recordings/meeting_{timestamp}.flac"
                            
                            with open(audio_filename, 'wb') as f:
                                while True:
                                    chunk = await response.content.read(8192)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                            
                            logger.info(f"Auto-downloaded Craig recording: {audio_filename}")
                            await processing_msg.edit(content="🎙️ Download complete! Transcribing...")
                            
                            # Process the audio
                            await process_audio_file(mock_ctx, processing_msg, audio_filename, timestamp)
                        else:
                            await processing_msg.edit(content=f"❌ Couldn't download recording (HTTP {response.status})")
                            
            except Exception as e:
                logger.error(f"Error auto-processing Craig recording: {e}", exc_info=True)
                await processing_msg.edit(content=f"❌ Error: {str(e)}")
    
    # Process commands
    await bot.process_commands(message)


@bot.command(name='join', help='Join voice channel and start recording')
async def join(ctx):
    """Join the voice channel and start recording"""
    global is_recording, current_recorder, recording_channel
    
    if not ctx.author.voice:
        await ctx.send("❌ You need to be in a voice channel first!")
        return
    
    if is_recording:
        await ctx.send("⚠️ Already recording! Use `!stop` to end the current recording.")
        return
    
    channel = ctx.author.voice.channel
    recording_channel = ctx.channel
    
    try:
        # Join voice channel with voice_recv support
        if ctx.voice_client is not None:
            voice_client = ctx.voice_client
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
        
        # Create recordings directory
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        # Start recording
        current_recorder = MeetingRecorder()
        voice_client.listen(current_recorder)
        
        is_recording = True
        
        await ctx.send(f"🔴 **Recording started** in {channel.name}!\n💡 Use `!stop` when done to get your summary.")
        logger.info(f"Started recording in {channel.name}")
        
    except Exception as e:
        logger.error(f"Error starting recording: {e}", exc_info=True)
        await ctx.send(f"❌ Error starting recording: {str(e)}")


@bot.command(name='stop', help='Stop recording and generate summary')
async def stop(ctx):
    """Stop recording and process the audio"""
    global is_recording, current_recorder, recording_channel
    
    if not is_recording:
        await ctx.send("❌ Not currently recording! Use `!join` to start.")
        return
    
    if ctx.voice_client is None:
        await ctx.send("❌ Not in a voice channel!")
        is_recording = False
        return
    
    processing_msg = await ctx.send("⏹️ Stopping recording and processing...")
    
    try:
        # Save the recording BEFORE stopping (stop_listening clears the data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audio_filename = f"recordings/meeting_{timestamp}.wav"
        
        if current_recorder and current_recorder.audio_data:
            success = current_recorder.save_to_file(audio_filename)
            
            # Now stop listening
            ctx.voice_client.stop_listening()
            is_recording = False
            
            if success:
                logger.info(f"Saved recording to {audio_filename}")
                await processing_msg.edit(content="🎙️ Recording saved! Transcribing...")
                
                # Process the audio
                await process_audio_file(ctx, processing_msg, audio_filename, timestamp)
            else:
                await processing_msg.edit(content="❌ Failed to save recording!")
        else:
            # Stop listening even if no data
            ctx.voice_client.stop_listening()
            is_recording = False
            await processing_msg.edit(content="❌ No audio data recorded! Make sure people spoke during the meeting.")
            logger.warning("No audio data in recorder")
        
        # Cleanup
        if current_recorder:
            current_recorder.cleanup()
        current_recorder = None
        
        # Disconnect from voice channel
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            logger.info("Disconnected from voice channel")
        
    except Exception as e:
        logger.error(f"Error stopping recording: {e}", exc_info=True)
        await processing_msg.edit(content=f"❌ Error processing recording: {str(e)}")
        is_recording = False
        current_recorder = None
        # Try to disconnect even on error
        if ctx.voice_client:
            await ctx.voice_client.disconnect()


@bot.command(name='leave', help='Leave the voice channel')
async def leave(ctx):
    """Disconnect from the voice channel"""
    global is_recording, current_recorder
    
    if ctx.voice_client is None:
        await ctx.send("❌ I'm not in a voice channel!")
        return
    
    if is_recording:
        await ctx.send("⚠️ Recording in progress! Use `!stop` first to save the recording.")
        return
    
    await ctx.voice_client.disconnect()
    await ctx.send("✅ Disconnected from voice channel")


async def process_audio_file(ctx, processing_msg, audio_filename: str, timestamp: str):
    """Helper function to process an audio file"""
    try:
        # Transcribe the audio
        transcript = await transcribe_audio(audio_filename)
        
        if transcript:
            transcript_filename = f"recordings/transcript_{timestamp}.txt"
            with open(transcript_filename, 'w', encoding='utf-8') as f:
                f.write(transcript)
            
            await processing_msg.edit(content="📝 Transcription complete! Generating summary...")
            
            # Generate summary
            summary = await summarize_transcript(transcript)
            
            # Save summary
            summary_filename = f"recordings/summary_{timestamp}.txt"
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write(summary)
            
            # Send summary to Discord (split if too long)
            await processing_msg.edit(content="✅ Processing complete!")
            
            # Send summary in chunks if needed
            summary_parts = split_message(summary, 1900)
            for i, part in enumerate(summary_parts):
                if i == 0:
                    await ctx.send(f"📊 **Meeting Summary**\n```\n{part}\n```")
                else:
                    await ctx.send(f"```\n{part}\n```")

            # Post summary to forum channel 'daily-meeting-logs'
            try:
                guild = getattr(ctx, 'guild', None) or getattr(getattr(ctx, 'channel', None), 'guild', None)
                if guild is not None:
                    today_title = datetime.now().strftime('%Y-%m-%d %H:%M')
                    await post_summary_to_forum(guild, forum_name='daily-meeting-logs', title=today_title, summary_text=summary)
                    logger.info("Posted summary to forum 'daily-meeting-logs'")
                else:
                    logger.warning("Could not resolve guild from context for forum posting")
            except Exception as e:
                logger.error(f"Failed to post summary to forum: {e}", exc_info=True)
            
            logger.info(f"Meeting processed successfully: {timestamp}")
        else:
            await processing_msg.edit(content="❌ Transcription failed!")
            logger.error("Transcription returned empty")
            
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        await processing_msg.edit(content=f"❌ Error: {str(e)}")


@bot.command(name='upload', help='Upload and process a meeting recording')
async def upload(ctx):
    """Process an uploaded audio file"""
    if not ctx.message.attachments:
        await ctx.send("❌ Please attach an audio file (mp3, wav, m4a, flac, ogg, etc.)")
        return
    
    attachment = ctx.message.attachments[0]
    
    # Check if it's an audio file
    audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.webm']
    if not any(attachment.filename.lower().endswith(ext) for ext in audio_extensions):
        await ctx.send("❌ Please upload an audio file (.mp3, .wav, .m4a, etc.)")
        return
    
    processing_msg = await ctx.send("📥 Downloading recording...")
    
    try:
        # Create recordings directory
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        # Download the file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_extension = Path(attachment.filename).suffix
        audio_filename = f"recordings/meeting_{timestamp}{file_extension}"
        
        await attachment.save(audio_filename)
        logger.info(f"Downloaded audio file: {audio_filename}")
        
        await processing_msg.edit(content="🎙️ Recording saved! Transcribing...")
        
        # Process the audio file
        await process_audio_file(ctx, processing_msg, audio_filename, timestamp)
        
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        await processing_msg.edit(content=f"❌ Error processing recording: {str(e)}")


@bot.command(name='help_recording', help='Show how to record meetings')
async def help_recording(ctx):
    """Show instructions for recording meetings"""
    help_text = """
📹 **How to Record Discord Meetings**

**🎙️ Direct Recording (Fully Automated!)**
1. `!join` - Bot joins your voice channel and starts recording
2. Have your meeting (speak normally!)
3. `!stop` - Bot stops, transcribes, and posts summary

That's it! Completely automated, no downloads needed!

**Alternative: Manual Upload**
If you recorded separately (OBS, QuickTime, etc.):
• Use `!upload` and attach your audio file
• Supported formats: MP3, WAV, M4A, FLAC, OGG

**Available Commands:**
• `!join` - Bot joins and starts recording
• `!stop` - Stop recording and get summary
• `!leave` - Bot leaves voice channel
• `!upload` - Upload a pre-recorded audio file

The bot will:
✅ Record in high quality (48kHz)
✅ Transcribe using Whisper AI
✅ Generate summary with action items
✅ Identify key decisions and blockers
✅ Post everything in this channel
"""
    await ctx.send(help_text)


@tasks.loop(minutes=1)
async def scheduled_recording():
    """Check if it's time for the scheduled meeting"""
    meeting_time_str = os.getenv('MEETING_TIME')
    if not meeting_time_str:
        return
    
    try:
        # Parse meeting time
        hour, minute = map(int, meeting_time_str.split(':'))
        meeting_time_obj = time(hour, minute)
        
        # Check if current time matches
        now = datetime.now().time()
        if now.hour == meeting_time_obj.hour and now.minute == meeting_time_obj.minute:
            await auto_start_recording()
    except Exception as e:
        logger.error(f"Error in scheduled recording: {e}")


async def auto_start_recording():
    """Automatically join voice channel at scheduled time"""
    try:
        guild_id = int(os.getenv('DISCORD_GUILD_ID'))
        channel_id = int(os.getenv('DISCORD_VOICE_CHANNEL_ID'))
        
        guild = bot.get_guild(guild_id)
        if not guild:
            logger.error(f"Guild {guild_id} not found")
            return
        
        channel = guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.VoiceChannel):
            logger.error(f"Voice channel {channel_id} not found")
            return
        
        # Join if not already in
        voice_client = guild.voice_client
        if voice_client is None:
            voice_client = await channel.connect()
        
        # Find text channel to send messages
        text_channel = discord.utils.get(guild.text_channels, name='general')
        if not text_channel:
            text_channel = guild.text_channels[0]
        
        await text_channel.send("🎙️ Meeting time! I've joined the voice channel. Use `!help_recording` to learn how to record and process meetings.")
        
        logger.info("Auto-joined voice channel for scheduled meeting")
        
    except Exception as e:
        logger.error(f"Error auto-joining channel: {e}", exc_info=True)


def split_message(text: str, max_length: int = 1900) -> list[str]:
    """Split a long message into chunks"""
    if len(text) <= max_length:
        return [text]
    
    parts = []
    while text:
        if len(text) <= max_length:
            parts.append(text)
            break
        
        # Try to split at newline
        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        
        parts.append(text[:split_pos])
        text = text[split_pos:].lstrip()
    
    return parts


async def post_summary_to_forum(guild: discord.Guild, forum_name: str, title: str, summary_text: str):
    """Create a new post in the specified forum with the given title and summary text.

    If the summary exceeds the message limit, the first chunk is used as the
    initial post content and remaining chunks are replied in the created thread.
    """
    # Find forum channel by name
    forum_channel = discord.utils.get(guild.channels, name=forum_name)
    if forum_channel is None or not isinstance(forum_channel, discord.ForumChannel):
        raise RuntimeError(f"Forum channel '{forum_name}' not found or is not a ForumChannel")

    parts = split_message(summary_text, 1900)
    first_content = parts[0]

    # Create the thread with the first part as the initial message
    created = await forum_channel.create_thread(name=title, content=first_content)
    thread = created.thread if hasattr(created, 'thread') else created

    # Post remaining parts as follow-up messages in the thread
    if len(parts) > 1:
        for part in parts[1:]:
            await thread.send(part)

def main():
    """Main entry point"""
    from dotenv import load_dotenv
    load_dotenv()
    
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables!")
        return
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)


if __name__ == '__main__':
    main()

