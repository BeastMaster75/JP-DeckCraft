"""Check a candidate word list against every lesson already built.

Two things matter:
  * an identical word string in an earlier lesson would split review history;
  * a word that merely SHARES a search term inherits that lesson's image
    silently, which the coverage count never flags.
Also reports which lesson first teaches a word, so authored example sentences
can be checked against "this lesson or earlier".
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as B

lessons = {}
for n in list(range(1, 51)):
    label = f"Lesson {n:02d}"
    note = B.VAULT / f"{label}.md"
    if not note.exists():
        note = B.NOTES / f"{label}.md"
    if not note.exists():
        continue
    # EXTRA rows are real taught words (mined from example sentences, rule 8)
    # and MUST be folded in here, not just into `seen` below - otherwise
    # --lookup reports them as untaught. That is the exact question --lookup
    # exists to answer, so the gap could green-light a duplicate row or an
    # example sentence built on a word that is already in the deck.
    # Caught 2026-08-22: `--lookup とまります` said "not taught" while L12's
    # EXTRA has held 泊まります since the Lesson 12 rebuild.
    lessons[n] = B.parse_vocab(note) + B.EXTRA.get(n, [])

# word string -> lessons it appears in
seen = {}
for n, rows in lessons.items():          # already includes EXTRA
    for r in rows:
        seen.setdefault(r["word"], []).append(n)

if len(sys.argv) > 1 and sys.argv[1] == "--lookup":
    for w in sys.argv[2:]:
        hits = [(n, r) for n, rows in lessons.items() for r in rows
                if w in r["word"] or (r["kanji"] and w in r["kanji"])]
        print(f"\n{w}:")
        for n, r in hits:
            print(f"   L{n:02d}  {r['word']:<24} {r['kanji']:<20} {r['meaning']}")
        if not hits:
            print("   (not taught in any built lesson)")
    raise SystemExit

target = int(sys.argv[1]) if len(sys.argv) > 1 else 26
print(f"=== duplicate word strings involving Lesson {target} ===")
for word, ns in sorted(seen.items()):
    if len(ns) > 1 and target in ns:
        print(f"  {word:<28} lessons {ns}")

print(f"\n=== search terms Lesson {target} shares with an earlier lesson ===")
terms = {}
for n, rows in lessons.items():
    for r in rows:
        terms.setdefault(B.search_term(r["kanji"], r["word"]), []).append((n, r["word"]))
for t, hits in sorted(terms.items()):
    ns = {n for n, _ in hits}
    if target in ns and len(ns) > 1:
        print(f"  term {t!r}")
        for n, w in hits:
            print(f"       L{n:02d}  {w}")

print(f"\n=== Lesson {target} rows with a ［～］ context gloss (audit these) ===")
for r in lessons.get(target, []):
    if "～" in r["kanji"] or "～" in r["word"]:
        print(f"  {r['word']:<28} term={B.search_term(r['kanji'], r['word'])!r}")
