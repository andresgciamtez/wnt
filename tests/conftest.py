"""Pytest configuration for Water Network Tools."""

from pathlib import Path
import sys


PLUGIN_PARENT = Path(__file__).resolve().parents[2]

if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))


