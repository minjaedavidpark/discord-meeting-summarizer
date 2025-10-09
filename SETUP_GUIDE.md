# 🚀 Complete Setup Guide

This guide will walk you through setting up your Discord Meeting Summarizer from scratch.

## Step 1: Create a Discord Bot

1. **Go to Discord Developer Portal**
   - Visit: https://discord.com/developers/applications
   - Click "New Application"
   - Give it a name (e.g., "Meeting Recorder")

2. **Configure the Bot**
   - In the left sidebar, click "Bot"
   - Click "Add Bot" → "Yes, do it!"
   - Under "Privileged Gateway Intents", enable:
     - ✅ Presence Intent
     - ✅ Server Members Intent
     - ✅ Message Content Intent
   - Click "Reset Token" and copy your bot token (save it securely!)

3. **Set Bot Permissions**
   - In the left sidebar, click "OAuth2" → "URL Generator"
   - Under "Scopes", select:
     - ✅ bot
   - Under "Bot Permissions", select:
     - ✅ Read Messages/View Channels
     - ✅ Send Messages
     - ✅ Connect
     - ✅ Speak
     - ✅ Use Voice Activity
   - Copy the generated URL at the bottom

4. **Invite Bot to Your Server**
   - Paste the URL in your browser
   - Select your server
   - Click "Authorize"

## Step 2: Get OpenAI API Key

1. **Sign up for OpenAI**
   - Visit: https://platform.openai.com/signup
   - Create an account or log in

2. **Get API Key**
   - Go to: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Give it a name (e.g., "Discord Bot")
   - Copy the key (save it securely - you won't see it again!)

3. **Add Payment Method**
   - Go to: https://platform.openai.com/account/billing
   - Add a payment method
   - Set up usage limits if desired

## Step 3: Get Discord IDs

1. **Enable Developer Mode**
   - Open Discord
   - Go to User Settings (gear icon)
   - Navigate to "Advanced"
   - Enable "Developer Mode"

2. **Get Server (Guild) ID**
   - Right-click on your server name
   - Click "Copy Server ID"
   - Save this ID

3. **Get Voice Channel ID**
   - Right-click on the voice channel you want to record
   - Click "Copy Channel ID"
   - Save this ID

## Step 4: Install the Bot

### Option A: Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd discord-meeting-summarizer

# Run setup script
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source venv/bin/activate
```

### Option B: Docker (Recommended)

```bash
# Just make sure Docker is installed
docker --version
docker-compose --version
```

## Step 5: Configure Environment Variables

1. **Copy example env file**
   ```bash
   cp .env.example .env
   ```

2. **Edit .env file**
   ```bash
   nano .env  # or use your favorite editor
   ```

3. **Fill in your credentials**
   ```env
   # Required
   DISCORD_BOT_TOKEN=your_bot_token_from_step_1
   OPENAI_API_KEY=your_openai_key_from_step_2
   
   # Optional but recommended for scheduled recordings
   DISCORD_GUILD_ID=your_server_id_from_step_3
   DISCORD_VOICE_CHANNEL_ID=your_voice_channel_id_from_step_3
   MEETING_TIME=09:00
   MEETING_TIMEZONE=America/New_York
   ```

## Step 6: Run the Bot

### Local Development

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the bot
python bot.py
```

You should see:
```
INFO - Bot has connected to Discord!
INFO - Bot is in X guild(s)
```

### Docker

```bash
# Start the bot
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

## Step 7: Test the Bot

1. **Join a voice channel** in your Discord server

2. **In a text channel, type:**
   ```
   !join
   ```
   Bot should join your voice channel

3. **Start recording:**
   ```
   !record
   ```

4. **Talk for a bit** (say something meaningful!)

5. **Stop recording:**
   ```
   !stop
   ```

6. **Check the results:**
   - Look in the `recordings/` folder for saved files
   - Bot should post a summary in Discord

## Troubleshooting

### Bot doesn't respond
- ✅ Check bot token is correct in `.env`
- ✅ Verify bot has "Message Content Intent" enabled
- ✅ Make sure bot has permissions in the channel
- ✅ Check bot is online (green dot in Discord)

### Can't record audio
- ✅ Install FFmpeg: `brew install ffmpeg` (Mac) or `apt install ffmpeg` (Linux)
- ✅ Install PyNaCl: `pip install PyNaCl`
- ✅ Check bot has "Connect" and "Speak" permissions

### Transcription fails
- ✅ Verify OpenAI API key is valid
- ✅ Check you have credits in your OpenAI account
- ✅ Make sure audio file is under 25MB

### Docker issues
- ✅ Make sure Docker daemon is running
- ✅ Check `.env` file is in the same directory
- ✅ View logs: `docker-compose logs`

## Cost Estimates

- **OpenAI Whisper**: ~$0.006 per minute of audio
  - 30-minute meeting: ~$0.18
  - Daily meetings for a month: ~$5.40
  
- **OpenAI GPT-4**: ~$0.01-0.03 per meeting summary
  - Daily summaries for a month: ~$0.60-1.80

**Total estimated cost**: ~$6-7/month for daily 30-minute meetings

## Next Steps

- ✅ Set up scheduled recordings with `MEETING_TIME`
- ✅ Deploy to a cloud provider for 24/7 uptime
- ✅ Customize the summary prompt in `summarizer.py`
- ✅ Set up automatic cleanup of old recordings
- ✅ Add webhooks to notify other tools

## Need Help?

- Check the main README.md
- Open an issue on GitHub
- Review Discord.py documentation: https://discordpy.readthedocs.io/

---

Happy recording! 🎙️

