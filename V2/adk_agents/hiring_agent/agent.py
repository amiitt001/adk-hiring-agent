"""Expose the project root agent using ADK's standard app-directory layout."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import root_agent  # noqa: E402

__all__ = ["root_agent"]
