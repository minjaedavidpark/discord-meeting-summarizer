# Recording Fix - October 12, 2025

## Problem Summary

During a meeting recording on October 12, 2025 (4:03 PM - 4:30 PM), the bot appeared to be recording but when `!stop` was issued, it reported "No audio data recorded!" despite the 27-minute duration.

## Root Cause Analysis

From analyzing `bot.log`, the issue was:

1. **Initial Success**: The bot successfully recorded audio from 16:03:20 to 16:03:27 (~7 seconds)
   - Audio data was being written from users "Lawless_Peninsula" and "jaffar"
   - Total of ~400+ audio packets were successfully captured

2. **Silent Crash**: At 16:03:27, Discord sent malformed audio packets (ssrc=0):
   ```
   [INFO] Received packet for unknown ssrc 0
   [ERROR] discord.opus.OpusError: invalid argument
   Error in <PacketRouter(packet-router-1039e8890, started daemon 6287405056)> loop
   ```

3. **Recorder Cleanup**: The packet router thread crashed, triggering automatic cleanup:
   ```
   Cleaning up recorder (recorded 2 users)
   ```
   This cleared all the audio data that had been captured.

4. **Silent Failure**: The bot's `is_recording` flag stayed `True` for the next 27 minutes, even though no audio was being captured. No warning was sent to users.

5. **Failed Stop**: When `!stop` was issued at 16:30:59, the recorder had no data because it had been cleared 27 minutes earlier.

## The Core Issues

1. **No Error Detection**: The bot didn't detect when the audio reception thread crashed
2. **No Data Persistence**: All audio data was lost when the crash occurred
3. **No User Notification**: Users weren't informed that recording had stopped
4. **External Library Failure**: The `discord-ext-voice-recv` library's packet router crashed on malformed packets from Discord

## Solutions Implemented

### 1. Recording Watchdog (`recording_watchdog()`)

A background task that:
- Monitors audio reception every 10 seconds
- Detects when no audio has been received for >60 seconds
- Sends warnings to users when recording appears to have stopped
- Tracks recording health metrics

### 2. Checkpoint System

Automatic backups created every 60 seconds:
- Saves a checkpoint WAV file to disk
- If main recording fails, the latest checkpoint is used
- Prevents total data loss from crashes

### 3. Enhanced Status Tracking

Added to `MeetingRecorder`:
- `last_audio_time`: Tracks when audio was last received
- `total_bytes_received`: Running total of audio data
- `is_stopped`: Flag to prevent writes after cleanup
- `get_status()`: Returns detailed recording health info

### 4. Better Error Handling

- `write()` method now has try-catch to prevent crashes
- `cleanup()` no longer clears data immediately (lets caller save first)
- Optional error callback for async error reporting

### 5. New `!status` Command

Users can check recording health mid-meeting:
```
!status
🟢 Recording Status
👥 Users: 2 user(s)
💾 Data: 5.23 MB
⏱️ Duration: ~65.2 seconds
📡 Last audio: 3 seconds ago
✅ Has data: Yes
```

## Updated User Experience

### Before
1. `!join` - "Recording started"
2. *[Silent crash 7 seconds later]*
3. *[27 minutes pass with no recording]*
4. `!stop` - "No audio data recorded!"
5. User: "What happened??" 😡

### After
1. `!join` - "Recording started" + "Auto-save checkpoints enabled every 60 seconds"
2. *[Checkpoint saved at 1 minute mark]*
3. *[Crash occurs]*
4. *[Watchdog detects silence after 60 seconds]*
5. Bot: "⚠️ Warning: No audio received for 60 seconds. Recording may have stopped unexpectedly."
6. User can:
   - Check status: `!status` 
   - Stop and use checkpoint data: `!stop` → "⚠️ Used backup checkpoint data"
   - Restart recording: `!leave` then `!join`

## Technical Details

### Checkpoint Implementation

```python
def create_checkpoint(self) -> bytes:
    """Create a checkpoint of current audio data (for backup purposes)"""
    # Creates in-memory WAV file
    # Mixes all user audio
    # Returns raw bytes for storage
```

### Watchdog Loop

```python
async def recording_watchdog():
    while is_recording:
        await asyncio.sleep(10)
        status = current_recorder.get_status()
        
        # Create checkpoint every 60 seconds
        if time_for_checkpoint:
            save_checkpoint_to_disk()
        
        # Warn if no audio for 60+ seconds
        if seconds_since_audio > 60:
            warn_user()
```

### Stop Command Changes

```python
@bot.command(name='stop')
async def stop(ctx):
    # Stop watchdog
    # Check if recorder has data
    if has_data:
        save_and_process()
    elif last_checkpoint_data:
        # Fallback to checkpoint
        use_checkpoint()
    else:
        error_message()
```

## Files Modified

1. **audio_recorder.py**
   - Added: `last_audio_time`, `total_bytes_received`, `is_stopped`, `error_callback`
   - Added: `set_error_callback()`, `get_status()`, `create_checkpoint()`
   - Modified: `write()` - added error handling
   - Modified: `cleanup()` - doesn't clear data immediately

2. **bot.py**
   - Added: `recording_watchdog_task`, `last_checkpoint_data` globals
   - Added: `recording_watchdog()` function
   - Added: `!status` command
   - Modified: `!join` - starts watchdog
   - Modified: `!stop` - stops watchdog, uses checkpoint on failure
   - Modified: `!leave` - stops watchdog

## Testing Recommendations

1. **Normal Operation Test**
   - Start recording, speak for 2 minutes, stop
   - Verify: Recording saves successfully

2. **Checkpoint Test**
   - Start recording, speak for 3+ minutes
   - Verify: Checkpoint files appear in recordings/ every 60 seconds

3. **Status Test**
   - Start recording, use `!status` during meeting
   - Verify: Shows correct user count, data size, timing

4. **Silence Detection Test** (requires simulation)
   - Start recording, simulate packet failure
   - Verify: Warning appears after 60 seconds

5. **Checkpoint Recovery Test** (requires simulation)
   - Start recording, create checkpoint, clear main data, stop
   - Verify: Uses checkpoint data successfully

## Prevention Measures

While we can't prevent Discord from sending bad packets, we now:
1. ✅ Detect when recording stops unexpectedly
2. ✅ Warn users in real-time
3. ✅ Save data periodically (checkpoints)
4. ✅ Recover from crashes gracefully
5. ✅ Provide visibility into recording health

## Known Limitations

1. **Discord Library Issue**: The underlying `discord-ext-voice-recv` library can still crash on malformed packets. We've added recovery, not prevention.

2. **Checkpoint Overhead**: Checkpoints add some CPU/memory overhead every 60 seconds. For long meetings (2+ hours), this is minimal but measurable.

3. **Race Conditions**: If a crash occurs right before a checkpoint, we could lose up to 60 seconds of audio.

## Future Improvements

1. **Smarter Checkpoint Timing**: Create checkpoints on-demand when silence is detected
2. **Automatic Recovery**: Automatically restart recording if crash is detected
3. **Better Discord Library**: Consider alternative voice recording libraries or patching discord-ext-voice-recv
4. **Metrics/Monitoring**: Track recording reliability over time
5. **User Preferences**: Let users configure checkpoint intervals

## Deployment Notes

- No breaking changes to existing commands
- Checkpoints will create additional files in `recordings/` directory
- New `!status` command available immediately
- Watchdog runs automatically, no configuration needed

## Summary

This fix transforms a silent failure into a recoverable situation with user visibility. While we can't prevent the underlying Discord packet issues, we now:
- Detect failures quickly
- Save data before loss
- Inform users of problems
- Provide recovery options

The next time Discord sends bad packets, users will be warned within 60 seconds and will have checkpoint data to fall back on.


