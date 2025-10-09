#!/bin/bash

# Clean restart script for Discord bot

echo "🛑 Stopping all bot processes..."
pkill -9 -f "bot.py" 2>/dev/null || true
sleep 2

# Verify all stopped
if pgrep -f "bot.py" > /dev/null; then
    echo "⚠️  Warning: Some bot processes still running, forcing kill..."
    killall -9 python 2>/dev/null || true
    sleep 1
fi

echo "🧹 Cleaning up old files..."
cd /Users/minjaedavidpark/projects/discord-meeting-summarizer
rm -f bot.log nohup.out bot.pid

echo "🚀 Starting bot..."
source venv/bin/activate
python bot.py > bot.log 2>&1 &
BOT_PID=$!

# Save PID to file for easy stopping later
echo $BOT_PID > bot.pid

sleep 3

# Verify bot is running
if ps -p $BOT_PID > /dev/null; then
    echo "✅ Bot started with PID: $BOT_PID"
    echo "📋 Checking status..."
    tail -5 bot.log
    
    echo ""
    echo "✨ Bot is running!"
    echo "📌 PID saved to bot.pid"
    echo "🛑 To stop: kill $BOT_PID (or: kill \$(cat bot.pid))"
    echo "📜 To view logs: tail -f bot.log"
    
    # Count running instances
    INSTANCE_COUNT=$(ps -A | grep "bot.py" | grep -v grep | wc -l | tr -d ' ')
    echo "🔢 Running instances: $INSTANCE_COUNT"
else
    echo "❌ Bot failed to start! Check bot.log for errors:"
    tail -20 bot.log
    exit 1
fi

