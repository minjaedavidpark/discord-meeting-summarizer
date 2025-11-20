# Recording Reliability Improvements

## What Was Fixed

Your October 12 meeting failed because Discord sent malformed audio packets that crashed the audio reception thread. The bot thought it was still recording for 27 minutes, but no audio was being captured after the crash at 7 seconds in.

## New Features to Prevent Data Loss

### 1. 🔒 Automatic Checkpoints (Every 60 seconds)

The bot now automatically saves backup copies of your recording every 60 seconds. If a crash occurs, you'll have at least the checkpoint data.

```
!join
🔴 Recording started in daily-standup!
💡 Use !stop when done to get your summary.
🔒 Auto-save checkpoints enabled every 60 seconds.
```

### 2. ⚠️ Real-Time Warnings

If no audio is received for 60+ seconds during a recording, you'll get a warning:

```
⚠️ Warning: No audio received for 60 seconds.
Recording may have stopped unexpectedly.
You may want to use !stop and restart.
```

### 3. 📊 Status Command

Check if recording is working mid-meeting:

```
!status

🟢 Recording Status
👥 Users: 2 user(s)
💾 Data: 5.23 MB
⏱️ Duration: ~65.2 seconds
📡 Last audio: 3 seconds ago
✅ Has data: Yes
```

Status indicators:
- 🟢 Green = Audio received within last 30 seconds (healthy)
- 🟡 Yellow = 30-60 seconds since last audio (warning)
- 🔴 Red = 60+ seconds since last audio (problem!)

### 4. 💾 Checkpoint Recovery

If the main recording fails but checkpoints exist, the bot will use them automatically:

```
!stop
⚠️ Used backup checkpoint data. Recording may have been interrupted.
Processing...
```

## Updated Commands

### Existing Commands (Enhanced)
- `!join` - Start recording with automatic checkpoints
- `!stop` - Stop recording (now uses checkpoint if main data lost)
- `!leave` - Leave voice channel (now stops watchdog)

### New Commands
- `!status` - Check recording health during a meeting

## Recommended Usage for Long Meetings

For meetings over 10 minutes:

1. **Start recording**: `!join`
2. **Check status periodically**: `!status` (every 5-10 minutes)
3. **Watch for warnings**: Bot will alert you if issues occur
4. **Stop when done**: `!stop`

If you see a warning:
- Check `!status` to see current state
- If recording is dead (red status, 60+ seconds), do `!stop` then `!join` to restart
- The checkpoint from before the crash will still be saved

## What Happens in Different Scenarios

### Scenario 1: Normal Recording ✅
```
!join → record for 30 minutes → !stop
Result: Full 30-minute recording processed
```

### Scenario 2: Crash at 5 Minutes ⚠️
```
!join → record for 5 mins → [crash] → continue for 25 mins → !stop
New behavior: 
- Warning at 6 minutes (60 seconds after crash)
- Checkpoint saved before crash
- !stop uses 5-minute checkpoint
Old behavior:
- No warning
- Total data loss
```

### Scenario 3: Multiple Checkpoints 💪
```
!join → 2 mins → checkpoint → 2 mins → checkpoint → 2 mins → crash → !stop
Result: Latest checkpoint (4 minutes of audio) is used
```

## Technical Details

### Checkpoint Files
- Saved to `recordings/checkpoint_TIMESTAMP.wav`
- Created every 60 seconds during active recording
- Automatically used if main recording fails
- Can accumulate during long meetings (safe to delete old ones)

### Watchdog Monitoring
- Checks recording health every 10 seconds
- Tracks: users recording, bytes received, time since last audio
- Sends warnings via Discord messages
- Runs automatically when you `!join`

### Status Information
The `!status` command shows:
- **Users**: How many people are being recorded
- **Data**: Total size of audio captured (in MB)
- **Duration**: Approximate recording duration
- **Last audio**: How recently audio was received
- **Has data**: Whether any audio exists

## Files Created

During recording, you'll see these files in `recordings/`:
- `checkpoint_YYYYMMDD_HHMMSS.wav` - Periodic backups (every 60 seconds)
- `meeting_YYYYMMDD_HHMMSS.wav` - Final recording (when you !stop)
- `transcript_YYYYMMDD_HHMMSS.txt` - Transcription
- `summary_YYYYMMDD_HHMMSS.txt` - AI summary

You can safely delete old checkpoint files after the meeting is processed.

## Known Limitations

1. **Can't prevent Discord packet issues**: We can't fix Discord's protocol issues, but we now recover from them
2. **Checkpoint overhead**: Creates additional files every 60 seconds (minimal CPU/storage impact)
3. **Gap between checkpoints**: If crash occurs at 1:30 and last checkpoint at 1:00, you lose 30 seconds

## Troubleshooting

### "Warning: No audio received"
**What it means**: The bot hasn't received audio packets for 60+ seconds

**What to do**:
1. Check `!status` to see current state
2. Make sure people are actually talking
3. If status shows 🔴 and no recent audio, stop and restart:
   - `!stop` (saves what you have)
   - `!join` (starts fresh)

### "Used backup checkpoint data"
**What it means**: Main recording failed but checkpoint exists

**What to do**:
- Nothing! The bot automatically used the backup
- You'll get a transcript of audio up to the last checkpoint
- Consider restarting recording more frequently if this happens often

### Recording shows "No audio data"
**What it means**: Both main recording and checkpoints are empty

**What to do**:
- Check that people spoke during the meeting
- Verify bot has proper voice permissions in Discord
- Check `bot.log` for errors
- Try restarting the bot: `./restart_bot.sh`

## Migration Notes

- No changes needed to your workflow
- All existing commands work the same
- New features activate automatically
- Old recordings are not affected

## Example Session

```
You: !join
Bot: 🔴 Recording started in daily-standup!
     💡 Use !stop when done to get your summary.
     🔒 Auto-save checkpoints enabled every 60 seconds.

[5 minutes pass, everyone talking]

You: !status
Bot: 🟢 Recording Status
     👥 Users: 3 user(s)
     💾 Data: 15.2 MB
     ⏱️ Duration: ~158.3 seconds
     📡 Last audio: 2 seconds ago
     ✅ Has data: Yes

[Discord sends bad packet, crash occurs]

[60 seconds pass]

Bot: ⚠️ Warning: No audio received for 60 seconds.
     Recording may have stopped unexpectedly.
     You may want to use !stop and restart.

You: !stop
Bot: ⚠️ Used backup checkpoint data. Recording may have been interrupted.
     Processing...
     🎙️ Recording saved! Transcribing...
     [transcription happens]
     ✅ Processing complete!
     
     📊 Meeting Summary
     [Your 5-minute summary here]
```

## Questions?

If you encounter issues:
1. Check `bot.log` for detailed error messages
2. Use `!status` to see current recording state
3. Look for checkpoint files in `recordings/` directory

The bot will now be much more resilient to Discord's packet issues!


