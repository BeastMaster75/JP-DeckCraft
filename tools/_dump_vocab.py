"""Scratch: dump the parsed vocabulary of every lesson note, for planning."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as b

for n in [7, 8, 9, 10, 11, 13, 14, 15]:
    rows = b.parse_vocab(b.VAULT / f"Lesson {n:02d}.md")
    print(f"\n===== Lesson {n:02d} : {len(rows)} rows =====")
    for r in rows:
        mark = "  SKIP" if r["word"] in b.SKIP else ""
        print(f'{r["word"]}\t{r["kanji"]}\t{r["meaning"]}\t| term={b.search_term(r["kanji"], r["word"])}{mark}')
