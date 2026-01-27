#!/bin/bash
# Setup script for local development

set -e

echo "🏡 House Search MLS Monitor - Local Setup"
echo "========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✓ .env file already exists"
fi

# Create data directories
mkdir -p data/backups
echo "✓ Data directories created"

echo ""
echo "========================================="
echo "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the service: python -m app.main"
echo "4. Or run tests: pytest"
