# Tools

Optional QA/debug helpers used while building decks - none of these are
required to build your own deck with `build_anki.py`. Run them from the repo
root, e.g.:

```
python tools/_diag.py 16
python tools/_verify.py
python tools/_deckcheck.py output/apkg/日本語_Lesson16_Vocabulary.apkg
```

Most of them import `build_anki`/`irasutoya` from the repo root and operate on
whatever `config.py`/`.env` currently point at.

`card_preview.html` / `card_preview_kanji.html` are static, self-contained
previews of the card CSS/templates - open either directly in a browser to
eyeball design changes without needing Anki.
