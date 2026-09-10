"""Scratch: list every word and the title of the illustration chosen for it.

The score alone is not trustworthy - ソフト "software" scored 162, comfortably
above MIN_SCORE, on 車いすソフトボール (wheelchair softball). Titles are cheap to
audit in bulk; the images themselves are read only for the doubtful ones.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as b
import irasutoya

lines = []
for n in [7, 8, 9, 10, 11, 12, 13, 14, 15]:
    report, _ = b.build(n)
    lines.append(f"\n===== Lesson {n:02d} =====")
    for r in sorted(report, key=lambda x: x["score"] if x["score"] != "" else -99999):
        flag = "MISS " if not r["img"] else ("weak " if r["score"] < irasutoya.MIN_SCORE else "     ")
        lines.append(f'{flag}{r["word"]}\t{r["meaning"]}\tterm={r["term"]}'
                     f'\t{r["score"]}\t{r["title"]}')

(b.OUT / "logs").mkdir(parents=True, exist_ok=True)
out = b.OUT / "logs" / "_titles.txt"
out.write_text("\n".join(lines), encoding="utf-8")
print(f"-> {out}")
