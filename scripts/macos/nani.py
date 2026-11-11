"""Compatibility entry point; implementation lives in modules."""
from pathlib import Path
import runpy
globals().update(runpy.run_path(str(Path(__file__).resolve().parents[2] / 'modules/macos-preferences/scripts/macos/nani.py'), run_name=__name__))
