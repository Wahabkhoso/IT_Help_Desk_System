"""
paths.py
Resolves the application's base data directory (where the database and
generated reports live) so it works correctly both when running from
source (`python main.py`) and when packaged as a standalone .exe with
PyInstaller.

PyInstaller extracts a bundled app into a temporary folder that gets
deleted after the program closes, so writing the database there would
lose all data between runs. Instead, when frozen, data is kept in a
folder right next to the .exe (which persists on disk).
"""

import sys
import os


def get_app_dir():
    """Directory for persistent app data (database, reports, outbox)."""
    if getattr(sys, "frozen", False):
        # Running as a PyInstaller-built .exe
        return os.path.dirname(sys.executable)
    # Running from source: utils/paths.py -> project root is one level up
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))