"""Compose labelled contact sheets of a lesson's chosen illustrations.

The picture has to be looked at - the title and the score are not sufficient
to know it's a correct match. Reading 44 PNGs one at a time is slow, so this
tiles them into a few sheets that can be read in one go. Labels are the
English meaning, in a Latin font, so no CJK font is required.

Usage:  python _contact.py 26
"""
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import build_anki as b

CELL = 300
LABEL = 46
COLS = 4
ROWS = 6

IMG = re.compile(r'src="([^"]+)"')
try:
    FONT = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    FONT_N = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
except OSError:
    FONT = FONT_N = ImageFont.load_default()

n = int(sys.argv[1])
report, _ = b.build(n)
rows = [r for r in report if r["img"]]

sheets = []
for start in range(0, len(rows), COLS * ROWS):
    chunk = rows[start:start + COLS * ROWS]
    h = ((len(chunk) - 1) // COLS + 1) * (CELL + LABEL)
    sheet = Image.new("RGB", (COLS * CELL, h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, r in enumerate(chunk):
        col, row = i % COLS, i // COLS
        x, y = col * CELL, row * (CELL + LABEL)
        fname = IMG.search(r["img"]).group(1)
        im = Image.open(b.IMAGE_CACHE / fname).convert("RGBA")
        im.thumbnail((CELL - 16, CELL - 16))
        bg = Image.new("RGBA", im.size, "white")
        bg.alpha_composite(im)
        sheet.paste(bg.convert("RGB"),
                    (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
        draw.text((x + 6, y + CELL + 2), f"{start + i + 1}. {r['meaning'][:34]}",
                  fill="black", font=FONT_N)
        draw.text((x + 6, y + CELL + 22), r["term"][:24], fill="#777", font=FONT)
        draw.rectangle([x, y, x + CELL - 1, y + CELL + LABEL - 1], outline="#ccc")
    (b.OUT / "logs").mkdir(parents=True, exist_ok=True)
    path = b.OUT / "logs" / f"_contact_{n:02d}_{len(sheets) + 1}.png"
    sheet.save(path)
    sheets.append(path)
    print(f"-> {path.name}  ({len(chunk)} cells)")

print("\nindex map:")
for i, r in enumerate(rows, 1):
    print(f"{i:3d}  {r['word']}\t{r['meaning']}\t{r['title']}")
