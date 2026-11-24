"""Progress lines with elapsed minutes, flushed at once (a long run on GitHub Actions should never look frozen)."""
from __future__ import annotations

import time

_T0 = time.monotonic()


def say(msg: str) -> None:
    print(f"[{(time.monotonic() - _T0) / 60:5.1f} min] {msg}", flush=True)
