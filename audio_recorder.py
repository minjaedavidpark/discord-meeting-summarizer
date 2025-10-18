import discord
from discord.ext import voice_recv
import wave
import io
import struct
from typing import Dict, Optional
import logging
from pathlib import Path
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class MeetingRecorder(voice_recv.AudioSink):
    """Audio sink for recording Discord voice channels"""
    
    def __init__(self):
        super().__init__()
        self.audio_data: Dict[int, bytearray] = {}
        self.user_names: Dict[int, str] = {}
        self.sample_rate = 48000  # Discord's sample rate
        self.channels = 2  # Discord sends stereo (we convert to mono when saving)
        self.sample_width = 2  # 16-bit audio
        self.last_audio_time = datetime.now()
        self.start_time = datetime.now()
        self.total_bytes_received = 0
        self.is_stopped = False
        self.error_callback: Optional[callable] = None
        logger.info("MeetingRecorder initialized")
    
    def wants_opus(self) -> bool:
        """We want decoded PCM audio, not Opus"""
        return False
    
    def set_error_callback(self, callback):
        """Set a callback to be called on errors"""
        self.error_callback = callback
    
    def write(self, user, data):
        """Called when audio data is received from a user"""
        if self.is_stopped:
            return
        
        try:
            if user.id not in self.audio_data:
                self.audio_data[user.id] = bytearray()
                self.user_names[user.id] = user.display_name
                logger.info(f"Started recording user: {user.display_name} ({user.id})")
            
            # Append PCM audio data
            if hasattr(data, 'pcm') and data.pcm:
                self.audio_data[user.id].extend(data.pcm)
                self.total_bytes_received += len(data.pcm)
                self.last_audio_time = datetime.now()
                logger.debug(f"Wrote {len(data.pcm)} bytes from {user.display_name}")
            else:
                logger.warning(f"No PCM data in packet from {user.display_name}, data type: {type(data)}, has pcm: {hasattr(data, 'pcm')}")
        except Exception as e:
            logger.error(f"Error in write() method: {e}", exc_info=True)
            if self.error_callback:
                try:
                    asyncio.create_task(self.error_callback(e))
                except Exception as callback_error:
                    logger.error(f"Error calling error callback: {callback_error}")
    
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
            
            # Discord sends STEREO PCM data (2 channels interleaved)
            # Each frame is 4 bytes: 2 bytes for left channel, 2 bytes for right channel
            # We need to convert stereo to mono by averaging the channels
            
            # Calculate mono sample count (stereo has twice as many samples)
            mono_sample_count = max_length // 4  # 4 bytes per stereo frame
            
            logger.info(f"Mixing {len(self.audio_data)} users into {mono_sample_count} samples ({mono_sample_count/self.sample_rate:.2f} seconds)")
            
            # First, convert each user's audio to mono samples
            user_samples = {}
            for user_id, audio_bytes in self.audio_data.items():
                user_mono = []
                for i in range(0, len(audio_bytes), 4):  # 4 bytes per stereo frame
                    if i + 3 < len(audio_bytes):
                        # Unpack stereo frame (left and right channels)
                        left = struct.unpack('<h', audio_bytes[i:i+2])[0]
                        right = struct.unpack('<h', audio_bytes[i+2:i+4])[0]
                        # Convert stereo to mono by averaging
                        mono_sample = (left + right) // 2
                        user_mono.append(mono_sample)
                
                # Pad shorter recordings with silence to match longest
                while len(user_mono) < mono_sample_count:
                    user_mono.append(0)
                
                user_samples[user_id] = user_mono
                user_name = self.user_names.get(user_id, user_id)
                logger.info(f"  User {user_name}: {len(user_mono)} samples (padded to {mono_sample_count})")
            
            # Now mix all users together with proper audio mixing
            mixed_samples = [0] * mono_sample_count
            for sample_index in range(mono_sample_count):
                # Add all users' samples at this time point
                sample_sum = sum(user_mono[sample_index] for user_mono in user_samples.values())
                mixed_samples[sample_index] = sample_sum
            
            # Apply dynamic normalization to prevent clipping while preserving volume
            # Find the peak value
            max_abs_value = max(abs(s) for s in mixed_samples)
            if max_abs_value > 32767:  # Clipping would occur
                # Scale down to fit in 16-bit range, but only if necessary
                scale_factor = 32767 / max_abs_value
                mixed_samples = [int(s * scale_factor) for s in mixed_samples]
                logger.info(f"Applied normalization with scale factor {scale_factor:.3f} (peak was {max_abs_value})")
            else:
                logger.info(f"No normalization needed (peak was {max_abs_value})")
            
            # Convert back to bytes
            mixed_bytes = bytearray()
            for sample in mixed_samples:
                # Clamp to 16-bit range
                sample = max(-32768, min(32767, sample))
                mixed_bytes.extend(struct.pack('<h', sample))
            
            # Save as WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono (converted from stereo)
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
    
    def stop(self):
        """Stop the recorder (called when user explicitly stops recording)"""
        self.is_stopped = True
        logger.info(f"Recorder stopped (recorded {len(self.audio_data)} users, {self.total_bytes_received} bytes total)")
        logger.info(f"Last audio received at: {self.last_audio_time}")
    
    def cleanup(self):
        """Clean up resources (called on disconnect, but doesn't stop recording)"""
        # Don't set is_stopped here - that should only be set when user explicitly stops
        logger.info(f"Cleaning up recorder (recorded {len(self.audio_data)} users, {self.total_bytes_received} bytes total)")
        logger.info(f"Last audio received at: {self.last_audio_time}")
        # Don't clear data here - let the caller save it first
        # self.audio_data.clear()
        # self.user_names.clear()
    
    def get_status(self) -> dict:
        """Get current recording status"""
        duration_since_last_audio = (datetime.now() - self.last_audio_time).total_seconds()
        recording_duration = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate actual duration from longest user's audio
        max_user_bytes = max((len(data) for data in self.audio_data.values()), default=0)
        # Each stereo frame is 4 bytes, sample rate is 48000 Hz
        estimated_duration = max_user_bytes / (self.sample_rate * 4) if max_user_bytes > 0 else 0
        
        return {
            'is_stopped': self.is_stopped,
            'users_recording': len(self.audio_data),
            'total_bytes': self.total_bytes_received,
            'recording_duration': recording_duration,
            'estimated_duration': estimated_duration,
            'last_audio_seconds_ago': duration_since_last_audio,
            'has_data': len(self.audio_data) > 0 and any(len(data) > 0 for data in self.audio_data.values())
        }
    
    def create_checkpoint(self) -> bytes:
        """Create a checkpoint of current audio data (for backup purposes)"""
        try:
            if not self.audio_data:
                return b''
            
            # Create an in-memory WAV file as a checkpoint
            with io.BytesIO() as buffer:
                with wave.open(buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(self.sample_width)
                    wav_file.setframerate(self.sample_rate)
                    
                    # Mix audio using same algorithm as save_to_file
                    max_length = max((len(data) for data in self.audio_data.values() if len(data) > 0), default=0)
                    if max_length == 0:
                        return b''
                    
                    mono_sample_count = max_length // 4
                    
                    # Convert each user to mono samples and pad
                    user_samples = []
                    for audio_bytes in self.audio_data.values():
                        user_mono = []
                        for i in range(0, len(audio_bytes), 4):
                            if i + 3 < len(audio_bytes):
                                left = struct.unpack('<h', audio_bytes[i:i+2])[0]
                                right = struct.unpack('<h', audio_bytes[i+2:i+4])[0]
                                mono_sample = (left + right) // 2
                                user_mono.append(mono_sample)
                        
                        # Pad to max length
                        while len(user_mono) < mono_sample_count:
                            user_mono.append(0)
                        user_samples.append(user_mono)
                    
                    # Mix all users
                    mixed_samples = [0] * mono_sample_count
                    for sample_index in range(mono_sample_count):
                        sample_sum = sum(user_mono[sample_index] for user_mono in user_samples)
                        mixed_samples[sample_index] = sample_sum
                    
                    # Apply dynamic normalization
                    max_abs_value = max(abs(s) for s in mixed_samples)
                    if max_abs_value > 32767:
                        scale_factor = 32767 / max_abs_value
                        mixed_samples = [int(s * scale_factor) for s in mixed_samples]
                    
                    # Write samples
                    mixed_bytes = bytearray()
                    for sample in mixed_samples:
                        sample = max(-32768, min(32767, sample))
                        mixed_bytes.extend(struct.pack('<h', sample))
                    
                    wav_file.writeframes(bytes(mixed_bytes))
                
                buffer.seek(0)
                return buffer.read()
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}", exc_info=True)
            return b''
