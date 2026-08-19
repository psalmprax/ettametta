# conftest.py - ensures src is importable
import sys
from pathlib import Path

_src = str(Path(__file__).parent.parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)
    print(f"[conftest] Added {_src} to sys.path", file=sys.stderr)
