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

MODE="${1:-cli}"

if [ "$MODE" = "web" ]; then
    echo "Starting ADK Web UI..."
    adk web .
else
    echo "Starting ADK CLI..."
    adk run .
fi
