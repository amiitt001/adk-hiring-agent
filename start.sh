#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

# Synchronize GEMINI_API_KEY and GOOGLE_API_KEY
if [ -n "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    export GOOGLE_API_KEY="$GEMINI_API_KEY"
elif [ -n "$GOOGLE_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    export GEMINI_API_KEY="$GOOGLE_API_KEY"
fi

echo "========================================================"
echo "🚀 ADK Hiring Agent Server Initializing"
echo "   Host: $HOST | Port: $PORT"
echo "========================================================"

if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY detected in environment variables!"
    echo "Starting ADK Web Server on ${HOST}:${PORT}..."
    exec adk web --host "$HOST" --port "$PORT" .
else
    echo "⚠️  No GEMINI_API_KEY found in environment variables."
    echo "Starting Setup Launcher on ${HOST}:${PORT}..."
    export PORT="$PORT"
    export HOST="$HOST"
    exec python3 launcher.py
fi
