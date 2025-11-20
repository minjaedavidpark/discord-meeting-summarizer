# Incident Report - October 10, 2025

## Summary
The Discord meeting summarizer bot failed to complete processing a 39-minute meeting recording. The bot crashed during transcription and never sent a completion message to Discord.

## Timeline
- **12:04 PM**: Recording started
- **12:43 PM**: Recording stopped (39 minutes, 203MB file)
- **12:44 PM**: Transcription started
- **12:44-13:26 PM**: Bot slowly processed chunks, encountering timeout errors
- **13:26 PM**: Bot crashed and reconnected
- **13:27 PM**: Issue discovered by user

## Root Causes

### 1. Chunks Too Large
- File was split into 4-minute chunks (~22MB each)
- Too close to OpenAI's 25MB limit
- Caused slow API responses (1.5-3+ minutes per chunk)
- 10 chunks × 3 minutes = 30+ minutes total transcription time

### 2. No Timeout Protection
- No timeout on OpenAI API calls
- Bot hung when API was slow or unresponsive
- Eventually led to crash when connection errors occurred

### 3. No Retry Logic
- Any temporary network issue would cause permanent failure
- No recovery mechanism for transient errors

### 4. No Progress Updates
- User had no visibility into what was happening
- Appeared as if the bot was frozen or broken

### 5. Poor Error Handling
- When errors occurred, bot crashed without notifying user
- User left waiting with no resolution

## Fixes Implemented

### ✅ 1. Smaller Chunks (transcription.py)
```python
# Before: 4-minute chunks (~22MB)
chunk_duration = 240

# After: 2-minute chunks (~10-11MB)  
chunk_duration = 120
```
**Impact**: 
- ~50% smaller chunks
- Safer margin under 25MB limit
- Faster API responses
- Lower timeout risk

### ✅ 2. Retry Logic (transcription.py)
```python
max_retries = 3
retry_delay = 5  # seconds
```
**Impact**:
- Automatically retries failed chunks up to 3 times
- 5-second delay between attempts
- Handles transient network issues gracefully

### ✅ 3. Timeout Protection (transcription.py)
```python
timeout=300.0  # 5 minute timeout per API call
asyncio.wait_for(transcribe_chunk(), timeout=360.0)  # 6 min total
```
**Impact**:
- Prevents infinite hanging
- Fails fast instead of waiting forever
- Total timeout: 6 min × 3 retries = 18 min max per chunk

### ✅ 4. Progress Updates (bot.py)
```python
async def update_progress(current, total, status):
    await processing_msg.edit(
        content=f"🎙️ Transcribing... [▓▓▓░░░] {current}/{total} chunks"
    )
```
**Impact**:
- User sees real-time progress bar
- Knows how many chunks are done/remaining
- Clear indication that bot is working

### ✅ 5. Better Error Messages (bot.py)
```python
await processing_msg.edit(
    content=f"❌ Error during processing: {str(e)}\nCheck logs for details."
)
```
**Impact**:
- User gets notified of failures
- Error message includes helpful context
- Directs user to logs for debugging

## Expected Performance (After Fixes)

For a 39-minute meeting (203MB file):
- **Chunks created**: ~20 chunks (2 minutes each)
- **Time per chunk**: 30-90 seconds (down from 90-180 seconds)
- **Total transcription time**: 10-30 minutes (down from 30-60+ minutes)
- **Reliability**: Much higher with retries and timeouts
- **User experience**: Progress bar shows status in real-time

## How to Process Today's Failed Recording

You have the recording saved at:
```
recordings/meeting_20251010_124319.wav
```

### Option 1: Manual Processing Script (Recommended)
Use the new `process_recording.py` script:

```bash
cd /Users/minjaedavidpark/projects/discord-meeting-summarizer
source venv/bin/activate
python process_recording.py recordings/meeting_20251010_124319.wav
```

This will:
- Process the recording with the new improvements
- Show progress in the terminal
- Save transcript and summary to `recordings/` folder
- Print the summary when complete

### Option 2: Re-upload to Discord
1. Download the file from `recordings/meeting_20251010_124319.wav`
2. In Discord, type `!upload` and attach the file
3. Bot will process it with the new fixes

## Testing Recommendations

### Test 1: Short Recording (5 minutes)
- Should complete in under 2 minutes
- Single chunk processing

### Test 2: Medium Recording (20 minutes)  
- Should complete in 5-10 minutes
- ~10 chunks with progress updates

### Test 3: Long Recording (60 minutes)
- Should complete in 20-40 minutes
- ~30 chunks with full retry logic tested

## Prevention Measures

### Immediate
- ✅ Fixed chunk size
- ✅ Added timeouts
- ✅ Added retries
- ✅ Added progress updates
- ✅ Improved error handling

### Future Enhancements (Optional)
1. **Parallel chunk processing**: Process multiple chunks simultaneously
2. **Resume capability**: Save progress and resume from last successful chunk
3. **Alternative transcription**: Use faster local model for long recordings
4. **File size warning**: Warn users before processing very large files
5. **Estimated time**: Show estimated completion time based on file size

## Files Modified
- `transcription.py`: Core transcription logic with retry, timeout, and smaller chunks
- `bot.py`: Progress updates and better error handling
- `process_recording.py`: New manual processing script

## Bot Status
✅ Bot restarted at 13:29 PM with all fixes applied
✅ Ready for new recordings with improved reliability

## Monitoring
Watch the logs for:
```bash
tail -f /Users/minjaedavidpark/projects/discord-meeting-summarizer/bot.log
```

Look for:
- Successful chunk completions
- Any retry attempts (indicates temporary issues)
- Total processing time for recordings

