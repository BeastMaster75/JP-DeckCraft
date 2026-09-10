"""Scratch: drop cached rankings for specific terms only.

The whole image_cache must NOT be wiped between lessons - it holds hand-tuned
picks and re-fetching everything would lose them. This clears just the terms
whose query list has changed.

Usage:  python _invalidate.py 研究します 売ります
"""
import re
import sys
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "cache" / "image_cache"

for term in sys.argv[1:]:
    slug = re.sub(r"\W+", "_", term)
    for path in (CACHE / f"{slug}.cands.json", CACHE / f"irasutoya_{slug}.png"):
        if path.exists():
            path.unlink()
            print(f"removed {path.name}")
        else:
            print(f"absent  {path.name}")
