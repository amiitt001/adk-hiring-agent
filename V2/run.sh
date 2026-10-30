#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "ERROR: Google ADK requires Python 3.10 or newer." >&2
    exit 1
fi

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

# Check process environment first, then .env.
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ] \
   && { [ ! -f ".env" ] || ! grep -Eq '^[[:space:]]*(GEMINI_API_KEY|GOOGLE_API_KEY)=.+' .env 2>/dev/null; }; then
    echo "--------------------------------------------------------"
    echo "⚠️  No valid GEMINI_API_KEY found in .env"
    echo "Starting interactive setup launcher at http://localhost:8888..."
    echo "--------------------------------------------------------"
    python3 launcher.py
    exit 0
fi

if [ "$MODE" = "web" ]; then
    echo "Starting ADK Web UI on http://localhost:8080..."
    adk web --port 8080 adk_agents
else
    echo "Starting ADK CLI..."
    adk run adk_agents/hiring_agent
fi
