"""Shared runtime configuration for the ADK agents."""

import os

from dotenv import load_dotenv

load_dotenv()

# google-adk's Gemini provider reads GOOGLE_API_KEY. Keep the public-facing
# GEMINI_API_KEY name supported for existing deployments.
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
elif os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

DEFAULT_MODEL_NAME = "gemini-3.5-flash"
MODEL_NAME = os.getenv("MODEL_NAME", DEFAULT_MODEL_NAME).strip() or DEFAULT_MODEL_NAME
