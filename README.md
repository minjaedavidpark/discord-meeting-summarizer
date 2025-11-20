# 🎙️ Discord Meeting Summarizer

A production-ready Discord bot that records daily voice meetings, transcribes them with OpenAI Whisper, and generates structured summaries with action items and key decisions. Perfect for startup standups and team sync meetings.

Built for [PontiFi](https://pontifi.com/) 🚀

## ✨ Features

- **🎤 Voice Recording**: Automatically join and record Discord voice channels
- **📝 AI Transcription**: High-quality transcription using OpenAI Whisper
- **📊 Smart Summaries**: AI-generated summaries with:
  - Key discussion points
  - Decisions made
  - Action items with assignees
  - Blockers and next steps
- **⏰ Scheduled Recording**: Auto-start recordings at scheduled times
- **☁️ Cloud Ready**: Deploy to Fly.io, Render, DigitalOcean, or Docker
- **💾 Persistent Storage**: Saves recordings, transcripts, and summaries locally

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- FFmpeg installed on your system

### Option 1: Local Setup (Recommended for Development)

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd discord-meeting-summarizer
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Run the bot**
   ```bash
   source venv/bin/activate
   python bot.py
   ```

### Option 2: Docker (Recommended for Production)

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **View logs**
   ```bash
   docker-compose logs -f
   ```

## 🔧 Configuration

Create a `.env` file with the following variables:

```env
# Required
DISCORD_BOT_TOKEN=your_discord_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DISCORD_GUILD_ID=your_server_id
DISCORD_VOICE_CHANNEL_ID=your_channel_id
MEETING_TIME=09:00
MEETING_TIMEZONE=America/New_York
```

### Getting Discord IDs

1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click on your server → Copy ID (Guild ID)
3. Right-click on voice channel → Copy ID (Voice Channel ID)

### Setting up the Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a New Application
3. Go to "Bot" section and create a bot
4. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent
5. Go to OAuth2 → URL Generator
6. Select scopes: `bot`
7. Select permissions:
   - Connect
   - Speak
   - Use Voice Activity
   - Send Messages
   - Read Message History
8. Use generated URL to invite bot to your server

## 📖 Usage

### 🎙️ Direct Recording (Fully Automated!)

The bot can directly record your Discord voice channels - no external tools needed!

**Basic Commands:**
```
!join              - Bot joins your voice channel and starts recording
!stop              - Stop recording and generate summary
!leave             - Bot leaves channel
!upload            - Upload a pre-recorded audio file
!help_recording    - Show all recording options
```

### Example Workflow (Direct Recording)

**Every meeting:**
1. Join your voice channel in Discord
2. Type: `!join` (Bot joins and starts recording)
3. Have your meeting (speak normally!)
4. Type: `!stop` (Bot processes and posts summary)

That's it! Fully automated. 🎉

The bot will:
- Record your voice channel in high quality (48kHz)
- Transcribe it with OpenAI Whisper
- Generate an AI summary with action items
- Post the summary in Discord
- Save all files in the `recordings/` directory

### Alternative: Manual Upload

If you recorded your meeting separately (OBS, QuickTime, etc.):
1. Type `!upload` in Discord
2. Attach your audio file (mp3, wav, m4a, flac, ogg)
3. Get your AI summary!

### Automated Recording (Optional)

If you configure `MEETING_TIME` and channel IDs in `.env`, the bot can automatically:
1. Join the specified voice channel at the scheduled time
2. Start recording
3. Generate summaries (you still need to use `!stop` to end recording)

## 📁 Output Files

All files are saved in the `recordings/` directory:

```
recordings/
├── meeting_20241009_093015.wav       # Audio recording
├── transcript_20241009_093015.txt    # Full transcript
└── summary_20241009_093015.txt       # AI-generated summary
```

## 🌐 Cloud Deployment

### Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and deploy
flyctl auth login
flyctl launch
flyctl secrets set DISCORD_BOT_TOKEN=xxx OPENAI_API_KEY=xxx
flyctl deploy
```

### Render

1. Connect your GitHub repo to Render
2. Select "New Worker"
3. Use `render.yaml` configuration
4. Add environment variables in Render dashboard
5. Deploy

### DigitalOcean / Generic VPS

```bash
# SSH into your server
ssh user@your-server

# Clone repo
git clone <your-repo-url>
cd discord-meeting-summarizer

# Setup and run with Docker
docker-compose up -d
```

## 🔒 Security Best Practices

- Never commit `.env` file
- Rotate API keys regularly
- Use environment variables for secrets
- Limit bot permissions to necessary channels only
- Regularly review recordings and delete old ones
   
## 💡 Tips & Tricks

- **Cost Optimization**: Whisper API costs ~$0.006 per minute. A 30-min meeting costs about $0.18
- **Quality**: Ensure good audio quality - quiet environment and decent microphones
- **Privacy**: Inform meeting participants they're being recorded
- **Storage**: Recordings can be large; consider automated cleanup scripts
- **Multiple Meetings**: The bot can only record one meeting at a time

## 🐛 Troubleshooting

### Bot not recording audio
- Check FFmpeg is installed: `ffmpeg -version`
- Verify bot has "Connect" and "Speak" permissions
- Ensure PyNaCl is installed: `pip install PyNaCl`

### Transcription fails
- Check OpenAI API key is valid
- Verify audio file is not corrupted
- Ensure file size is under 25MB (Whisper limit)

### Bot doesn't respond
- Verify bot token is correct
- Check bot has "Message Content Intent" enabled
- Ensure bot has permission to read/send messages in the channel

### Docker issues
- Make sure Docker and Docker Compose are installed
- Check logs: `docker-compose logs`
- Verify `.env` file exists and is properly formatted

## 📝 License

MIT License - feel free to use for your own projects!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💬 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Made with ❤️ for better team communication at [PontiFi](https://pontifi.com/)
