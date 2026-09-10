# Japanese Anki Deck Builder

Builds Anki (`.apkg`) flashcard decks from a Markdown vocabulary table: it
generates Japanese TTS audio for each word and its example sentence, attaches
an いらすとや illustration where one honestly fits, and packages everything
into a nested deck.

## Quick start

```
git clone <this repo>
cd "日本語 Anki Decks"
pip install -r requirements.txt
```

Drop your own lesson notes into `notes/` (copy `notes/Lesson-template.md` and
rename it, e.g. `notes/Lesson 01.md`), then:

```
python build_anki.py 1
```

This writes `output/apkg/日本語_Lesson01_Vocabulary.apkg` (import it into
Anki) and `output/review/review_lesson01.html` (a self-contained page for
eyeballing every word next to its illustration before you commit to a deck).

## Note format

Only the `## Vocabulary` table is read; everything else in the file is yours.

```markdown
## Vocabulary

| Word | Kanji | Meaning | Example | ExampleEN |
| :--: | :---: | :-----: | :-----: | :-------- |
| たべますⅡ | 食べます | eat | あさごはんをたべます。 | I eat breakfast. |
| すし | | sushi | すしをたべます。 | I eat sushi. |
```

- The **Kanji** column can be left blank (katakana words, or words with no
  kanji).
- A trailing verb-group marker (Ⅰ/Ⅱ/Ⅲ) on **Word** is stripped automatically
  before the card is built or read aloud.

## Configuration

`config.py` ships with generic defaults: both the note vault and the
curriculum module point at the local, empty starting point (`notes/` and
`curriculum/blank.py`). To point at a different note folder, or to use a
curriculum module with your own image-search overrides/skip list, copy
`.env.example` to `.env` (gitignored, never committed) and edit it:

```
VAULT_DIR=C:\path\to\your\notes
CURRICULUM_MODULE=curriculum.my_curriculum
```

### Curriculum modules

A curriculum module supplies four names: `TERM_OVERRIDE` (per-word image
search overrides), `SKIP` (words to drop from the deck), `EXTRA` (extra
vocabulary mined from example sentences), and `EXAMPLE_EN_OVERRIDE` (English
translations, for note formats without their own translation column). Start
from `curriculum/blank.py` (all four empty - the pipeline runs fine without
any of them) and grow it as you go, or look at
`curriculum/minna_no_nihongo.py` for a full worked example.

## CLI usage

```
python build_anki.py 12              # build lesson 12
python build_anki.py 12 --no-images  # skip いらすとや lookup
python build_anki.py 12 --vault path/to/notes   # one-off vault override
```

## Kanji deck (optional, separate pipeline)

`build_kanji.py` is a second, self-contained builder for a kanji recognition
deck. It doesn't read the vocabulary notes or `config.py`'s curriculum
module - its own kanji list lives inline in the script (a `LESSONS` list of
5-kanji batches). It takes no arguments:

```
python build_kanji.py
```

This writes a single `output/apkg/漢字.apkg` (one flat deck, no per-batch
subdecks - re-running after adding kanji updates it in place) and
`output/review/review_kanji.html`. Stroke-order diagrams are fetched from
[KanjiVG](https://kanjivg.tagaini.net/) (CC BY-SA 3.0) and cached under
`cache/kanjivg/`. To add kanji, edit the `LESSONS` list at the top of the
script and rerun.

## Project layout

```
build_anki.py           main vocabulary deck pipeline
build_kanji.py          separate, self-contained kanji deck
irasutoya.py            いらすとや image search
config.py               path/curriculum defaults (.env overrides, gitignored)
curriculum/             per-textbook override data (blank.py, minna_no_nihongo.py)
notes/                  lesson notes (drop your own here)
tools/                  optional QA/debug helpers and card-design previews (see tools/README.md)
cache/, output/, logs/  gitignored, generated at build time
```

## Licensing note

Illustrations come from いらすとや and are for personal study only - please
don't redistribute `.apkg` files that bundle them (e.g. on AnkiWeb's shared
decks). The kanji deck's stroke-order diagrams come from KanjiVG (CC BY-SA
3.0) - see [Kanji deck](#kanji-deck-optional-separate-pipeline) above. Audio
is generated via gTTS (Google Translate's unofficial TTS endpoint) for
personal, non-commercial use. This repo's own code is licensed under Apache
2.0 (see `LICENSE`) and has no such restriction; the example Minna no Nihongo
curriculum data follows that textbook's lesson structure but isn't
affiliated with or endorsed by its publisher.
