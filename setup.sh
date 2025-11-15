#!/bin/bash
# Setup script for E-Commerce Data Analysis Agent

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   E-Commerce Data Analysis Agent - Setup Script              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it to add your GOOGLE_API_KEY."
else
    echo ""
    echo "⚠️  .env file already exists. Skipping..."
fi

# Check for Google Cloud SDK
echo ""
echo "Checking for Google Cloud SDK..."
if command -v gcloud &> /dev/null; then
    echo "✅ Google Cloud SDK is installed."
    
    # Check authentication
    echo ""
    echo "Checking Google Cloud authentication..."
    gcloud auth application-default print-access-token &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Google Cloud authentication is configured."
    else
        echo "⚠️  Google Cloud authentication not found."
        echo ""
        echo "Run the following command to authenticate:"
        echo "  gcloud auth application-default login"
    fi
else
    echo "⚠️  Google Cloud SDK not found."
    echo ""
    echo "To install Google Cloud SDK:"
    echo "  Visit: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "After installation, authenticate with:"
    echo "  gcloud auth application-default login"
fi

# Final instructions
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     Setup Complete!                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Get a Google AI Studio API key from:"
echo "     https://makersuite.google.com/app/apikey"
echo ""
echo "  2. Add your API key to .env file:"
echo "     GOOGLE_API_KEY=your_api_key_here"
echo ""
echo "  3. Authenticate with Google Cloud (if not already done):"
echo "     gcloud auth application-default login"
echo ""
echo "  4. Run the agent:"
echo "     python main.py"
echo ""
echo "For more information, see README.md"
echo ""

