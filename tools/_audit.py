"""Scratch: list the chosen title and PNG path for each stand-in word.

Only covers terms that have a QUERY_OVERRIDE, i.e. the words whose picture is
an approximation rather than a literal match. Those are the ones worth looking
at with the Read tool; the score cannot tell you whether the picture is right.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as b
import irasutoya

IMG = re.compile(r'src="([^"]+)"')

for n in (int(a) for a in sys.argv[1:]):
    report, _ = b.build(n)
    print(f"\n===== LESSON {n} =====")
    for r in report:
        stand_in = (r["term"] in irasutoya.QUERY_OVERRIDE
                    or (n, r["word"]) in b.TERM_OVERRIDE)
        if not stand_in:
            continue
        m = IMG.search(r["img"])
        fname = m.group(1) if m else "(none)"
        print(f'{r["word"]}\t{r["meaning"]}\t{r["score"]}\t{r["title"]}\t{fname}')
