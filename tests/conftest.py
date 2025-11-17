from __future__ import annotations

import sys
from pathlib import Path


def _ensure_backend_on_path() -> None:
    root = Path(__file__).resolve().parents[1]
    backend_src = root / "src" / "backend"
    backend_path = str(backend_src)
    if backend_path not in sys.path:
        sys.path.append(backend_path)


_ensure_backend_on_path()
