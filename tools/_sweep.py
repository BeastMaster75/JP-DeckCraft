"""Scratch: build every lesson and collect the image problems in one report.

Fixing lesson by lesson wastes network round trips - gather the whole problem
set first, then batch-test the replacement queries.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import irasutoya
import build_anki as b

LESSONS = [7, 8, 9, 10, 11, 12, 13, 14, 15]
missing, weak = [], []

for n in LESSONS:
    report, _ = b.build(n)
    for r in report:
        if not r["img"]:
            missing.append((n, r))
        elif r["score"] < irasutoya.MIN_SCORE:
            weak.append((n, r))

lines = ["===== MISSING: no image at all ====="]
for n, r in missing:
    lines.append(f'L{n:02d}\t{r["word"]}\t{r["meaning"]}\tterm={r["term"]}')
lines.append(f"\n===== WEAK: below MIN_SCORE, likely a bad match =====")
for n, r in weak:
    lines.append(f'L{n:02d}\t{r["word"]}\t{r["meaning"]}\tterm={r["term"]}'
                 f'\t{r["score"]}\t{r["title"]}')
lines.append(f"\ntotals: {len(missing)} missing, {len(weak)} weak")

(b.OUT / "logs").mkdir(parents=True, exist_ok=True)
out = b.OUT / "logs" / "_sweep.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[-1:]))
print(f"-> {out}")
