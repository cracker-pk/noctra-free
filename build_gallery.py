#!/usr/bin/env python3
"""Build the local gallery catalog from the original image folders."""
from pathlib import Path
import subprocess
import sys
script = Path(__file__).with_name("enhance_wallpapers.py")
raise SystemExit(subprocess.call([sys.executable, str(script), *sys.argv[1:]]))
