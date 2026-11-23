"""Vercel entrypoint.

Vercel looks for a top-level `app` at a supported entrypoint; src/legaloo/main.py
is not one. This shim puts src/ on the path and re-exports the real app.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from legaloo.main import app

__all__ = ["app"]
