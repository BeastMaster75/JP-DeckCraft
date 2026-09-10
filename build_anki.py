"""
Build a Japanese vocabulary Anki .apkg deck from a Markdown lesson note.

Reads the `## Vocabulary` table out of a lesson note, filters out low-value
entries, generates Japanese TTS audio for both the word and its example
sentence, attaches an いらすとや illustration where one honestly fits, and
writes a nested .apkg.

Lesson notes are only ever read, never written. See config.py for where
notes are read from and README.md for the expected table format.

Usage:  python build_anki.py 12
"""

import hashlib
import html
import importlib
import re
import sys
from pathlib import Path

import genanki
from gtts import gTTS

import config
import irasutoya
from config import VAULT_DIR as VAULT, NOTES_DIR as NOTES

OUT = Path(__file__).parent
# Lessons 01-06 and 16-25 have no vault note. Their vocabulary is extracted from
# みんなの日本語 (translation volume) and the example sentences are written to
# match; those notes live here, because the vault is read-only to this tooling.
CACHE = OUT / "cache"
AUDIO_CACHE = CACHE / "media_cache"
IMAGE_CACHE = CACHE / "image_cache"
APKG_OUT = OUT / "output" / "apkg"
REVIEW_OUT = OUT / "output" / "review"

# Curriculum-specific data (per-word image search overrides, skip list,
# extra mined vocabulary, English translation overrides) lives in a
# swappable module - see config.CURRICULUM_MODULE and curriculum/blank.py.
_curriculum = importlib.import_module(config.CURRICULUM_MODULE)
TERM_OVERRIDE = _curriculum.TERM_OVERRIDE
SKIP = _curriculum.SKIP
EXTRA = _curriculum.EXTRA
EXAMPLE_EN_OVERRIDE = _curriculum.EXAMPLE_EN_OVERRIDE


# Stable ids. Never change these or Anki will treat rebuilt decks as new ones.
MODEL_ID = 1607392319
DECK_ID_BASE = 2059400110

# The only parent deck. It carries the daily new-card limit; every deck under
# it is a flat leaf named "Lesson NN Vocabulary" with an unlimited limit.
DECK_PARENT = "みんなの日本語"


# Lessons 14 and 15 tag each verb with its conjugation group as a Roman
# numeral glued to the word: つけますⅡ, けしますⅠ, コピーしますⅢ. That is note
# metadata, not part of the word - it would be printed on the card and read
# aloud by gTTS. The group stays recoverable from the vault note.
VERB_GROUP = re.compile(r"[ⅠⅡⅢⅣⅤⅠ-Ⅴ]")


def strip_md(text):
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    return text.strip()


def tts_text(word):
    """かんたん[な] -> かんたん ; ［お］まつり -> おまつり ;
    さんかします［パーティーに～］ -> さんかします

    Context-gloss brackets (anything containing ～/~) are dropped whole, not
    just unwrapped - gTTS was reading "さんかしますパーティーに～" as one
    nonsense run-on. This mirrors search_term's handling of the same brackets.
    """
    word = re.sub(r"[［\[][^］\]]*[～~][^］\]]*[］\]]", "", word)
    word = re.sub(r"[［\[]\s*な\s*[］\]]", "", word)
    word = re.sub(r"[［］\[\]]", "", word)
    return word.strip()


def search_term(kanji, word):
    """Pick the best string to search いらすとや with.

    簡単［な］ -> 簡単 ; 速い／早い -> 速い ; 多い［人が～］ -> 多い
    """
    base = kanji or word
    base = base.split("／")[0].split("/")[0]
    base = re.sub(r"[［\[][^］\]]*[～~][^］\]]*[］\]]", "", base)
    base = re.sub(r"[［\[]\s*な\s*[］\]]", "", base)
    base = re.sub(r"[［］\[\]]", "", base)
    base = base.strip()
    if not base:
        # The whole kanji cell was a bracketed context gloss, as in
        # います［子どもが～］ whose kanji column is just ［子どもが～］. Fall
        # back to the kana word with its own bracket stripped.
        base = re.sub(r"[［\[][^］\]]*[］\]]", "", word).strip()
    return base


def parse_vocab(note_path):
    lines = note_path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip().startswith("## Vocabulary"))
    rows = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped.startswith("## ") or stripped == "---":
            break
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if set(cells[0]) <= set(":- ") or strip_md(cells[0]).lower() == "word":
            continue
        while len(cells) < 5:
            cells.append("")
        word, kanji, meaning, example, example_en = (strip_md(c) for c in cells[:5])
        word = VERB_GROUP.sub("", word).strip()
        if not word:
            continue
        if kanji in ("ー", "-", "—"):
            kanji = ""
        rows.append({"word": word, "kanji": kanji, "meaning": meaning,
                     "example": example, "example_en": example_en})
    return rows


def make_audio(text):
    AUDIO_CACHE.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    filename = f"jpvocab_{digest}.mp3"
    path = AUDIO_CACHE / filename
    if not path.exists():
        gTTS(text, lang="ja").save(str(path))
    return filename, path


CSS = """
.card {
  font-family: "Yu Gothic UI", "Hiragino Kaku Gothic ProN", "Noto Sans JP",
               "Meiryo", sans-serif;
  background: #eef1f7;
  padding: 0;
  margin: 0;
  --sheet:  #ffffff;
  --ink:    #1b1c22;
  --muted:  #71727d;
  --accent: #4f6bd8;
  --accent-soft: #eaeefc;
  --jade:   #157f5f;
  --jade-soft: #e6f5ef;
  --line:   #e2e5ee;
  --shadow: 0 1px 2px rgba(20,25,50,.06), 0 12px 34px rgba(20,25,50,.10);
}
.nightMode.card {
  background: #16171c;
  --sheet:  #22242c;
  --ink:    #eceef4;
  --muted:  #9a9cab;
  --accent: #8ba4ff;
  --accent-soft: #2b3150;
  --jade:   #5fce9f;
  --jade-soft: #1e3630;
  --line:   #32353f;
  --shadow: 0 1px 2px rgba(0,0,0,.3), 0 14px 36px rgba(0,0,0,.45);
}

.wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  padding: 20px 14px;
}
.sheet {
  background: var(--sheet);
  border-radius: 20px;
  box-shadow: var(--shadow);
  width: 100%;
  max-width: 620px;
  padding: 34px 28px 26px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
/* thin accent ribbon along the top edge */
.sheet::before {
  content: "";
  position: absolute; inset: 0 0 auto 0; height: 4px;
  background: linear-gradient(90deg, var(--accent), var(--jade));
}

.jp {
  font-size: clamp(44px, 12vw, 66px);
  font-weight: 700;
  line-height: 1.25;
  color: var(--ink);
  letter-spacing: .02em;
}
.reading {
  font-size: clamp(22px, 6vw, 29px);
  color: var(--accent);
  font-weight: 600;
  margin-top: 8px;
  letter-spacing: .04em;
}
.meaning {
  font-size: clamp(21px, 5.6vw, 28px);
  color: var(--ink);
  font-weight: 600;
  line-height: 1.4;
}
.kanji-line {
  display: inline-block;
  margin-top: 12px;
  padding: 5px 15px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: clamp(18px, 4.6vw, 23px);
  font-weight: 600;
}

.example {
  margin-top: 22px;
  padding: 14px 16px;
  background: var(--jade-soft);
  border-left: 4px solid var(--jade);
  border-radius: 0 12px 12px 0;
  color: var(--jade);
  font-size: clamp(19px, 4.8vw, 25px);
  line-height: 1.65;
  text-align: left;
}
.example-en {
  margin-top: 6px;
  color: var(--muted);
  font-size: 0.68em;
  font-weight: 400;
  font-style: italic;
  line-height: 1.5;
}

.pic { margin-top: 20px; }
.pic img {
  max-width: 78%;
  max-height: 220px;
  width: auto; height: auto;
  border-radius: 14px;
  background: #fff;
  padding: 8px;
  border: 1px solid var(--line);
}

.rule {
  border: none;
  border-top: 1px solid var(--line);
  margin: 22px 0 20px;
}
.chip {
  display: inline-block;
  margin-top: 24px;
  font-size: 12px;
  letter-spacing: .13em;
  text-transform: uppercase;
  color: var(--muted);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 13px;
}
.prompt {
  font-size: 12px;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 18px;
}
ruby rt { font-size: .5em; color: var(--muted); font-weight: 500; }
.replay-button svg { width: 22px; height: 22px; }
"""

# Card 1 - "I see this Japanese word, what does it mean?"
# Front plays the word. Back plays the example sentence, so the audio on the
# answer covers the whole answer rather than repeating what was already shown.
RECOGNITION_FRONT = """
<div class="wrap"><div class="sheet">
  <div class="prompt">意味は？</div>
  <div class="jp">{{#Kanji}}{{Kanji}}{{/Kanji}}{{^Kanji}}{{Word}}{{/Kanji}}</div>
  {{Audio}}
</div></div>
"""

RECOGNITION_BACK = """
<div class="wrap"><div class="sheet">
  <div class="jp">{{#Kanji}}{{Kanji}}{{/Kanji}}{{^Kanji}}{{Word}}{{/Kanji}}</div>
  {{#Kanji}}<div class="reading">{{Word}}</div>{{/Kanji}}
  <hr class="rule">
  <div class="meaning">{{Meaning}}</div>
  {{#Image}}<div class="pic">{{Image}}</div>{{/Image}}
  {{#Example}}<div class="example">{{Example}}{{#ExampleEN}}<div class="example-en">{{ExampleEN}}</div>{{/ExampleEN}}</div>{{/Example}}
  <div class="chip">{{Lesson}}</div>
  {{#ExampleAudio}}{{ExampleAudio}}{{/ExampleAudio}}
  {{^ExampleAudio}}{{Audio}}{{/ExampleAudio}}
</div></div>
"""

# Card 2 - "I mean this, can I produce the Japanese?"
# No audio on the front; it would hand over the answer.
RECALL_FRONT = """
<div class="wrap"><div class="sheet">
  <div class="prompt">日本語で？</div>
  <div class="meaning">{{Meaning}}</div>
  {{#Image}}<div class="pic">{{Image}}</div>{{/Image}}
</div></div>
"""

RECALL_BACK = """
<div class="wrap"><div class="sheet">
  <div class="meaning">{{Meaning}}</div>
  <hr class="rule">
  <div class="jp">{{Word}}</div>
  {{#Kanji}}<div class="kanji-line">{{Kanji}}</div>{{/Kanji}}
  {{#Example}}<div class="example">{{Example}}{{#ExampleEN}}<div class="example-en">{{ExampleEN}}</div>{{/ExampleEN}}</div>{{/Example}}
  <div class="chip">{{Lesson}}</div>
  {{Audio}}
  {{ExampleAudio}}
</div></div>
"""

MODEL = genanki.Model(
    MODEL_ID,
    "JP Vocab (vault)",
    fields=[
        {"name": "Word"},
        {"name": "Kanji"},
        {"name": "Meaning"},
        {"name": "Example"},
        {"name": "Audio"},
        {"name": "Image"},
        {"name": "Lesson"},
        {"name": "ExampleAudio"},
        {"name": "ExampleEN"},      # appended last so existing ordinals hold
    ],
    templates=[
        {"name": "Recognition JP-EN", "qfmt": RECOGNITION_FRONT,
         "afmt": RECOGNITION_BACK},
        {"name": "Recall EN-JP", "qfmt": RECALL_FRONT, "afmt": RECALL_BACK},
    ],
    css=CSS,
)


class GuidNote(genanki.Note):
    @property
    def guid(self):
        return genanki.guid_for("jp-vocab", self.fields[6], self.fields[0])


def build(lesson_num, with_images=True):
    label = f"Lesson {lesson_num:02d}"
    note = VAULT / f"{label}.md"
    if not note.exists():
        note = NOTES / f"{label}.md"
    rows = parse_vocab(note) + EXTRA.get(lesson_num, [])
    kept = [r for r in rows if r["word"] not in SKIP]
    dropped = [r for r in rows if r["word"] in SKIP]

    # Flat deck names, one level under the parent - no `::Vocabulary` subdeck.
    # `label` stays zero-padded and is NOT part of the deck name: it feeds the
    # Lesson field and therefore the note GUID, so changing it would orphan
    # every existing card.
    deck = genanki.Deck(DECK_ID_BASE + lesson_num, f"{DECK_PARENT}::{label} Vocabulary")
    media, report = [], []
    used_urls = set()

    for row in kept:
        word_file, word_path = make_audio(tts_text(row["word"]))
        media.append(str(word_path))

        ex_tag = ""
        if row["example"]:
            ex_file, ex_path = make_audio(row["example"])
            media.append(str(ex_path))
            ex_tag = f"[sound:{ex_file}]"

        img_tag, img_title, img_score = "", "", ""
        term = TERM_OVERRIDE.get((lesson_num, row["word"])) or \
            search_term(row["kanji"], row["word"])
        if with_images and row["word"] not in irasutoya.NO_IMAGE:
            # One unavailable illustration must not abort the whole run; the
            # word is reported as a miss and picked up in the review pass.
            try:
                hit = irasutoya.pick(term, IMAGE_CACHE, used_urls,
                                     alias=tts_text(row["word"]))
                if hit:
                    img_score, img_title, url = hit
                    used_urls.add(url)
                    fname, fpath = irasutoya.fetch(term, url, IMAGE_CACHE)
                    media.append(str(fpath))
                    img_tag = f'<img src="{fname}">'
            except Exception as exc:
                print(f"    ! image failed for {row['word']} ({term}): {exc}")
                img_tag, img_title, img_score = "", "", ""

        report.append({
            "word": row["word"], "kanji": row["kanji"], "meaning": row["meaning"],
            "term": term, "img": img_tag, "title": img_title, "score": img_score,
            "skipped": row["word"] in irasutoya.NO_IMAGE,
        })

        deck.add_note(GuidNote(
            model=MODEL,
            fields=[
                html.escape(row["word"]),
                html.escape(row["kanji"]),
                html.escape(row["meaning"]),
                html.escape(row["example"]),
                f"[sound:{word_file}]",
                img_tag,
                label,
                ex_tag,
                html.escape(row.get("example_en") or
                            EXAMPLE_EN_OVERRIDE.get((lesson_num, row["word"]), "")),
            ],
            tags=["日本語", label.replace(" ", "-"), "vocabulary"],
        ))

    package = genanki.Package(deck)
    package.media_files = sorted(set(media))
    APKG_OUT.mkdir(parents=True, exist_ok=True)
    out_path = APKG_OUT / f"日本語_{label.replace(' ', '')}_Vocabulary.apkg"
    package.write_to_file(str(out_path))

    with_img = sum(1 for r in report if r["img"])
    print(f"{label}: {len(rows)} rows -> {len(kept)} kept, {len(dropped)} dropped")
    print(f"   {len(kept) * 2} cards | {len(package.media_files)} media files")
    print(f"   images: {with_img}/{len(kept)} matched")
    print(f"   -> {out_path}")
    return report, out_path


def write_review(report, lesson_num):
    """Emit a self-contained page showing every word next to the illustration
    chosen for it, so the matches can be eyeballed rather than trusted."""
    import base64

    cells = []
    for r in sorted(report, key=lambda x: (not x["img"], x["skipped"])):
        if r["img"]:
            fname = re.search(r'src="([^"]+)"', r["img"]).group(1)
            data = base64.b64encode((IMAGE_CACHE / fname).read_bytes()).decode()
            art = f'<img src="data:image/png;base64,{data}">'
            note = f'<div class="t">{html.escape(r["title"])}</div>'
            # Below the confidence bar the picture is a stand-in for an
            # abstract word, not a literal match - worth flagging for review.
            state = "ok" if r["score"] >= irasutoya.MIN_SCORE else "approx"
        elif r["skipped"]:
            art = '<div class="none">no image<br><small>excluded</small></div>'
            note = '<div class="t">deliberately left empty</div>'
            state = "skip"
        else:
            art = '<div class="none">no match</div>'
            note = '<div class="t">nothing scored high enough</div>'
            state = "miss"
        cells.append(
            f'<figure class="{state}">{art}'
            f'<figcaption><b>{html.escape(r["word"])}</b>'
            f'<span>{html.escape(r["meaning"])}</span>{note}</figcaption></figure>'
        )

    doc = f"""<!doctype html><meta charset="utf-8">
<title>Lesson {lesson_num:02d} image review</title>
<style>
 body{{font-family:"Yu Gothic UI",system-ui,sans-serif;background:#f4f6fb;
      margin:0;padding:32px;color:#1b1c22}}
 h1{{font-size:20px;margin:0 0 4px}}
 p.sub{{color:#71727d;margin:0 0 26px;font-size:14px}}
 .grid{{display:grid;gap:16px;
       grid-template-columns:repeat(auto-fill,minmax(190px,1fr))}}
 figure{{margin:0;background:#fff;border-radius:14px;padding:14px;text-align:center;
        box-shadow:0 1px 3px rgba(20,25,50,.08);border-top:3px solid #4f6bd8}}
 figure.approx{{border-top-color:#3f9e78}}
 figure.skip{{border-top-color:#c9ccd6;opacity:.72}}
 figure.miss{{border-top-color:#e0a03a}}
 figure img{{max-width:100%;max-height:135px}}
 .none{{height:135px;display:flex;flex-direction:column;align-items:center;
       justify-content:center;color:#9a9cab;font-size:13px}}
 figcaption{{margin-top:10px;font-size:13px;line-height:1.5}}
 figcaption b{{display:block;font-size:19px}}
 figcaption span{{display:block;color:#71727d;font-style:italic}}
 .t{{margin-top:6px;color:#9a9cab;font-size:11px}}
</style>
<h1>Lesson {lesson_num:02d} - illustration review</h1>
<p class="sub">Blue = direct match. Green = approximate stand-in for an abstract
word. Amber = nothing found at all. Images &copy; いらすとや (Takashi Mifune),
personal study use only.</p>
<div class="grid">{''.join(cells)}</div>"""

    REVIEW_OUT.mkdir(parents=True, exist_ok=True)
    path = REVIEW_OUT / f"review_lesson{lesson_num:02d}.html"
    path.write_text(doc, encoding="utf-8")
    print(f"   review -> {path}")
    return path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson", type=int, nargs="?", default=12,
                         help="Lesson number to build (default: 12)")
    parser.add_argument("--vault", type=Path, default=None,
                         help="Override the note vault/folder for this run only")
    parser.add_argument("--no-images", action="store_true",
                         help="Skip いらすとや image lookup")
    args = parser.parse_args()

    if args.vault:
        VAULT = args.vault

    rep, _ = build(args.lesson, with_images=not args.no_images)
    write_review(rep, args.lesson)
