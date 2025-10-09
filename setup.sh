#!/bin/bash

# Discord Meeting Summarizer Setup Script

echo "🚀 Setting up Discord Meeting Summarizer..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your credentials!"
else
    echo "✅ .env file already exists"
fi

# Create recordings directory
mkdir -p recordings

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Discord bot token and OpenAI API key"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the bot: python bot.py"
echo ""
echo "For Docker deployment:"
echo "1. Edit .env file with your credentials"
echo "2. Run: docker-compose up -d"

