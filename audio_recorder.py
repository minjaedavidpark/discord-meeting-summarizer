import discord
from discord.ext import voice_recv
import wave
import io
import struct
from typing import Dict
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MeetingRecorder(voice_recv.AudioSink):
    """Audio sink for recording Discord voice channels"""
    
    def __init__(self):
        super().__init__()
        self.audio_data: Dict[int, bytearray] = {}
        self.user_names: Dict[int, str] = {}
        self.sample_rate = 48000  # Discord's sample rate
        self.channels = 2  # Stereo
        self.sample_width = 2  # 16-bit audio
        logger.info("MeetingRecorder initialized")
    
    def wants_opus(self) -> bool:
        """We want decoded PCM audio, not Opus"""
        return False
    
    def write(self, user, data):
        """Called when audio data is received from a user"""
        if user.id not in self.audio_data:
            self.audio_data[user.id] = bytearray()
            self.user_names[user.id] = user.display_name
            logger.info(f"Started recording user: {user.display_name} ({user.id})")
        
        # Append PCM audio data
        if hasattr(data, 'pcm') and data.pcm:
            self.audio_data[user.id].extend(data.pcm)
            logger.debug(f"Wrote {len(data.pcm)} bytes from {user.display_name}")
        else:
            logger.warning(f"No PCM data in packet from {user.display_name}, data type: {type(data)}, has pcm: {hasattr(data, 'pcm')}")
    
    def save_to_file(self, filename: str):
        """Save all recorded audio to a WAV file, mixing all users"""
        if not self.audio_data:
            logger.warning("No audio data to save")
            return False
        
        try:
            logger.info(f"Saving recording with {len(self.audio_data)} users")
            
            # Log audio data sizes
            for user_id, data in self.audio_data.items():
                logger.info(f"User {self.user_names.get(user_id, user_id)}: {len(data)} bytes")
            
            # Find the longest recording to determine output length
            non_empty_data = [data for data in self.audio_data.values() if len(data) > 0]
            if not non_empty_data:
                logger.warning("All audio data is empty")
                return False
            
            max_length = max(len(data) for data in non_empty_data)
            
            # Mix all audio streams
            # Each sample is 2 bytes (16-bit), so divide by 2 for sample count
            sample_count = max_length // 2
            mixed_samples = [0] * sample_count
            
            # Mix all user audio
            user_count = len(self.audio_data)
            for user_id, audio_bytes in self.audio_data.items():
                # Convert bytes to samples (16-bit signed integers)
                sample_index = 0
                for i in range(0, len(audio_bytes), 2):
                    if i + 1 < len(audio_bytes):
                        # Unpack 16-bit signed integer (little-endian)
                        sample = struct.unpack('<h', audio_bytes[i:i+2])[0]
                        if sample_index < sample_count:
                            # Add to mix (we'll normalize later)
                            mixed_samples[sample_index] += sample
                            sample_index += 1
            
            # Normalize mixed audio to prevent clipping
            # Divide by number of users to average the volume
            if user_count > 1:
                mixed_samples = [int(s / user_count) for s in mixed_samples]
            
            # Convert back to bytes
            mixed_bytes = bytearray()
            for sample in mixed_samples:
                # Clamp to 16-bit range
                sample = max(-32768, min(32767, sample))
                mixed_bytes.extend(struct.pack('<h', sample))
            
            # Save as WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono (already mixed)
                wav_file.setsampwidth(self.sample_width)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(bytes(mixed_bytes))
            
            file_size = len(mixed_bytes) / 1024 / 1024  # MB
            duration = len(mixed_samples) / self.sample_rate  # seconds
            
            logger.info(f"Saved {file_size:.2f} MB, duration: {duration:.1f}s")
            logger.info(f"Recorded users: {list(self.user_names.values())}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio file: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """Clean up resources"""
        logger.info(f"Cleaning up recorder (recorded {len(self.audio_data)} users)")
        self.audio_data.clear()
        self.user_names.clear()
