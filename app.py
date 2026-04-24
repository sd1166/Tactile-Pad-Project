"""Backward-compatible entry point for the Flask app.

Prefer ``pip install -e .`` then ``flask --app tactile.app run`` or ``python -m tactile``.
"""

from pathlib import Path
import sys

_SRC_ROOT = Path(__file__).resolve().parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from tactile.app import app

__all__ = ["app"]

if __name__ == "__main__":
    # use_reloader=False avoids two processes fighting over the USB serial port
    app.run(debug=True, use_reloader=False)

