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

if [ -z "$GEMINI_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
    echo "ERROR: GEMINI_API_KEY (or GOOGLE_API_KEY) must be configured in the deployment environment." >&2
    echo "The interactive launcher is local-only and is not exposed as a public setup endpoint." >&2
    exit 1
fi

echo "Starting ADK Web Server on ${HOST}:${PORT}..."
exec adk web --host "$HOST" --port "$PORT" adk_agents
