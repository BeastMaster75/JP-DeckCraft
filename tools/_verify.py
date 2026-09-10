"""Verify the built .apkg files rather than trusting the build log.

An .apkg is a zip: `media` is a JSON name map and `collection.anki2` is SQLite.
Note the `decks` table does not exist in this schema version - deck names live
in the col table's JSON.
"""
import hashlib
import json
import sqlite3
import tempfile
import zipfile
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "output" / "apkg"

# \xff\xf3 and \xff\xfb are both valid MPEG-1 Layer III frame syncs; an earlier
# check omitted one and wrongly flagged every mp3 in the deck as malformed.
MP3_SYNC = (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"\xff\xfa", b"ID3")

problems = []
print(f"{'lesson':>7} {'notes':>6} {'cards':>6} {'img':>7} {'uniq-img':>9} "
      f"{'audio':>7} {'guid':>6} {'MB':>5}")

for n in range(1, 51):
    path = OUT / f"日本語_Lesson{n:02d}_Vocabulary.apkg"
    if not path.exists():
        problems.append(f"L{n:02d}: package missing")
        continue

    with zipfile.ZipFile(path) as z:
        media = json.loads(z.read("media").decode("utf-8"))
        blobs = {name: z.read(name) for name in media}
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "c.anki2"
            db.write_bytes(z.read("collection.anki2"))
            con = sqlite3.connect(db)
            notes = con.execute("SELECT guid, flds, tags FROM notes").fetchall()
            cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
            con.close()

    words, guids, imgs, with_img, both_audio = [], set(), [], 0, 0
    for guid, flds, _tags in notes:
        f = flds.split("\x1f")
        words.append(f[0])
        guids.add(guid)
        if f[5].strip():
            with_img += 1
            imgs.append(f[5])
        if f[4].strip() and f[7].strip():
            both_audio += 1

    # Distinct images matter: without URL deduplication 冬 and 雪 both landed on
    # the same snowman and the two cards were visually identical.
    digests = set()
    for name, blob in blobs.items():
        fn = media[name]
        if fn.endswith(".png"):
            digests.add(hashlib.sha1(blob).hexdigest())
            if not blob.startswith(b"\x89PNG"):
                problems.append(f"L{n:02d}: {fn} is not a PNG")
        elif fn.endswith(".mp3"):
            if not blob.startswith(MP3_SYNC):
                problems.append(f"L{n:02d}: {fn} bad mp3 header {blob[:3]!r}")

    if len(guids) != len(notes):
        problems.append(f"L{n:02d}: {len(notes)-len(guids)} duplicate GUIDs")
    if len(set(words)) != len(words):
        dupes = [w for w in set(words) if words.count(w) > 1]
        problems.append(f"L{n:02d}: duplicate words {dupes}")
    if with_img != len(notes):
        problems.append(f"L{n:02d}: {len(notes)-with_img} notes without an image")
    if both_audio != len(notes):
        problems.append(f"L{n:02d}: {len(notes)-both_audio} notes missing audio")
    if cards != len(notes) * 2:
        problems.append(f"L{n:02d}: {cards} cards for {len(notes)} notes")

    mb = path.stat().st_size / 1024 / 1024
    print(f"{n:>7} {len(notes):>6} {cards:>6} {with_img:>7} {len(digests):>9} "
          f"{both_audio:>7} {len(guids):>6} {mb:>5.1f}")

print()
if problems:
    print(f"PROBLEMS ({len(problems)}):")
    for p in problems:
        print("  -", p)
else:
    print("all checks passed")
