# Bug Fix: Recording Stops After Discord Reconnection

**Date:** 2025-10-15  
**Issue:** Recording stopped mid-meeting after Discord connection timeout  
**Status:** ✅ FIXED

## Problem Description

During a meeting on 2025-10-15 at ~12:30 PM, the bot stopped recording audio even though people were still talking. The Discord bot showed warnings about no audio received, but the meeting was still active.

### Symptoms
- Recording started normally at 12:05 PM
- At 12:34 PM, bot warned: "No audio received for 65 seconds"
- Briefly showed "Audio reception resumed!"
- Then showed another warning: "No audio received for 60 seconds"
- After that, recording completely stopped (no more audio captured)

## Root Cause Analysis

### Timeline of Events (from bot.log)

1. **12:30:01** - Checkpoint creation started (30 min of audio accumulated)
   - Processing ~1GB of audio data synchronously
   - List comprehension `mixed_samples = [int(s * scale_factor) for s in mixed_samples]` blocked the event loop
   
2. **12:30:01** - Discord heartbeat blocked warning
   - `Shard ID None heartbeat blocked for more than 10 seconds`
   - Discord connection requires regular heartbeats; blocking >10s causes timeout
   
3. **12:35:56** - Discord disconnected and reconnected
   - `Disconnecting from voice normally, close code 1000`
   - Gateway successfully resumed session
   - BUT: `cleanup()` method was called, setting `is_stopped = True`
   
4. **After 12:35:56** - Recording silently failed
   - `write()` method rejected all audio packets because `is_stopped = True`
   - Watchdog showed `'is_stopped': True` but recording flag was still active
   - No new audio was captured

### The Two Bugs

#### Bug #1: Blocking Checkpoint Creation
The `create_checkpoint()` method processes large amounts of audio synchronously:
- Converts 30 minutes of stereo audio to mono samples
- Mixes multiple user tracks
- Applies normalization with list comprehensions
- **Blocked the asyncio event loop for >10 seconds**
- Caused Discord heartbeat to fail and connection to timeout

```python
# In audio_recorder.py, line 237
mixed_samples = [int(s * scale_factor) for s in mixed_samples]  # BLOCKS!
```

#### Bug #2: Recorder Stopped on Reconnection
The `cleanup()` method set `is_stopped = True` when Discord disconnected:
- Called during normal voice disconnect/reconnect cycles
- Set `is_stopped = True` permanently
- After reconnection, `write()` rejected all audio packets
- No way to resume recording

```python
# In audio_recorder.py, line 164 (OLD CODE)
def cleanup(self):
    self.is_stopped = True  # BUG: Stops recording permanently!
```

## The Fix

### Fix #1: Non-blocking Checkpoint Creation
Move checkpoint creation to a thread pool executor to avoid blocking the event loop:

```python
# In bot.py, recording_watchdog()
loop = asyncio.get_event_loop()
last_checkpoint_data = await loop.run_in_executor(
    None, 
    current_recorder.create_checkpoint
)
```

**Result:** Checkpoints no longer block Discord heartbeat

### Fix #2: Separate Stop from Cleanup
Split `cleanup()` into two methods:
- `stop()` - Explicitly stops recording (called when user runs `!stop`)
- `cleanup()` - Logs status but doesn't stop (called on disconnect)

```python
# In audio_recorder.py
def stop(self):
    """Stop the recorder (called when user explicitly stops recording)"""
    self.is_stopped = True
    logger.info(f"Recorder stopped...")

def cleanup(self):
    """Clean up resources (called on disconnect, but doesn't stop recording)"""
    # Don't set is_stopped here - that should only be set when user explicitly stops
    logger.info(f"Cleaning up recorder...")
```

**Result:** Recording survives Discord reconnections

### Fix #3: Better Monitoring
Added `on_voice_state_update` event handler to track voice connection state:

```python
@bot.event
async def on_voice_state_update(member, before, after):
    if member == bot.user:
        if after.channel is None:
            logger.warning("Bot was disconnected from voice channel")
            if is_recording:
                logger.warning("Voice disconnection during recording - waiting for reconnection...")
```

### Fix #4: Improved User Warnings
Updated watchdog warnings to be more helpful:

```python
if current_recorder.is_stopped:
    await recording_channel.send(
        "⚠️ **Critical**: Recorder was stopped unexpectedly. This is a bug."
    )
else:
    await recording_channel.send(
        "⚠️ **Warning**: No audio received for 60 seconds. "
        "This could be due to:\n"
        "• Everyone is muted or silent\n"
        "• Network issues (bot will auto-recover)\n"
        "• Recording will continue when audio resumes"
    )
```

## Testing the Fix

### Manual Test
1. Start recording: `!join`
2. Wait for 2+ checkpoints (2 minutes)
3. Simulate network issue by disrupting connection briefly
4. Verify recording continues after reconnection
5. Stop recording: `!stop`
6. Verify all audio is captured

### What Changed
- ✅ Checkpoints no longer block the event loop
- ✅ Recording survives Discord reconnections  
- ✅ Better logging of voice connection state
- ✅ More informative user warnings
- ✅ `is_stopped` only set when user explicitly stops

## Files Modified

1. **audio_recorder.py**
   - Added `stop()` method for explicit stopping
   - Modified `cleanup()` to NOT set `is_stopped`
   - Recording now survives disconnections

2. **bot.py**
   - Moved checkpoint creation to executor (non-blocking)
   - Added `on_voice_state_update` event handler
   - Improved watchdog warnings
   - Call `stop()` explicitly before cleanup

## Prevention

To avoid similar issues in the future:

1. **Always use executors for heavy CPU work**
   - Never process large amounts of data synchronously in async context
   - Use `asyncio.run_in_executor()` for CPU-intensive operations

2. **Separate lifecycle methods**
   - `cleanup()` should not change behavioral state
   - Use explicit `start()` and `stop()` methods for state changes

3. **Test with long recordings**
   - Checkpoint creation scales with recording length
   - Test with 30+ minute recordings to catch blocking issues

4. **Monitor heartbeat health**
   - Discord heartbeat warnings indicate event loop blocking
   - Add metrics for event loop lag

## Verification

To verify the fix is working:
```bash
# Check recent logs for proper behavior
tail -f bot.log | grep -E "(checkpoint|heartbeat|Disconnecting|is_stopped)"
```

Expected behavior:
- Checkpoints complete without heartbeat warnings
- `is_stopped: False` during recording (even after reconnections)
- Clean reconnections without stopping the recorder

## Recovery Checkpoint

The bot saves checkpoints every 60 seconds to `recordings/checkpoint_TIMESTAMP.wav`. If a crash occurs, these files can be used to recover the recording up to the last checkpoint.

In this incident, checkpoints were available:
- `recordings/checkpoint_20251015_123358.wav`
- `recordings/checkpoint_20251015_123556.wav`
- (and others)

These can be used to reconstruct most of the meeting if needed.


