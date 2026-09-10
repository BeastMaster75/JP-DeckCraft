"""Scratch: invalidate cached rankings for every term that now has an override.

The image cache must not be wiped wholesale - it holds Lesson 12's hand-tuned
picks and re-fetching everything would lose them. This clears exactly the terms
whose query list changed, plus any term that previously cached an empty result
(those are the words that came back with no image at all).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import irasutoya

CACHE = Path(__file__).resolve().parent.parent / "cache" / "image_cache"

targets = set(irasutoya.QUERY_OVERRIDE)

# Terms whose cached ranking is empty or was produced before the ~します rule.
for meta in CACHE.glob("*.cands.json"):
    term = meta.stem[:-6]
    try:
        cached = json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        cached = []
    if not cached:
        targets.add(term)
    elif term.endswith("します") and len(term) - 3 >= 2:
        targets.add(term)

removed = 0
for term in targets:
    slug = re.sub(r"\W+", "_", term)
    for path in (CACHE / f"{slug}.cands.json", CACHE / f"irasutoya_{slug}.png"):
        if path.exists():
            path.unlink()
            removed += 1

print(f"targets: {len(targets)}  files removed: {removed}")
print(f"remaining cands: {len(list(CACHE.glob('*.cands.json')))}")
