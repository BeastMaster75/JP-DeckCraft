"""Scratch: report which words in a lesson got no image, or only a weak one."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as b
import irasutoya

n = int(sys.argv[1])
report, _ = b.build(n)
print("\n--- MISSING (no image at all) ---")
for r in report:
    if not r["img"]:
        print(f'{r["word"]}\t{r["meaning"]}\tterm={r["term"]}')
print("\n--- WEAK (below MIN_SCORE, an approximation) ---")
for r in report:
    if r["img"] and r["score"] < irasutoya.MIN_SCORE:
        print(f'{r["word"]}\t{r["meaning"]}\tterm={r["term"]}\t{r["score"]}\t{r["title"]}')
print("\n--- OK ---")
for r in report:
    if r["img"] and r["score"] >= irasutoya.MIN_SCORE:
        print(f'{r["word"]}\t{r["meaning"]}\tterm={r["term"]}\t{r["score"]}\t{r["title"]}')
