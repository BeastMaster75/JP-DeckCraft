"""Builds the 漢字 (kanji) deck — companion to build_anki.py's vocab decks, but
a separate note type, model id and deck so it never touches the validated vocab
pipeline.

ONE deck, one file, grown over time. Fares' call 2026-08-22, replacing a first
version that shipped 25 separate per-batch decks: "I meant all of them in one
deck, and this deck will be updated across time." So:

  * output is a single `output/apkg/漢字.apkg`, rebuilt in place;
  * the deck is a single flat `漢字` with no parent and no leaves, so its own
    daily limit is the only number to set - none of the parent-gate/leaf-limit
    juggling the vocab decks need;
  * note GUIDs key on the KANJI ALONE, not on its batch, so renumbering or
    regrouping batches as the list grows can never orphan a card. This is the
    one place the vocab deck's (lesson, word) GUID scheme is deliberately NOT
    copied - its lessons are pinned by a textbook, these batches are not.

To add kanji: append to LESSONS, rerun `python build_kanji.py`, reimport. Notes
already in Anki update in place; only genuinely new characters come in as new
cards. Rebuild immediately before reimporting - a stale .apkg gets silently
skipped as "already present".

Recognition-only design, per Fares' call: one direction only, kanji shown ->
meaning recalled. No reverse "meaning -> kanji" card - Fares pointed out that
direction is mental production (recalling the exact character shape with
nothing on screen to check against) even without a handwriting canvas, which
is exactly what recognition-only was chosen to avoid. Card layout mirrors the
vocab deck's CSS (sheet/jp/reading) so the two decks feel like one system.

121 kanji in 25 batches of 5 (batch 25 currently holds just 1 - 糸 - matching
Fares' own list, which is a work in progress). Batches 6-9 and 11-14 (rows
matching his list) reuse the readings/compounds already authored in the vault
notes' own "## Kanji" tables (notes/Lesson 07-15.md except 11, which was
blank) - those are guaranteed already-taught vocabulary. Every other kanji's
compounds are standard/common Japanese, cross-checked by eye against the vocab
notes where the word was recognisable, but not exhaustively grepped one by one.

The batch number survives only as a tag (`漢字-01`) for browser filtering; it
is not shown on the card, since with a single deck a "Kanji 01" chip would
point at a deck that no longer exists.
"""
import html
import re
import time
import urllib.request
from pathlib import Path

import genanki

OUT = Path(__file__).parent
APKG_OUT = OUT / "output" / "apkg"
REVIEW_OUT = OUT / "output" / "review"

# --------------------------------------------------------------------------
# Stroke-order diagrams come from KanjiVG (https://kanjivg.tagaini.net/),
# Copyright (C) 2009-2011 Ulrich Apel, licensed CC BY-SA 3.0. Files are cached
# locally on first run and never refetched.
#
# They are INLINED into the note rather than shipped as 121 media files, for
# two reasons: (1) Fares' media sync to his phone is already struggling with
# 2700 files, and inlined SVG adds none - it rides along in the collection,
# which syncs as one compressed unit; (2) an <img src="x.svg"> is a separate
# document and cannot inherit the card's colour, so it would be invisible in
# dark mode. Inlined, the strokes use `currentColor` and follow the theme.
# --------------------------------------------------------------------------
KANJIVG_CACHE = OUT / "cache" / "kanjivg"
KANJIVG_URL = "https://raw.githubusercontent.com/KanjiVG/kanjivg/master/kanji/%05x.svg"

# Stable ids - never change these or Anki will treat rebuilds as new decks.
MODEL_ID = 1937004821
DECK_ID = 2059450000

# ONE deck, not a parent with per-batch leaves. Fares' call 2026-08-22: this is
# a single living deck that grows as he learns more kanji, so there is no
# parent/leaf split to manage and no per-leaf daily limit to get wrong - the
# deck's own limit is the only number. Rebuilding overwrites the same
# 漢字.apkg and updates notes in place (see GuidNote).
DECK_NAME = "漢字"

# --------------------------------------------------------------------------
# Data: 25 lessons of 5 kanji (kun, on, meaning, primitive breakdown,
# mnemonic, compounds). Kunyomi/Onyomi left "" when the kanji has no common
# reading of that kind (e.g. 気 has no standalone kun; 畑 is a kokuji with no
# on at all).
# --------------------------------------------------------------------------
LESSONS = [
  (1, [
    ("月", "つき", "ゲツ・ガツ", "Moon, month",
     "Pictograph — a crescent moon",
     "Picture the character as a crescent moon lying on its side, with two "
     "short strokes inside marking its craters. The moon rules the night "
     "sky, and lends its name to the month too — つき is both \"moon\" and "
     "(read differently) \"month.\"",
     [("月曜日","げつようび","Monday"), ("先月","せんげつ","last month"),
      ("今月","こんげつ","this month"), ("来月","らいげつ","next month"),
      ("何月","なんがつ","what month")]),
    ("火", "ひ", "カ", "Fire",
     "Pictograph — a flame throwing off two sparks",
     "A tongue of flame in the center kicks off two sparks, one to each "
     "side — 火 is a fire caught mid-flicker.",
     [("火曜日","かようび","Tuesday"), ("花火","はなび","fireworks")]),
    ("水", "みず", "スイ", "Water",
     "Pictograph — a current with droplets splashing off both sides",
     "A central stream with droplets flicked off to either side — this is "
     "water caught mid-splash.",
     [("水曜日","すいようび","Wednesday"), ("飲料水","いんりょうすい","drinking water")]),
    ("木", "き", "モク・ボク", "Tree, wood",
     "Pictograph — trunk with branches above, roots below",
     "A trunk with branches spreading upward and roots digging into the "
     "ground below — literally a little tree standing still.",
     [("木曜日","もくようび","Thursday"), ("木","き","tree, wood")]),
    ("金", "（お）かね", "キン・コン", "Gold, money, metal",
     "王 (king) buried under a roof, guarding two nuggets",
     "A king (王) sits under a little roof, guarding two gold nuggets at "
     "his feet — kings hoard treasure, so 金 means gold, and by extension, "
     "money.",
     [("金曜日","きんようび","Friday"), ("お金","おかね","money"),
      ("現金","げんきん","cash"), ("金額","きんがく","amount of money")]),
  ]),
  (2, [
    ("土", "つち", "ド・ト", "Soil, earth",
     "A plant (十) sprouting from a single baseline stroke",
     "A cross growing out of a single baseline — a little plant pushing up "
     "through the soil. 土 is earth itself.",
     [("土曜日","どようび","Saturday"), ("土地","とち","land")]),
    ("日", "ひ", "ニチ・ジツ", "Sun, day",
     "Pictograph — the sun, a disk with a ray inside",
     "A square sun with a single stroke inside — 日 is the sun, and by "
     "extension a day.",
     [("日曜日","にちようび","Sunday"), ("毎日","まいにち","every day"),
      ("今日","きょう","today"), ("日本","にほん","Japan")]),
    ("本", "もと", "ホン", "Book, origin, main",
     "木 (tree) with a stroke marking its very root",
     "A tree (木) with an extra stroke at its base, marking the root — the "
     "origin, the true foundation of the thing. From \"origin\" it grew to "
     "also mean \"book,\" the root of knowledge.",
     [("日本","にほん","Japan"), ("本","ほん","book"), ("本当","ほんとう","really")]),
    ("万", "", "マン・バン", "Ten thousand",
     "A flag planted on a mound",
     "A little flag planted on a mound — plant your flag once you've "
     "counted all the way to ten thousand.",
     [("一万円","いちまんえん","10,000 yen"), ("万年筆","まんねんひつ","fountain pen")]),
    ("円", "まる（い）", "エン", "Yen, circle, round",
     "儿 (a person) enclosed inside 冂 (a ring)",
     "A person (儿) enclosed inside a ring (冂) — curled into a perfect "
     "circle. 円 is round, and Japan's round coins gave it the meaning "
     "\"yen.\"",
     [("円","えん","yen"), ("千円","せんえん","1,000 yen"), ("円い","まるい","round")]),
  ]),
  (3, [
    ("百", "", "ヒャク", "Hundred",
     "一 (one) sack of 白 (white) rice",
     "One (一) hundred white (白) grains of rice packed into a single sack "
     "— 百 is a hundred.",
     [("百","ひゃく","hundred"), ("八百屋","やおや","greengrocer"),
      ("三百円","さんびゃくえん","300 yen")]),
    ("千", "", "セン", "Thousand",
     "人 (a person) with one extra stroke through the legs",
     "A person (人) with one extra line drawn through their legs — marking "
     "them as one in a thousand.",
     [("千円","せんえん","1,000 yen"), ("三千","さんぜん","three thousand")]),
    ("時", "とき", "ジ", "Time, hour",
     "日 (sun) beside 寺 (temple)",
     "The sun (日) moving past a temple (寺) — monks marked the hours by "
     "the sun's shadow on the temple grounds. 時 is time itself.",
     [("時間","じかん","time, hours"), ("何時","なんじ","what time"),
      ("時々","ときどき","sometimes")]),
    ("分", "わ（ける）", "フン・ブン", "Minute, part, understand",
     "刀 (a knife) splitting something into 八 (two parts)",
     "A knife (刀) splitting something into two parts (八) — 分 is to "
     "divide, and a divided hour gives you minutes.",
     [("一分","いっぷん","one minute"), ("半分","はんぶん","half"),
      ("自分","じぶん","oneself")]),
    ("半", "なか（ば）", "ハン", "Half",
     "八 (divide) splitting 十 (ten) down the middle",
     "Divide (八) a full ten (十) right down the middle — 半 is half.",
     [("半分","はんぶん","half"), ("一時半","いちじはん","half past one")]),
  ]),
  (4, [
    ("一", "ひと（つ）", "イチ", "One",
     "A single stroke",
     "A single horizontal stroke — the simplest possible way to draw "
     "\"one.\"",
     [("一つ","ひとつ","one thing"), ("一月","いちがつ","January"),
      ("一人","ひとり","one person, alone")]),
    ("二", "ふた（つ）", "ニ", "Two",
     "Two stacked strokes",
     "Two horizontal strokes stacked — as literal as counting gets.",
     [("二つ","ふたつ","two things"), ("二月","にがつ","February"),
      ("二人","ふたり","two people")]),
    ("三", "みっ（つ）", "サン", "Three",
     "Three stacked strokes",
     "Three horizontal strokes — one more line than 二, one less than "
     "starting to look silly.",
     [("三つ","みっつ","three things"), ("三月","さんがつ","March"),
      ("三人","さんにん","three people")]),
    ("四", "よっ（つ）", "シ", "Four",
     "儿 (legs) boxed in by 囗 (four walls)",
     "Legs (儿) boxed in on all sides (囗) — four walls closing in, four is "
     "the number.",
     [("四つ","よっつ","four things"), ("四月","しがつ","April"),
      ("四人","よにん","four people")]),
    ("五", "いつ（つ）", "ゴ", "Five",
     "乂 (a cross) wedged between two lines",
     "An X wedged between two lines, like five fingers crossed for luck — "
     "五 is five.",
     [("五つ","いつつ","five things"), ("五月","ごがつ","May"),
      ("五人","ごにん","five people")]),
  ]),
  (5, [
    ("六", "むっ（つ）", "ロク", "Six",
     "亠 (a roof) over 八 (spread legs)",
     "A little roof (亠) over two spread legs (八) — a hut with six sides. "
     "六 is six.",
     [("六つ","むっつ","six things"), ("六月","ろくがつ","June"),
      ("六人","ろくにん","six people")]),
    ("七", "なな（つ）", "シチ", "Seven",
     "A bent hook cross",
     "A cross with a hooked stem, like a scythe missing its handle — seven "
     "is the odd one out among the number kanji.",
     [("七つ","ななつ","seven things"), ("七月","しちがつ","July"),
      ("七人","しちにん","seven people")]),
    ("八", "やっ（つ）", "ハチ", "Eight",
     "Two strokes fanning apart",
     "Two strokes fanning apart like an open pair of chopsticks — 八 is "
     "eight.",
     [("八つ","やっつ","eight things"), ("八月","はちがつ","August"),
      ("八百屋","やおや","greengrocer")]),
    ("九", "ここの（つ）", "キュウ・ク", "Nine",
     "A hook curling back on itself",
     "A single stroke that curls back on itself almost to a full circle — "
     "nine, one short of a perfect loop of ten.",
     [("九つ","ここのつ","nine things"), ("九月","くがつ","September"),
      ("九人","きゅうにん","nine people")]),
    ("十", "とお", "ジュウ", "Ten",
     "A cross, vertical meeting horizontal dead center",
     "One line crossing another dead center — a perfect ten, complete in "
     "every direction.",
     [("十","じゅう","ten"), ("十月","じゅうがつ","October"),
      ("何十","なんじゅう","several tens")]),
  ]),
  (6, [  # = vault Lesson 07's Kanji table, verbatim
    ("手", "て", "シュ", "Hand",
     "Pictograph — an open hand and wrist",
     "An open palm with fingers splayed above a wrist — 手 is hand.",
     [("歌手","かしゅ","singer"), ("手紙","てがみ","letter"),
      ("上手な","じょうずな","skillful")]),
    ("父", "ちち", "フ", "Father",
     "Pictograph — a hand holding an axe or tool",
     "A raised hand gripping a tool — the head of the household at work. "
     "父 is father.",
     [("お父さん","おとうさん","father (polite)"), ("父母","ふぼ","father and mother")]),
    ("母", "はは", "ボ", "Mother",
     "Pictograph — a kneeling woman, two dots marking nursing breasts",
     "A kneeling figure with two marks on her chest — 母 is mother.",
     [("お母さん","おかあさん","mother (polite)"), ("母国","ぼこく","home country")]),
    ("花", "はな", "カ", "Flower",
     "艹 (grass) over 化 (change/transform)",
     "A plant (艹) transforming (化) from bud to bloom — 花 is flower.",
     [("花便","はなびん","flower delivery"), ("花火","はなび","fireworks")]),
    ("私", "わたし", "シ", "I, me",
     "禾 (grain) beside 厶 (a curled arm, \"my own\")",
     "Grain (禾) pulled in close to one's own curled arm (厶) — keeping "
     "something for yourself. 私 is \"I, me.\"",
     [("私立大学","しりつだいがく","private university")]),
  ]),
  (7, [  # = vault Lesson 08's Kanji table, verbatim (+ one spelling fix)
    ("大", "おお（きい）", "ダイ・タイ", "Large",
     "Pictograph — a person standing with arms stretched wide",
     "A person standing with both arms flung out wide, making themselves "
     "as big as possible — 大 is large.",
     [("大きい","おおきい","big"), ("大学","だいがく","university"),
      ("大人","おとな","adult"), ("大切","たいせつ","important")]),
    ("小", "ちい（さい）", "ショウ", "Small",
     "Pictograph — a tiny thing splitting into even tinier specks",
     "A single dot splitting into two smaller specks beside it — 小 is "
     "small.",
     [("小さい","ちいさい","small"), ("小川","おがわ","stream"),
      ("小学校","しょうがっこう","elementary school")]),
    ("新", "あたら（しい）", "シン", "New",
     "立+木 (a standing tree) beside 斤 (an axe)",
     "An axe (斤) beside a freshly standing tree (立木) — cut fresh wood, "
     "brand new. 新 is new.",
     [("新しい","あたらしい","new"), ("新聞","しんぶん","newspaper"),
      ("新車","しんしゃ","new car"), ("新年","しんねん","new year")]),
    ("古", "ふる（い）", "コ", "Old",
     "十 (ten) generations of 口 (mouths, i.e. voices) passed down",
     "Ten (十) generations of mouths (口) telling the same story — old "
     "enough to have been passed down for ages. 古 is old.",
     [("古い","ふるい","old"), ("中古車","ちゅうこしゃ","used car"),
      ("古本","ふるほん","secondhand book")]),
    ("聞", "き（きます）", "ブン", "Hear",
     "耳 (ear) at 門 (a gate), listening in",
     "An ear (耳) pressed right up against a gate (門) — 聞 is to hear, to "
     "listen.",
     [("聞きます","ききます","to hear, to listen"), ("新聞","しんぶん","newspaper")]),
  ]),
  (8, [  # = vault Lesson 09's Kanji table, verbatim
    ("上", "うえ", "ジョウ", "Above, on, up",
     "A short stroke sitting above a baseline",
     "A short mark perched above a long baseline — literally \"above.\" 上 "
     "is up.",
     [("上","うえ","above"), ("上り","のぼり","ascent"),
      ("上がる","あがる","to rise"), ("上手","じょうず","skillful")]),
    ("下", "した", "カ", "Under, down",
     "A short stroke sitting below a baseline",
     "A short mark hanging below a long baseline — literally \"below.\" 下 "
     "is down.",
     [("下","した","under"), ("地下","ちか","underground"),
      ("下がる","さがる","to fall"), ("下車","げしゃ","getting off (a train)")]),
    ("安", "やす（い）", "アン", "Peaceful, cheap",
     "宀 (a roof) over 女 (a woman)",
     "A woman (女) safe under her own roof (宀) — peace of mind. From "
     "\"peaceful\" it also came to mean an easy, cheap price. 安 is "
     "peaceful/cheap.",
     [("安い","やすい","cheap"), ("安心します","あんしんします","to feel relieved"),
      ("安全","あんぜん","safety")]),
    ("高", "たか（い）", "コウ", "High, expensive",
     "Pictograph — a tall tower with a base, body and roof",
     "A tall building drawn in three tiers, base to roof — 高 is high, "
     "and a high price is an expensive one.",
     [("高い","たかい","expensive, tall"), ("高校","こうこう","high school"),
      ("高速","こうそく","high speed")]),
    ("好", "す（き）", "コウ", "Like, favorable",
     "女 (a woman) beside 子 (a child)",
     "A mother (女) beside her child (子) — the most natural picture of "
     "affection there is. 好 is to like.",
     [("好き","すき","likeable, favorite"), ("好物","こうぶつ","favorite food")]),
  ]),
  (9, [  # = vault Lesson 10's Kanji table, verbatim
    ("女", "おんな", "ジョ", "Woman",
     "Pictograph — a kneeling figure with arms crossed gracefully",
     "A kneeling figure with arms folded gracefully in the lap — 女 is "
     "woman.",
     [("男女","だんじょ","men and women"), ("女性","じょせい","woman (formal)"),
      ("彼女","かのじょ","she, girlfriend"), ("女子","じょし","girl")]),
    ("男", "おとこ", "ダン", "Male",
     "田 (a rice field) topped by 力 (strength/muscle)",
     "Strength (力) applied out in the rice field (田) — the traditional "
     "picture of a man's labor. 男 is male.",
     [("男性","だんせい","man (formal)"), ("男子","だんし","boy"),
      ("長男","ちょうなん","eldest son")]),
    ("間", "あいだ", "カン", "Between",
     "門 (a gate) with 日 (the sun) shining through the gap",
     "Sunlight (日) slipping through the gap of a gate (門) — the space "
     "between two things. 間 is between.",
     [("日本間","にほんま","Japanese-style room"), ("人間","にんげん","human being"),
      ("時間","じかん","time")]),
    ("左", "ひだり", "サ", "Left",
     "A hand (ナ) holding a carpenter's square (工)",
     "A hand (ナ) steadying a carpenter's square (工) — traditionally held "
     "in the left hand while the right hand held the tool. 左 is left.",
     [("左手","ひだりて","left hand"), ("左側","ひだりがわ","left side"),
      ("左折禁止","させつきんし","no left turn")]),
    ("右", "みぎ", "ウ・ユウ", "Right",
     "A hand (ナ) beside a mouth (口)",
     "A hand (ナ) raised to the mouth (口) — the hand you'd naturally use "
     "to eat. 右 is right.",
     [("右手","みぎて","right hand"), ("左右確認","さゆうかくにん","checking left and right"),
      ("右側","みぎがわ","right side")]),
  ]),
  (10, [
    ("人", "ひと", "ジン・ニン", "Person",
     "Pictograph — two legs mid-stride",
     "Two legs mid-stride — the simplest picture of a person walking. 人 "
     "is person.",
     [("日本人","にほんじん","Japanese person"), ("外国人","がいこくじん","foreigner"),
      ("一人","ひとり","one person")]),
    ("国", "くに", "コク", "Country",
     "玉 (a king's jewel) sealed inside 囗 (a border)",
     "A king's jewel (玉) sealed inside a border wall (囗) — the treasure "
     "a nation protects within its borders. 国 is country.",
     [("外国","がいこく","foreign country"), ("中国","ちゅうごく","China"),
      ("国","くに","country")]),
    ("外", "そと", "ガイ", "Outside",
     "夕 (evening/moon) beside ト (a divining stick)",
     "Under the evening moon (夕), someone reads a fortune stick (ト) out "
     "in the open — 外 is outside.",
     [("外国","がいこく","foreign country"), ("外国人","がいこくじん","foreigner")]),
    ("中", "なか", "チュウ", "Middle, inside",
     "A vertical line piercing straight through a box",
     "A line driven straight through the center of a box — dead in the "
     "middle. 中 is inside/middle.",
     [("中国","ちゅうごく","China"), ("中","なか","inside"),
      ("一日中","いちにちじゅう","all day long")]),
    ("休", "やす（む）", "キュウ", "Rest",
     "人 (a person) leaning against 木 (a tree)",
     "A person (人) leaning back against a tree (木) — the classic picture "
     "of taking a rest. 休 is to rest.",
     [("休みます","やすみます","to rest, take a day off"),
      ("夏休み","なつやすみ","summer vacation"), ("休日","きゅうじつ","holiday")]),
  ]),
  (11, [  # = vault Lesson 12's Kanji table, verbatim
    ("多", "おお（い）", "タ", "Many, much",
     "夕 (evening) stacked twice",
     "Two evenings (夕) stacked one on the other — night after night after "
     "night, one after another. 多 is many.",
     [("多い","おおい","many"), ("多数","たすう","a large number"),
      ("多少","たしょう","somewhat")]),
    ("少", "すく（ない）・すこ（し）", "ショウ", "Few, little",
     "小 (small) with an extra downward stroke",
     "\"Small\" (小) shaved down even further by one more stroke — 少 is "
     "few, a little.",
     [("少ない","すくない","few"), ("少年","しょうねん","boy"),
      ("少女","しょうじょ","girl")]),
    ("学", "まな（ぶ）", "ガク", "Study, learn, school",
     "冖 (a roof) over 子 (a child) at a desk",
     "A child (子) sitting under a roof (冖), head bent over a desk — 学 "
     "is to study.",
     [("大学","だいがく","university"), ("学年","がくねん","school year"),
      ("学校","がっこう","school")]),
    ("生", "い（きる）・う（まれる）", "セイ・ショウ", "Live, be born, life",
     "Pictograph — a fresh shoot growing up out of the ground",
     "A young plant pushing up out of the soil, growing straight and new "
     "— 生 is to live, to be born.",
     [("生まれる","うまれる","to be born"), ("学生","がくせい","student"),
      ("生活","せいかつ","daily life"), ("誕生日","たんじょうび","birthday")]),
    ("先", "さき", "セン", "Ahead, previous",
     "土 (a plant sprout, 屮) walking on 儿 (legs)",
     "A shoot sprouting up out ahead of legs already walking — always the "
     "one out in front. 先 is ahead, previous.",
     [("先生","せんせい","teacher"), ("先週","せんしゅう","last week"),
      ("先月","せんげつ","last month"), ("先輩","せんぱい","senior")]),
  ]),
  (12, [  # = vault Lesson 13's Kanji table, verbatim
    ("行", "い（く）・おこな（う）", "コウ・ギョウ", "Go, act, line",
     "Pictograph — a crossroads seen from above",
     "A crossroads seen from above, paths branching left and right — pick "
     "a direction and go. 行 is to go, to act.",
     [("旅行","りょこう","travel"), ("行事","ぎょうじ","event"),
      ("二行目","にぎょうめ","second line")]),
    ("何", "なに・なん", "カ", "What, how many",
     "亻(person) beside 可 (a bent, questioning mouth)",
     "A person (亻) with a mouth twisted in a question (可) — always "
     "asking \"what?\" 何 is what.",
     [("何人","なんにん","how many people"), ("何年","なんねん","what year")]),
    ("食", "た（べる）", "ショク", "Eat, meal",
     "人 (a person) over 良 (good food)",
     "A person (人) bent over a good meal (良) below — 食 is to eat.",
     [("食堂","しょくどう","cafeteria"), ("食事","しょくじ","meal"),
      ("定食","ていしょく","set meal")]),
    ("飲", "の（む）", "イン", "Drink",
     "食 (eating) beside 欠 (an open, gasping mouth)",
     "An open, gasping mouth (欠) right next to a meal (食) — gulping "
     "something down. 飲 is to drink.",
     [("飲み物","のみもの","drink"), ("飲料水","いんりょうすい","drinking water")]),
    ("書", "か（く）", "ショ", "Write, book",
     "聿 (a hand holding a brush) over 日 (a flat surface)",
     "A hand gripping a brush (聿) pressed down onto a flat page (日) — "
     "書 is to write.",
     [("読書","どくしょ","reading"), ("図書館","としょかん","library"),
      ("書類","しょるい","documents")]),
  ]),
  (13, [  # = vault Lesson 14's Kanji table, verbatim
    ("今", "いま", "コン", "Now, this",
     "人 (a person) gathered under 一 (a single roof line)",
     "A person tucked under a single roof stroke, right here, right now — "
     "今 is \"now.\"",
     [("今年","ことし","this year"), ("今月","こんげつ","this month"),
      ("今日","きょう","today")]),
    ("読", "よ（む）", "ドク", "Read",
     "言 (words) beside 売 (a merchant crying out to sell)",
     "Words (言) called out loud like a merchant selling his wares (売) — "
     "読 is to read aloud.",
     [("読書","どくしょ","reading"), ("読者","どくしゃ","reader")]),
    ("語", "", "ゴ", "Language",
     "言 (words) beside 吾 (\"I, myself\")",
     "The words (言) that come out of my own (吾) mouth — a language. 語 "
     "is language.",
     [("日本語","にほんご","Japanese language"), ("英語","えいご","English language"),
      ("中国語","ちゅうごくご","Chinese language")]),
    ("入", "はい（る）・い（れる）", "ニュウ", "Enter, put in",
     "Pictograph — a wedge or tent-flap pushing inward",
     "A wedge shape pointing in and down, like pushing through a tent "
     "flap — 入 is to enter, to put in.",
     [("入る","はいる","to enter"), ("入口","いりぐち","entrance"),
      ("入学","にゅうがく","school enrollment")]),
    ("出", "で（る）・だ（す）", "シュツ・シュッ", "Go out, put out",
     "山 (a mountain) stacked on another peak, pushing upward",
     "One peak pushing up over another — bursting up and out. 出 is to "
     "go out.",
     [("出す","だす","to put out"), ("出口","でぐち","exit"),
      ("外出","がいしゅつ","going out")]),
  ]),
  (14, [  # = vault Lesson 15's Kanji table, verbatim
    ("見", "み（る）", "ケン", "See, watch",
     "目 (an eye) on top of 儿 (legs)",
     "A big eye (目) carried around on a pair of legs (儿) — going places "
     "just to look. 見 is to see.",
     [("見学する","けんがくする","to observe, tour"), ("発見する","はっけんする","to discover")]),
    ("会", "あ（う）", "カイ", "Meet, association",
     "人 (a person) over 云 (clouds/gathering, a lid meeting a base)",
     "A lid (人) closing perfectly down over its base (云) — two halves "
     "meeting exactly. 会 is to meet.",
     [("会社","かいしゃ","company"), ("会話","かいわ","conversation")]),
    ("話", "はな（す）・はなし", "ワ", "Speak, talk",
     "言 (words) beside 舌 (a tongue)",
     "Words (言) wagging off a tongue (舌) — 話 is to speak.",
     [("会話","かいわ","conversation"), ("電話","でんわ","telephone")]),
    ("社", "", "シャ", "Company, society",
     "示 (an altar) beside 土 (earth/land)",
     "An altar (示) set up on the local land (土) — the shared community "
     "gathered around it. 社 is company, society.",
     [("会社","かいしゃ","company"), ("社会","しゃかい","society"),
      ("社長","しゃちょう","company president")]),
    ("教", "おし（える）", "キョウ", "Teach",
     "孝 (filial devotion, a child under an elder) beside 攵 (a hand with "
     "a stick)",
     "An elder guiding a child (孝), stick in hand (攵) to keep them in "
     "line — the old way of teaching. 教 is to teach.",
     [("教育","きょういく","education"), ("教室","きょうしつ","classroom")]),
  ]),
  (15, [
    ("体", "からだ", "タイ", "Body",
     "亻(person) beside 本 (root, origin)",
     "A person (亻) next to their own root (本) — your body is your "
     "origin, the base of you. 体 is body.",
     [("体","からだ","body"), ("体育","たいいく","physical education"),
      ("体調","たいちょう","physical condition")]),
    ("足", "あし・た（りる）", "ソク", "Foot, leg, sufficient",
     "口 (a knee) planted above 止 (a foot)",
     "A knee (口) planted above a foot (止) — a whole leg, joint to sole. "
     "足 is foot/leg, and having two good legs means you have \"enough.\"",
     [("足りる","たりる","to be sufficient"), ("一足","いっそく","one pair (shoes)")]),
    ("目", "め", "モク", "Eye",
     "Pictograph — an eye tipped on its side",
     "A rectangle with two bars across it, like an eye tipped on its side "
     "— 目 is eye.",
     [("目的","もくてき","purpose"), ("三日目","みっかめ","the third day")]),
    ("耳", "みみ", "ジ", "Ear",
     "Pictograph — the curled outer shape of an ear",
     "A curling, ridged outline — trace the shape of an ear. 耳 is ear.",
     [("耳鼻科","じびか","ENT clinic")]),
    ("口", "くち", "コウ・ク", "Mouth",
     "Pictograph — a plain open square",
     "A plain open square — the simplest picture of an open mouth. 口 is "
     "mouth, and also \"opening\" more generally.",
     [("入口","いりぐち","entrance"), ("出口","でぐち","exit")]),
  ]),
  (16, [
    ("来", "く（る）・きた", "ライ", "Come",
     "木 (a tree) with grain hanging heavy on both sides",
     "Grain hanging heavy on both sides of a tree — harvest has come. 来 "
     "means to come.",
     [("来ます","きます","to come"), ("来月","らいげつ","next month"),
      ("来年","らいねん","next year")]),
    ("長", "なが（い）", "チョウ", "Long, chief",
     "Pictograph — an elder with long flowing hair, leaning on a cane",
     "An old man with long flowing hair, leaning on his cane — age makes "
     "both the hair and the walk long, and elders become the chief. 長 is "
     "long, and also \"head, chief.\"",
     [("長い","ながい","long"), ("社長","しゃちょう","company president"),
      ("長男","ちょうなん","eldest son")]),
    ("短", "みじか（い）", "タン", "Short",
     "矢 (an arrow) beside 豆 (a squat bean-pot)",
     "An arrow (矢) next to a squat little bean-pot (豆) — both short, "
     "stubby things. 短 means short.",
     [("短い","みじかい","short"), ("短期","たんき","short-term")]),
    ("暗", "くら（い）", "アン", "Dark",
     "日 (sun) beside 音 (sound, a covered mouth)",
     "The sun (日) has gone quiet, muffled like a covered sound (音) — "
     "when the sun goes silent, it's dark. 暗 is dark.",
     [("暗い","くらい","dark"), ("暗記する","あんきする","to memorize")]),
    ("明", "あか（るい）", "メイ・ミョウ", "Bright",
     "日 (sun) beside 月 (moon)",
     "Sun (日) and moon (月) side by side, both shining at once — doubly "
     "bright. 明 is bright, clear.",
     [("明るい","あかるい","bright"), ("明日","あした","tomorrow")]),
  ]),
  (17, [
    ("前", "まえ", "ゼン", "Front, before",
     "A boat's prow — bow strokes over a hull, cutting forward",
     "A boat's prow cutting forward through the water — 前 is \"in "
     "front,\" the direction the bow always faces.",
     [("午前","ごぜん","a.m."), ("名前","なまえ","name")]),
    ("後", "うし（ろ）・あと", "ゴ・コウ", "Back, after",
     "幺 (a small child) trailing 夂 (dragging feet) on 彳 (the road)",
     "A small child (幺) dragging their feet (夂) along the road (彳) — "
     "always lagging behind. 後 is \"after, behind.\"",
     [("後ろ","うしろ","behind"), ("午後","ごご","p.m."), ("後で","あとで","later")]),
    ("年", "とし", "ネン", "Year",
     "千 (a thousand) stalks of 干 (dry grain)",
     "A thousand (千) stalks of dry grain (干) harvested — one full "
     "harvest cycle marks a year. 年 is year.",
     [("今年","ことし","this year"), ("毎年","まいとし","every year")]),
    ("馬", "うま", "バ", "Horse",
     "Pictograph — a flowing mane, sturdy body, four legs as dots",
     "A flowing mane on top, a sturdy body, and four legs trailing as dots "
     "underneath — a running horse drawn in one character. 馬 is horse.",
     [("馬","うま","horse"), ("競馬","けいば","horse racing")]),
    ("低", "ひく（い）", "テイ", "Low",
     "亻(person) beside 氐 (a base, a root)",
     "A person (亻) standing right at the very base (氐) of something — "
     "as low as you can get. 低 is low.",
     [("低い","ひくい","low"), ("最低","さいてい","the lowest, the worst")]),
  ]),
  (18, [
    ("山", "やま", "サン", "Mountain",
     "Pictograph — three peaks side by side",
     "Three peaks rising side by side — the simplest picture of a "
     "mountain range. 山 is mountain.",
     [("富士山","ふじさん","Mt. Fuji"), ("火山","かざん","volcano")]),
    ("物", "もの", "ブツ・モツ", "Thing",
     "牛 (an ox) beside 勿 (a fluttering banner)",
     "An ox (牛) standing beneath a fluttering banner (勿) at market — "
     "livestock and goods alike are \"things\" for sale. 物 means thing.",
     [("飲み物","のみもの","drink"), ("買い物","かいもの","shopping")]),
    ("子", "こ", "シ", "Child",
     "Pictograph — a swaddled baby, arms out, legs wrapped",
     "A baby's head on top, arms spread, legs wrapped together below — 子 "
     "is child.",
     [("子供","こども","child"), ("男の子","おとこのこ","boy"), ("女の子","おんなのこ","girl")]),
    ("茶", "", "チャ・サ", "Tea",
     "艹 (a plant) growing between 人 and 木 (a person and a tree)",
     "A plant (艹) growing between a person (人) and a tree (木) — pluck "
     "its leaves and brew them. 茶 is tea.",
     [("お茶","おちゃ","tea"), ("茶色","ちゃいろ","brown"), ("喫茶店","きっさてん","café")]),
    ("買", "か（う）", "バイ", "Buy",
     "网 (a net) scooping up 貝 (shells, ancient currency)",
     "A net (网) scooping up shells (貝) — shells were once money, so "
     "netting them means buying. 買 is to buy.",
     [("買います","かいます","to buy"), ("買い物","かいもの","shopping")]),
  ]),
  (19, [
    ("車", "くるま", "シャ", "Car, vehicle",
     "Pictograph — a cart's wheels and axle, seen from above",
     "A box with a line straight through the middle and bars top and "
     "bottom — a cart's wheels and axle seen from above. 車 is vehicle.",
     [("電車","でんしゃ","train"), ("自転車","じてんしゃ","bicycle")]),
    ("名", "な", "メイ・ミョウ", "Name",
     "夕 (evening) beside 口 (a mouth)",
     "In the evening (夕) dark, you can't see someone's face, so you call "
     "out their name with your mouth (口) instead. 名 is name.",
     [("名前","なまえ","name"), ("有名","ゆうめい","famous")]),
    ("元", "もと", "ゲン・ガン", "Origin, former",
     "儿 (a person) standing firm on 二 (two solid lines)",
     "A person (儿) standing on two firm lines (二) at the very start of "
     "the path — 元 is the origin, where you first stood.",
     [("元気","げんき","healthy, energetic"), ("地元","じもと","home area")]),
    ("気", "", "キ・ケ", "Spirit, energy",
     "气 (rising steam) wrapping around 米 (rice)",
     "Steam (气) rising off a pot of cooking rice (米) — invisible energy "
     "escaping into the air. 気 is spirit, energy.",
     [("元気","げんき","healthy"), ("天気","てんき","weather"), ("病気","びょうき","illness")]),
    ("電", "", "デン", "Electricity",
     "雨 (rain clouds) with lightning striking over 田 (a field)",
     "Rain clouds (雨) crackle over a field (田) as lightning strikes — 電 "
     "is electricity, born from a storm.",
     [("電車","でんしゃ","train"), ("電話","でんわ","telephone"),
      ("電気","でんき","electricity")]),
  ]),
  (20, [
    ("力", "ちから", "リョク・リキ", "Power, strength",
     "Pictograph — a flexed arm",
     "A single curved stroke like a flexed arm — 力 is strength, power.",
     [("力","ちから","strength"), ("協力","きょうりょく","cooperation")]),
    ("雨", "あめ", "ウ", "Rain",
     "Pictograph — drops falling under a roof line",
     "A roof line up top with drops falling beneath it — rain caught "
     "mid-fall. 雨 is rain.",
     [("雨","あめ","rain"), ("大雨","おおあめ","heavy rain")]),
    ("友", "とも", "ユウ", "Friend",
     "Two hands (ナ + 又) clasped together",
     "Two hands reaching in and clasping one another — 友 is friend.",
     [("友達","ともだち","friend"), ("親友","しんゆう","close friend")]),
    ("方", "かた", "ホウ", "Direction, polite \"person\"",
     "A flag on a pole, pointing one way",
     "A flagpole with its banner streaming off to one side, pointing the "
     "way — 方 is direction, and politely, \"the person\" being pointed to.",
     [("使い方","つかいかた","how to use"), ("一方","いっぽう","one direction"),
      ("あの方","あのかた","that person (polite)")]),
    ("言", "い（う）・こと", "ゲン・ゴン", "Say, word",
     "口 (a mouth) with sound waves rising above it",
     "Sound waves rising straight up out of an open mouth (口) — 言 is to "
     "speak, a word.",
     [("言います","いいます","to say"), ("方言","ほうげん","dialect"),
      ("言葉","ことば","word, language")]),
  ]),
  (21, [
    ("石", "いし", "セキ・シャク", "Stone",
     "厂 (a cliff) over 口 (a boulder)",
     "A boulder (口) sitting at the base of a cliff (厂) — 石 is stone.",
     [("石","いし","stone"), ("石鹸","せっけん","soap")]),
    ("肉", "", "ニク", "Meat",
     "冂 (an outline) around ribs of fat and muscle",
     "A slab of meat, cross-cut so you can see its ribs of fat and muscle "
     "inside — 肉 is meat.",
     [("牛肉","ぎゅうにく","beef"), ("豚肉","ぶたにく","pork"), ("鳥肉","とりにく","chicken meat")]),
    ("魚", "さかな", "ギョ", "Fish",
     "Pictograph — head on top, boxy body, tail (灬) at bottom",
     "A fish drawn nose-down: head at top, a boxy body with fins, and a "
     "fanned tail (灬) at the bottom — 魚 is fish.",
     [("魚","さかな","fish"), ("魚市場","うおいちば","fish market")]),
    ("牛", "うし", "ギュウ", "Cow, ox",
     "Pictograph — a cow's head with one horn crossing the frame",
     "A cross with one horn poking up past the crossbar — a cow's head "
     "and horns seen from the front. 牛 is cow.",
     [("牛肉","ぎゅうにく","beef"), ("牛乳","ぎゅうにゅう","milk")]),
    ("鳥", "とり", "チョウ", "Bird",
     "Pictograph — a sharp eye on top, feathered tail (灬) below",
     "A bird standing tall, a sharp eye at top and tail feathers (灬) "
     "fanned at the bottom — 鳥 is bird.",
     [("鳥","とり","bird"), ("鳥肉","とりにく","chicken meat"), ("白鳥","はくちょう","swan")]),
  ]),
  (22, [
    ("店", "みせ", "テン", "Shop",
     "广 (a roof/building) over 占 (a claimed spot)",
     "A roof (广) built over a claimed spot (占) where a fortune-teller "
     "sets up shop — 店 is a store.",
     [("喫茶店","きっさてん","café"), ("店員","てんいん","shop clerk")]),
    ("川", "かわ", "セン", "River",
     "Pictograph — three flowing streams",
     "Three vertical strokes flowing side by side — a river's currents. "
     "川 is river.",
     [("川","かわ","river"), ("小川","おがわ","stream")]),
    ("立", "た（つ）", "リツ", "Stand",
     "Pictograph — a figure standing, arms out, feet on the ground",
     "A figure standing firmly with arms spread, feet planted on the "
     "ground line beneath — 立 is to stand.",
     [("立ちます","たちます","to stand"), ("国立","こくりつ","national"),
      ("立派","りっぱ","splendid")]),
    ("門", "かど", "モン", "Gate",
     "Pictograph — a double-leafed swinging gate",
     "Two matching panels swinging on a frame — a classic double gate. 門 "
     "is gate.",
     [("専門","せんもん","specialty"), ("校門","こうもん","school gate")]),
    ("帰", "かえ（る）", "キ", "Return",
     "帚 (a broom) set down, ready to head for the door",
     "Someone sets down their broom (帚) and heads for the door — "
     "sweeping done, time to go home. 帰 is to return.",
     [("帰ります","かえります","to go home"), ("帰国","きこく","returning to one's country")]),
  ]),
  (23, [
    ("田", "た", "デン", "Rice field",
     "Pictograph — a field divided into four plots",
     "A square divided into four even plots by a cross — a rice paddy "
     "seen from above. 田 is field.",
     [("田","た","rice field"), ("水田","すいでん","paddy field")]),
    ("米", "こめ", "ベイ・マイ", "Rice",
     "十 (a stalk) with grains scattered on four sides",
     "A central stalk with grains scattered to all four sides — rice "
     "ready for harvest. 米 is rice, and (from an old transliteration) "
     "also \"America.\"",
     [("米","こめ","rice"), ("新米","しんまい","new rice, rookie")]),
    ("畑", "はたけ", "", "Cultivated field",
     "火 (fire) beside 田 (a field)",
     "Fire (火) used to clear a field (田) before planting — a dry, "
     "burned field, not a flooded rice paddy. 畑 is a cultivated field. "
     "It's a kanji invented in Japan, so it has no Chinese reading.",
     [("畑","はたけ","field"), ("花畑","はなばたけ","flower field")]),
    ("字", "あざ", "ジ", "Character, letter",
     "宀 (a roof) over 子 (a child)",
     "A child (子) sheltered under a roof (宀), learning their letters at "
     "home — 字 is a written character.",
     [("漢字","かんじ","kanji"), ("習字","しゅうじ","calligraphy")]),
    ("文", "ふみ", "ブン・モン", "Sentence, writing, culture",
     "Pictograph — a person with crossed markings on their chest",
     "A person with an X marked across their chest, like patterned "
     "tattoos or writing on the body — 文 is writing, and by extension, "
     "culture.",
     [("文化","ぶんか","culture"), ("作文","さくぶん","composition")]),
  ]),
  (24, [
    ("岩", "いわ", "ガン", "Rock",
     "石 (stone) sitting on top of 山 (a mountain)",
     "A stone (石) sitting right on top of a mountain (山) — a big "
     "boulder. 岩 is rock.",
     [("岩","いわ","rock"), ("岩石","がんせき","rock, mineral")]),
    ("竹", "たけ", "チク", "Bamboo",
     "Pictograph — two bamboo stalks with leaves",
     "Two bamboo stalks side by side, each with leaves branching off — 竹 "
     "is bamboo.",
     [("竹","たけ","bamboo"), ("竹の子","たけのこ","bamboo shoot")]),
    ("林", "はやし", "リン", "Woods",
     "Two 木 (tree) side by side",
     "Two trees (木) standing together — enough trees to call it a small "
     "woods. 林 is woods.",
     [("林","はやし","woods"), ("森林","しんりん","forest")]),
    ("森", "もり", "シン", "Forest",
     "Three 木 (tree) stacked",
     "Three trees (木) together — more than a woods, now a whole forest. "
     "森 is forest.",
     [("森","もり","forest"), ("森林","しんりん","forest")]),
    ("貝", "かい", "", "Shell",
     "Pictograph — an open clam shell with legs peeking out",
     "An oval shell split by a line, with two little legs of a mollusk "
     "peeking out below — 貝 is shellfish, shell. Ancient shells were used "
     "as currency, which is why so many money-related kanji (買, for "
     "instance) contain it.",
     [("貝","かい","shellfish"), ("貝殻","かいがら","seashell")]),
  ]),
  (25, [
    ("糸", "いと", "シ", "Thread",
     "Pictograph — a skein of twisted thread, knotted at the bottom",
     "A tangle of thread looped and knotted at the bottom — 糸 is thread, "
     "string.",
     [("糸","いと","thread"), ("毛糸","けいと","knitting wool")]),
  ]),
]

# --------------------------------------------------------------------------
# Card design - shares the vocab deck's visual language (sheet/jp/reading/
# chip) so the two families read as one system. New classes: .mnemonic
# (blue, RTK-style primitive story) and .compounds-grid (aligned word/
# meaning columns, replacing an earlier wrapped-inline-text draft Fares
# rejected as "unordered and shit looking").
# --------------------------------------------------------------------------
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
  font-size: clamp(18px, 5vw, 23px);
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
.mnemonic {
  margin-top: 20px;
  padding: 14px 16px;
  background: var(--accent-soft);
  border-left: 4px solid var(--accent);
  border-radius: 0 12px 12px 0;
  color: var(--ink);
  font-size: clamp(15px, 3.6vw, 17px);
  line-height: 1.6;
  text-align: left;
}
.mnemonic .primitives {
  display: block;
  font-size: 12px;
  letter-spacing: .08em;
  text-transform: uppercase;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 6px;
}
.compounds {
  margin-top: 14px;
  padding: 14px 18px;
  background: var(--jade-soft);
  border-left: 4px solid var(--jade);
  border-radius: 0 12px 12px 0;
  text-align: left;
}
.compounds-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  column-gap: 18px;
  row-gap: 9px;
}
.compounds-grid .cw {
  color: var(--jade);
  font-weight: 700;
  font-size: clamp(16px, 4vw, 19px);
  white-space: nowrap;
}
.compounds-grid .cm {
  color: var(--muted);
  font-size: clamp(13px, 3.2vw, 15px);
  align-self: center;
}

/* Stroke-order diagram (inlined KanjiVG). `color` here is what the strokes
   pick up via currentColor, so the diagram follows light/dark automatically. */
.strokes { margin-top: 20px; text-align: center; }
.strokes-label {
  font-size: 11px;
  letter-spacing: .15em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}
.strokes .kvg {
  width: min(210px, 58%);
  height: auto;
  color: var(--ink);
  background: var(--sheet);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 6px;
  box-sizing: border-box;
}
.rule {
  border: none;
  border-top: 1px solid var(--line);
  margin: 22px 0 20px;
}
.chip {
  display: inline-block;
  margin-top: 22px;
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
ruby rt { font-size: .55em; color: var(--muted); font-weight: 500; }
"""

# Shows Kunyomi, then " ・ " only if both are present, then Onyomi.
_READING = ("{{#Kunyomi}}{{Kunyomi}}{{/Kunyomi}}"
            "{{#Onyomi}}{{#Kunyomi}}　・　{{/Kunyomi}}{{Onyomi}}{{/Onyomi}}")

RECOGNITION_FRONT = """
<div class="wrap"><div class="sheet">
  <div class="prompt">意味は？</div>
  <div class="jp">{{Kanji}}</div>
</div></div>
"""

RECOGNITION_BACK = f"""
<div class="wrap"><div class="sheet">
  <div class="jp">{{{{Kanji}}}}</div>
  <div class="reading">{_READING}</div>
  <hr class="rule">
  <div class="meaning">{{{{Meaning}}}}</div>
  <div class="mnemonic"><span class="primitives">{{{{Primitives}}}}</span>{{{{Mnemonic}}}}</div>
  {{{{#Compounds}}}}<div class="compounds">{{{{Compounds}}}}</div>{{{{/Compounds}}}}
</div></div>
"""

# Card 2 - "I mean this, can I WRITE the kanji?" Added 2026-08-22 when Fares'
# sensei told him to memorize the kanji, which means producing them by hand,
# not just recognising them. This is the card the earlier recognition-only
# decision deliberately left out; the goal changed, so it goes back in.
#
# The prompt carries BOTH readings alongside the meaning, and that is load-
# bearing rather than decoration. Meaning alone is ambiguous in this set -
# 本/書 both answer to "book" and 本/元 both to "origin" - so a bare keyword
# would have two defensible answers and no way to self-grade. Checked across
# all 121: (meaning + kun + on) is unique for every one of them.
PRODUCTION_FRONT = f"""
<div class="wrap"><div class="sheet">
  <div class="prompt">漢字を書いて</div>
  <div class="meaning">{{{{Meaning}}}}</div>
  <div class="reading">{_READING}</div>
</div></div>
"""

# The answer has to support self-grading, since Anki cannot check handwriting:
# the kanji to compare shape against, the stroke order to compare sequence
# against, and the mnemonic to repair the memory when it was wrong.
PRODUCTION_BACK = f"""
<div class="wrap"><div class="sheet">
  <div class="jp">{{{{Kanji}}}}</div>
  <div class="reading">{_READING}</div>
  {{{{#StrokeOrder}}}}<div class="strokes">
    <div class="strokes-label">筆順</div>{{{{StrokeOrder}}}}
  </div>{{{{/StrokeOrder}}}}
  <hr class="rule">
  <div class="mnemonic"><span class="primitives">{{{{Primitives}}}}</span>{{{{Mnemonic}}}}</div>
  {{{{#Compounds}}}}<div class="compounds">{{{{Compounds}}}}</div>{{{{/Compounds}}}}
</div></div>
"""

MODEL = genanki.Model(
    MODEL_ID,
    "JP Kanji",
    fields=[
        {"name": "Kanji"},
        {"name": "Kunyomi"},
        {"name": "Onyomi"},
        {"name": "Meaning"},
        {"name": "Primitives"},
        {"name": "Mnemonic"},
        {"name": "Compounds"},
        # Batch number the kanji arrived in (provenance only). Not shown on the
        # card - with a single deck a "Kanji 01" chip would point at a deck that
        # no longer exists. Kept as a field so it can be surfaced later without
        # a note-type schema migration (adding a field to an already-imported
        # note type is a manual step in Anki).
        {"name": "Batch"},
        # Inlined KanjiVG SVG. Appended last so existing field order is stable.
        {"name": "StrokeOrder"},
    ],
    templates=[
        {"name": "Recognition Kanji-EN", "qfmt": RECOGNITION_FRONT,
         "afmt": RECOGNITION_BACK},
        # Appended last so the recognition card keeps ordinal 0 and its
        # scheduling; the writing card arrives as a new ordinal-1 sibling.
        {"name": "Production EN-Kanji", "qfmt": PRODUCTION_FRONT,
         "afmt": PRODUCTION_BACK},
    ],
    css=CSS,
)


class GuidNote(genanki.Note):
    @property
    def guid(self):
        # Keyed on the KANJI ALONE (fields[0]), deliberately not on the batch.
        # The character is the note's real identity; a kanji that moves between
        # batches, or gets its batch renumbered as the list grows, must keep the
        # same GUID or Anki orphans the card and its review history. This is why
        # the vocab deck's (lesson, word) scheme is NOT copied here - that deck's
        # lessons are fixed by a textbook, this one's batches are not.
        return genanki.guid_for("jp-kanji", self.fields[0])


def stroke_order_svg(kanji):
    """Inlined, theme-aware KanjiVG diagram for one kanji, or "" if unavailable.

    Downloads once into cache/kanjivg/ and reads from there forever after, so a
    rebuild never touches the network. The upstream file is ~2.4 KB but is
    mostly a license comment and a DOCTYPE with an ATTLIST block - stripping
    those and the kvg:* bookkeeping attributes leaves roughly a third of that,
    which is what actually goes into the note.
    """
    KANJIVG_CACHE.mkdir(parents=True, exist_ok=True)
    path = KANJIVG_CACHE / ("%05x.svg" % ord(kanji))
    if not path.exists():
        try:
            path.write_bytes(urllib.request.urlopen(
                KANJIVG_URL % ord(kanji), timeout=30).read())
            time.sleep(0.12)          # be polite to raw.githubusercontent.com
        except Exception as exc:
            print(f"    ! no stroke order for {kanji}: {exc}")
            return ""

    raw = path.read_text(encoding="utf-8")
    start = raw.find("<svg")
    if start < 0:
        return ""
    svg = raw[start:]

    # kvg:* attributes are structural metadata (radical, element, stroke type)
    # that nothing on the card reads. Dropping them roughly halves the payload.
    svg = re.sub(r'\s+kvg:[\w-]+="[^"]*"', "", svg)
    svg = re.sub(r'\s+xmlns:kvg="[^"]*"', "", svg)
    svg = re.sub(r'\s+id="[^"]*"', "", svg)

    # Theme-awareness. The upstream inline styles hardcode black strokes and
    # grey numbers; inline styles beat any CSS rule we could write, so rewrite
    # them in place. currentColor follows the card's text colour, and
    # var(--accent) resolves against the .card variables since this is inlined
    # into the same DOM rather than loaded as a separate <img> document.
    svg = svg.replace("stroke:#000000", "stroke:currentColor")
    svg = svg.replace("fill:#808080", "fill:var(--accent)")

    # Let CSS size it instead of the hardcoded 109x109.
    svg = svg.replace('width="109" height="109"', 'class="kvg"', 1)

    svg = re.sub(r"\n\s*", "", svg)   # collapse whitespace, it is markup not prose
    return f"<!-- stroke order: KanjiVG, CC BY-SA 3.0 -->{svg}"


def compounds_html(items):
    if not items:
        return ""
    cells = "".join(
        f'<div class="cw"><ruby>{html.escape(w)}<rt>{html.escape(r)}</rt></ruby></div>'
        f'<div class="cm">{html.escape(m)}</div>'
        for w, r, m in items
    )
    return f'<div class="compounds-grid">{cells}</div>'


def build():
    """Build the whole 漢字 deck into one package.

    Every kanji in LESSONS lands in the single `漢字` deck. The batch number is
    kept only as a tag (`漢字-01`), so the browser can still filter "the newest
    five" without the deck list sprouting 25 entries.
    """
    deck = genanki.Deck(DECK_ID, DECK_NAME)

    total = 0
    for batch_num, entries in LESSONS:
        batch_tag = f"漢字-{batch_num:02d}"
        for kanji, kun, on, meaning, prim, mnem, comp in entries:
            deck.add_note(GuidNote(
                model=MODEL,
                fields=[
                    kanji,
                    kun,
                    on,
                    html.escape(meaning),
                    html.escape(prim),
                    html.escape(mnem),
                    compounds_html(comp),
                    f"{batch_num:02d}",
                    stroke_order_svg(kanji),
                ],
                tags=["日本語", "kanji", batch_tag],
            ))
            total += 1

    package = genanki.Package(deck)
    APKG_OUT.mkdir(parents=True, exist_ok=True)
    out_path = APKG_OUT / "漢字.apkg"
    package.write_to_file(str(out_path))
    cards = total * len(MODEL.templates)
    print(f"{DECK_NAME}: {total} kanji -> {total} notes / {cards} cards "
          f"({len(MODEL.templates)} templates) -> {out_path}")
    return out_path


def write_review():
    """Static HTML page rendering every card's front+back so the content and
    layout can be eyeballed before importing, matching build_anki.py's
    review-page habit."""
    blocks = []
    for batch_num, entries in LESSONS:
        for kanji, kun, on, meaning, prim, mnem, comp in entries:
            reading = kun + ("　・　" + on if kun and on else on)
            comp_html = compounds_html(comp)
            strokes = stroke_order_svg(kanji)
            stroke_block = (f'<div class="strokes"><div class="strokes-label">筆順</div>'
                            f'{strokes}</div>') if strokes else ''
            blocks.append(f"""
<div class="kanji-block">
  <h2>{kanji} — {html.escape(meaning)} <span class="lbl">漢字-{batch_num:02d}</span></h2>
  <div class="layout">
    <div class="frame"><div class="card"><div class="wrap"><div class="sheet">
      <div class="prompt">意味は？</div><div class="jp">{kanji}</div>
    </div></div></div></div>
    <div class="frame"><div class="card"><div class="wrap"><div class="sheet">
      <div class="jp">{kanji}</div>
      <div class="reading">{reading}</div>
      <hr class="rule">
      <div class="meaning">{html.escape(meaning)}</div>
      <div class="mnemonic"><span class="primitives">{html.escape(prim)}</span>{html.escape(mnem)}</div>
      {'<div class="compounds">' + comp_html + '</div>' if comp_html else ''}
    </div></div></div></div>
    <div class="frame"><div class="card"><div class="wrap"><div class="sheet">
      <div class="prompt">漢字を書いて</div>
      <div class="meaning">{html.escape(meaning)}</div>
      <div class="reading">{reading}</div>
    </div></div></div></div>
    <div class="frame"><div class="card"><div class="wrap"><div class="sheet">
      <div class="jp">{kanji}</div>
      <div class="reading">{reading}</div>
      {stroke_block}
      <hr class="rule">
      <div class="mnemonic"><span class="primitives">{html.escape(prim)}</span>{html.escape(mnem)}</div>
      {'<div class="compounds">' + comp_html + '</div>' if comp_html else ''}
    </div></div></div></div>
  </div>
</div>""")

    doc = f"""<!doctype html><meta charset="utf-8"><title>kanji deck review</title>
<style>
 body{{margin:0;padding:24px;background:#8b8f9c;font-family:system-ui,sans-serif}}
 h1{{color:#fff;font-size:18px;margin:0 0 20px}}
 h2{{color:#fff;font-size:14px;font-weight:600;margin:0 0 8px;display:flex;
     justify-content:space-between;align-items:baseline}}
 h2 .lbl{{font-size:11px;opacity:.65;letter-spacing:.08em;text-transform:uppercase}}
 .kanji-block{{margin-bottom:30px}}
 .layout{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;max-width:1600px}}
 @media (max-width:1300px){{.layout{{grid-template-columns:1fr 1fr}}}}
 .frame{{border-radius:12px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,.28)}}
 .frame .card{{min-height:380px;display:block}}
 .card .wrap{{min-height:380px}}
{CSS}
</style>
<h1>漢字 deck — {sum(len(k) for _, k in LESSONS)} kanji, one deck.
Each row: recognition front/back, then writing front/back.</h1>
{''.join(blocks)}"""

    REVIEW_OUT.mkdir(parents=True, exist_ok=True)
    path = REVIEW_OUT / "review_kanji.html"
    path.write_text(doc, encoding="utf-8")
    print(f"review -> {path}")
    return path


if __name__ == "__main__":
    # No per-batch argument: this is one deck, always built whole. Adding kanji
    # means editing LESSONS and rerunning this with no arguments.
    build()
    write_review()
