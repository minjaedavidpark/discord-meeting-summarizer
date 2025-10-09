#!/bin/bash

# Quick start script for Discord Meeting Summarizer

echo "🎙️  Discord Meeting Summarizer - Starting..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "   Please run: cp .env.example .env"
    echo "   Then edit .env with your credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: ./setup.sh first"
    exit 1
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Test configuration
echo "🔍 Testing configuration..."
python scripts/test_config.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Configuration test failed!"
    echo "   Please fix the issues above before starting the bot"
    exit 1
fi

# Create recordings directory
mkdir -p recordings

# Start the bot
echo ""
echo "🚀 Starting bot..."
echo "   Press Ctrl+C to stop"
echo ""
python bot.py

