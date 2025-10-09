#!/bin/bash

# Stop the Discord bot cleanly

echo "🛑 Stopping Discord bot..."

if [ -f bot.pid ]; then
    BOT_PID=$(cat bot.pid)
    if ps -p $BOT_PID > /dev/null; then
        kill $BOT_PID
        echo "✅ Stopped bot (PID: $BOT_PID)"
        rm -f bot.pid
    else
        echo "⚠️  Bot with PID $BOT_PID is not running"
        rm -f bot.pid
    fi
else
    echo "⚠️  No bot.pid file found, killing all bot processes..."
    pkill -f "bot.py"
fi

sleep 1

# Verify stopped
if pgrep -f "bot.py" > /dev/null; then
    echo "⚠️  Some processes still running, forcing kill..."
    pkill -9 -f "bot.py"
fi

echo "✅ Bot stopped"

