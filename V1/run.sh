#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

source venv/bin/activate

MODE="${1:-launcher}"

if [ "$MODE" = "launcher" ] || [ "$MODE" = "setup" ]; then
    echo "🔑 Starting API Key Setup Launcher on http://localhost:8888..."
    python3 launcher.py
    exit 0
fi

# Check if .env file exists and has GEMINI_API_KEY set
if [ ! -f ".env" ] || ! grep -q "GEMINI_API_KEY=." .env 2>/dev/null; then
    echo "--------------------------------------------------------"
    echo "⚠️  No valid GEMINI_API_KEY found in .env"
    echo "Starting interactive setup launcher at http://localhost:8888..."
    echo "--------------------------------------------------------"
    python3 launcher.py
    exit 0
fi

if [ "$MODE" = "web" ]; then
    echo "Starting ADK Web UI on http://localhost:8080..."
    adk web --port 8080 .
else
    echo "Starting ADK CLI..."
    adk run .
fi
