#!/bin/bash

# OCR Pipeline v3.0 Setup Script
# Automated installation and configuration

echo "🚀 Setting up OCR Pipeline v3.0..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "🔄 Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ollama
        else
            echo "❌ Homebrew not found. Please install Ollama manually from: https://ollama.ai"
            exit 1
        fi
    else
        echo "❌ Please install Ollama manually from: https://ollama.ai"
        exit 1
    fi
fi

# Start Ollama service
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# Install required models
echo "🤖 Installing AI models..."
echo "   - granite3.2-vision (primary model)"
ollama pull granite3.2-vision

echo "   - llama3.1:8b (fast processing)"
ollama pull llama3.1:8b

echo "   - llama3.1:70b (high accuracy)"
ollama pull llama3.1:70b

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment configuration..."
    cp config/.env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Configure Transkribus credentials in .env file"
    echo "   1. Get credentials from: https://transkribus.eu/"
    echo "   2. Edit .env file with your email and password"
    echo ""
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/{input,output,temp}

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "   1. Configure Transkribus credentials in .env (optional for PDF processing)"
echo "   2. Test with: python3 run_pipeline.py --help"
echo "   3. Process a document: python3 run_pipeline.py your_file.pdf"
echo ""
echo "📚 Documentation: README.md"
