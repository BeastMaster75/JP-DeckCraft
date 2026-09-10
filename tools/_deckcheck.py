"""Print the deck names and a sample note out of a built .apkg."""
import json, sqlite3, sys, tempfile, zipfile
from pathlib import Path

path = Path(sys.argv[1])
with tempfile.TemporaryDirectory() as td:
    with zipfile.ZipFile(path) as z:
        z.extract("collection.anki2", td)
    db = sqlite3.connect(Path(td) / "collection.anki2")

    try:
        decks = db.execute("select id, name from decks").fetchall()
        names = [n.replace("\x1f", "::") for _, n in decks]
    except sqlite3.OperationalError:
        col = db.execute("select decks from col").fetchone()[0]
        names = [d["name"] for d in json.loads(col).values()]

    print("decks:")
    for n in sorted(names):
        print("   ", n)

    rows = db.execute("select guid, flds from notes order by id").fetchall()
    print(f"\nnotes: {len(rows)}")
    for guid, flds in rows[:3]:
        f = flds.split("\x1f")
        print(f"    {guid}  word={f[0]!r}  Lesson={f[6]!r}")

    db.close()  # Windows will not delete the tempdir while the handle is open.
