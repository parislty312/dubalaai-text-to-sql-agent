#!/bin/bash

set -e

echo "Setting up DubalaAI Text-to-SQL Agent..."
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed."
    echo "Please install uv first: https://github.com/astral-sh/uv"
    echo "Quick install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment and install dependencies
echo "Creating virtual environment and installing dependencies..."
uv venv
source .venv/bin/activate
uv pip install -e .

# Build the sample personal finance database
echo ""
echo "Creating personal finance database..."
mkdir -p data

python scripts/create_personal_finance_db.py

if [ -f "data/personal_finance.db" ]; then
    echo "Successfully created data/personal_finance.db"
else
    echo "Error: Failed to create database"
    exit 1
fi

echo ""
echo "Setup complete!"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source .venv/bin/activate"
echo "  2. Put FIREWORKS_API_KEY and optional FIREWORKS_BASE_URL in .env"
echo "  3. Run the CLI: python -m src.cli --model qwen3p7-plus --strategy single --no-summary"
echo "     or without activation: uv run python -m src.cli --model qwen3p7-plus --strategy single --no-summary"
echo ""
