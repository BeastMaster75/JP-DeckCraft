"""
Default, empty curriculum.

Use this as the starting point for your own material: build_anki.py runs
correctly with all four of these empty, it just won't have any per-word image
overrides, skip list, extra mined vocabulary, or English-translation
overrides. Copy this file, rename it, fill it in as you go, and point
config.py's CURRICULUM_MODULE at it.
"""

# Per-(lesson, word) いらすとや search term overrides, e.g.:
#   TERM_OVERRIDE = {(3, "はいります"): "教室"}
TERM_OVERRIDE = {}

# Words to exclude from the deck, e.g.:
#   SKIP = {"ホテル": "katakana-transparent"}
SKIP = {}

# Extra vocabulary rows mined from example sentences, keyed by lesson number:
#   EXTRA = {3: [{"word": "...", "kanji": "...", "meaning": "...", "example": "..."}]}
EXTRA = {}

# English translations for example sentences, keyed by (lesson, word), for note
# formats that don't carry their own ExampleEN column:
#   EXAMPLE_EN_OVERRIDE = {(3, "はいります"): "I enter the classroom."}
EXAMPLE_EN_OVERRIDE = {}
