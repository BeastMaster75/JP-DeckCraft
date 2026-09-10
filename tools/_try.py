"""Scratch: test candidate いらすとや queries against the live site in bulk.

Usage:  python _try.py queries.txt out.txt
        python _try.py 売る 販売          (ad-hoc, prints to stdout)

Input file is one query per line; blank lines and #comments ignored. Prints
the top few scored titles for each so a stand-in can be checked before it is
committed to QUERY_OVERRIDE - guessed queries very often return nothing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import irasutoya


def probe(q):
    try:
        raw = irasutoya._harvest(q)
    except Exception as exc:
        return f"{q}\t! FAILED {exc}"
    if not raw:
        return f"{q}\t-- NOTHING --"
    ranked = sorted(((irasutoya._score(t, q), t, u) for t, u in raw),
                    reverse=True)
    top = [f"{s}:{t}" for s, t, u in ranked[:3] if s > -9000]
    return f"{q}\t({len(raw)} hits)\t" + " | ".join(top)


args = sys.argv[1:]
if args and args[0].endswith(".txt"):
    queries = [l.strip() for l in Path(args[0]).read_text(encoding="utf-8").splitlines()]
    queries = [q for q in queries if q and not q.startswith("#")]
    out = Path(args[1]) if len(args) > 1 else None
    lines = []
    for i, q in enumerate(queries, 1):
        line = probe(q)
        lines.append(line)
        print(f"[{i}/{len(queries)}] {line}", flush=True)
        if out:
            out.write_text("\n".join(lines), encoding="utf-8")
else:
    for q in args:
        print(probe(q), flush=True)
