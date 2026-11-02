"""Make the CROWN root importable, whichever directory pytest was started in."""
import sys
from pathlib import Path

CROWN_ROOT = str(Path(__file__).resolve().parents[3])
if CROWN_ROOT not in sys.path:
    sys.path.insert(0, CROWN_ROOT)
