"""
Resource path utilities for PyInstaller compatibility.

In development, read relative path
In production, read from MEIPASS temporary directory created by PyInstaller
"""

import sys
from pathlib import Path


def get_resource_path(relative_path):
    try:
        # PyInstaller's _MEIPASS tmporary folder
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Get relative path
        base_path = Path(__file__).parent
    
    return base_path / relative_path


# Convenience constants for common paths
ASSETS_PATH = get_resource_path("assets")
ICONS_PATH = get_resource_path("assets/icons")
CACHE_PATH = get_resource_path("cache.json")
