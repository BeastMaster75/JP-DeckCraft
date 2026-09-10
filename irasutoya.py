"""
Find an いらすとや illustration matching a Japanese word.

Blogger's search ranks by RECENCY, not relevance, so the first hit for 海 is
whatever sea-adjacent picture was posted most recently. This module pages
through the whole result set and re-ranks it locally.

Licensing note: irasutoya images are free for personal use, but the site
prohibits redistributing the images themselves as the main content of a
package. Decks built with this are for personal study only - do not upload
them to AnkiWeb's shared decks or otherwise publish them.
"""

import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (personal Anki deck builder; low volume)"}
FEED = "https://www.irasutoya.com/feeds/posts/default"

# Words whose literal form searches badly. Two kinds live here.
#
# 1. The kanji leads a common compound with an unrelated meaning
#    (春 -> 春巻き "spring roll", 甘い -> 甘食 a sweet bread), or the site
#    files the concept under a different word (季節 -> 春夏秋冬).
#
# 2. Adjectives and adverbs that cannot be drawn directly, so they get a
#    depictable stand-in instead: fast -> a bullet train, slow -> a snail,
#    "the most" -> a winner's podium. These are approximations by design -
#    a picture that is roughly right beats a blank card.
#
# Each entry is a list of queries tried in order; the first to produce a
# confident match wins, otherwise the strongest of them is used. Every query
# below was checked against the live site rather than guessed.
QUERY_OVERRIDE = {
    # -- searches badly in its literal form ---------------------------------
    "春": ["桜"],
    "夏": ["海水浴"],
    "秋": ["落ち葉"],
    "冬": ["冬"],
    "季節": ["春夏秋冬", "四季"],
    "天気": ["天気予報", "お天気"],   # bare 天気 lands on 天気痛, "weather pain"
    "曇り": ["雲", "曇り空"],
    "雪": ["雪だるま"],
    "世界": ["地球"],
    "とり肉": ["鶏肉"],
    "［お］祭り": ["お祭り"],
    "お祭り": ["お祭り"],
    "辛い": ["唐辛子"],
    "甘い": ["砂糖"],
    "重い": ["重い荷物"],
    "疲れました": ["疲れた"],
    "お帰りなさい": ["帰宅"],
    "ただいま": ["帰宅"],

    # -- abstract, illustrated by a stand-in --------------------------------
    "簡単": ["低いハードル", "余裕"],       # a low hurdle = easy
    "近い": ["近く", "徒歩"],
    "遠い": ["遠く"],                      # 遠くのスーパーマーケット
    "速い": ["新幹線"],                    # bullet train = fast
    "遅い": ["カタツムリ", "亀"],           # snail = slow
    "多い": ["満員電車", "人混み"],         # packed train = many
    "少ない": ["過疎", "田舎の村"],
    "暖かい": ["暖房", "ストーブ"],
    "涼しい": ["扇風機", "風鈴"],
    "軽い": ["風船"],                      # balloon = light
    "いい": ["OKサイン"],
    "どちら": ["分かれ道", "迷う人"],       # choosing at a fork
    "どちらも": ["仲良し"],                 # two together = both
    "いちばん": ["表彰台", "金メダル"],      # podium = the most
    "ずっと": ["比較"],                     # comparison, as the grammar uses it
    "初めて": ["入学式", "新入社員"],        # first day

    # ----------------------------------------------------------------------
    # Lessons 07-15. These lessons are dense with verbs, and いらすとや files
    # nothing under a polite ～ます form: 売ります returns zero results. The
    # plain dictionary form is no better - 売る, 知る and 住む were all checked
    # against the live site and return only incidental matches. So every verb
    # below is represented by the noun for the scene it describes.
    # ----------------------------------------------------------------------

    # -- L07 verbs and objects
    "送ります": ["宅配便"],
    "あげます": ["贈り物"],
    "もらいます": ["受け取り"],
    "貸します": ["レンタル"],
    "借ります": ["レンタル"],
    "教えます": ["先生"],
    "習います": ["授業"],
    "切ります": ["包丁"],
    "かけます": ["電話"],                   # かけます is "make a phone call"
    # The site's own spelling differs from the textbook's, so the correct
    # illustration was being found and then scored down as a near-miss.
    "ホッチキス": ["ホチキス"],
    "セロテープ": ["セロハンテープ"],
    "紙": ["コピー用紙"],                    # bare 紙 lands on 紙皿, a paper plate
    "ケータイ": ["携帯電話"],
    "まだ": ["砂時計"],                      # still running = not yet
    "これから": ["スタート"],

    # -- L08 adjectives
    "にぎやか": ["商店街"],
    "易しい": ["低いハードル"],
    "いい (よい)": ["OKサイン"],             # the note writes the word this way
    "親切": ["席を譲る"],                    # giving up a seat = kind
    "おもしろい": ["大笑い"],
    "きれい": ["掃除"],
    "有名": ["サイン会"],
    "おいしい": ["グルメ"],
    "暑い、熱い": ["暑い日"],                # the note gives both kanji in one cell
    "生活": ["家族"],                        # bare 生活 lands on 生活保護, welfare
    # Connectives and degree adverbs. None of these can be drawn; the pictures
    # are mnemonic props, not definitions. Without them the matches were pure
    # noise - そして got a graduation certificate, あまり got a radio.
    "そして": ["矢印"],
    "あまり": ["バツ"],
    "どんな～": ["疑問"],
    "～が、～": ["分かれ道"],                # the fork that also stands in for どちら
    "すてき": ["ハート"],

    # -- L09
    "わかります": ["ひらめき"],
    "どうして": ["疑問"],
    "上手〔な〕": ["名人"],
    "好き〔な〕": ["ハート"],                # bare 好き lands on 腐女子
    "全然": ["バツ"],                        # the mirror of OKサイン for いい
    "だいたい": ["電卓"],
    "～から": ["矢印"],                      # cause pointing to effect
    "用事": ["カレンダー"],
    "かたかな": ["カタカナ"],
    # あります/います scored above the bar on nonsense - 骨盤 (a pelvis) and
    # 熊胆 (bear gallbladder), both of which merely contain the kana.
    "あります": ["机の上"],
    "います": ["家族"],
    "ローマ字": ["アルファベット"],
    "字": ["書道"],
    "細かいお金": ["小銭"],
    "夫": ["夫婦"],
    "妻": ["夫婦"],
    "ご主人": ["夫婦"],

    # -- L10. The position words were the worst offenders in the whole set:
    # 上 matched 上新粉 (rice flour), 右 matched 石川五右衛門 (a folk outlaw),
    # 間 matched 歯間ブラシ (an interdental brush). Arrows and the 上下左右
    # pointing illustration are the only things that actually depict relative
    # position, so the group shares them and lets deduplication spread them out.
    "男の人": ["男性"],
    "女の人": ["女性"],
    # Only two illustrations on the site actually depict left versus right -
    # the 上下左右 pair - so those go to 右/左, which have no other option, and
    # the vertical words take arrows. 右手/左手 were tried and rejected: they
    # return Fleming's-rule hands, and the 右 one points left.
    "上": ["上下左右"],
    "下": ["上下左右"],
    "前": ["行列"],                          # the head of a queue = the front
    "右": ["上下左右"],
    "左": ["上下左右"],
    "間": ["隙間"],
    "物": ["荷物"],                          # bare 物 lands on 戦隊もののキャラクター
    "～屋": ["商店街"],
    "～や～など": ["一覧"],
    "乗り場": ["バス停"],
    "どうもすみません。": ["お辞儀"],
    "一番下": ["棚"],

    # -- L11 counters. Nothing depicts "-台" or "四つ" directly, so the whole
    # group leans on counting imagery and lets pick()'s URL deduplication hand
    # each number a different one. 数字 has 36 candidates, which is enough to
    # go round. Without this 六つ matched 6つに割れた腹筋 (a six-pack stomach)
    # and 八つ matched 八岐の大蛇, the eight-headed serpent.
    "１つ": ["数字", "そろばん"],
    "２つ": ["数字", "そろばん"],
    "３つ": ["数字", "そろばん"],
    "４つ": ["数字", "そろばん"],
    "５つ": ["数字", "そろばん"],
    "６つ": ["数字", "そろばん"],
    "７つ": ["数字", "そろばん"],
    "８つ": ["数字", "そろばん"],
    "９つ": ["数字", "そろばん"],
    "１０": ["数字", "そろばん"],
    "いくつ": ["数える"],
    "１人": ["一人暮らし"],
    "２人": ["夫婦"],
    "－人": ["行列"],
    "－台": ["駐車場"],
    "－枚": ["枚数"],
    "－回": ["回数券"],
    "－時間": ["時計"],
    "－週間": ["カレンダー"],
    "－か月": ["カレンダー"],
    "－年": ["カレンダー"],
    "全部で": ["電卓"],
    "みんな": ["家族"],
    "どのくらい": ["時計"],
    "～ぐらい": ["電卓"],
    "～だけ": ["一人暮らし"],                # alone = only

    "かかります": ["砂時計"],                # time passing
    "休みます": ["有給休暇"],
    "葉書": ["はがき"],
    "弟さん": ["兄弟"],
    "妹さん": ["姉と妹"],
    "弟": ["兄弟"],                          # bare 弟 lands on ライト兄弟, the Wright brothers

    # -- L12 mined words
    "咲きます": ["開花"],
    "入れます": ["注ぐ"],
    "泊まります": ["旅館"],

    # -- L13
    "遊びます": ["遊具"],
    "泳ぎます": ["水泳"],
    "のどがかわきます": ["水を飲む"],
    "そうしましょう": ["握手"],
    "ご注文は？": ["ウェイター"],
    "どこか": ["地図"],
    "～ごろ": ["時計"],
    "迎えます": ["お迎え"],
    "疲れます": ["疲れた"],
    "週末": ["休日"],
    "おなかがすきます": ["空腹"],
    "牛どん": ["牛丼"],
    "広い": ["草原"],
    "別々に": ["割り勘"],

    # -- L14
    "急ぎます": ["遅刻"],                    # rushing because you are late
    "待ちます": ["待合室"],
    "持ちます": ["荷物を持つ"],
    "手伝います": ["お手伝い"],
    "呼びます": ["手招き"],
    "話します": ["会話"],
    "止めます": ["駐車場"],
    "座ります": ["正座"],
    "立ちます": ["起立"],
    "降ります": ["雨"],
    "住所": ["名刺"],
    "これで おねがいします": ["レジ"],
    "ゆっくり": ["カタツムリ"],              # same snail that stands in for 遅い
    "開けます": ["窓を開ける"],
    "閉めます": ["ドアを閉める"],
    "入ります": ["玄関"],
    "出ます": ["改札"],
    "つけます": ["電球"],
    "けします": ["消灯", "電気をつける"],
    "使います": ["道具"],
    "見せます": ["提示"],
    "取ります": ["受け取り"],
    "まっすぐ": ["道案内"],
    "すぐ": ["ストップウォッチ"],
    "あとで": ["時計"],
    "もう少し": ["おかわり"],
    "さあ": ["応援"],                        # cheering = the "come on!" sense
    # ～方 is "the way of doing"; 読み方 sits in the same lesson, so dedup hands
    # one the manual itself and the other the person reading it.
    "～方": ["説明書"],
    "読み方": ["説明書"],

    # -- L15
    "売ります": ["販売"],
    "知ります": ["自己紹介"],
    "置きます": ["棚"],
    "時刻表": ["時計"],                      # bare 時刻表 lands on 時差, "time difference"
    "住みます": ["住宅"],
    "独身": ["一人暮らし"],
    "すみません": ["お辞儀"],
    "思い出します": ["思い出"],
    "いらっしゃいます": ["接客"],
    "作ります": ["手作り"],
    "製品": ["工場"],
    "皆さん": ["集合写真"],

    # -- Lessons 16-20 -------------------------------------------------------
    # Same pattern as everything above: the polite verb form returns nothing,
    # so each verb points at the noun for the scene it describes. Every query
    # below was checked against the live site (_queries7/8.txt) before landing.
    "浴びます": ["シャワーを浴びる"],
    "下ろします": ["ATM"],
    "始めます": ["スタート"],
    "すごいですね。": ["拍手"],
    "いいえ、まだまだです。": ["お辞儀"],
    "お引き出しですか": ["ATM"],

    "覚えます": ["暗記"],                    # 単語カード, memorisation flashcards
    "忘れます": ["忘れ物"],
    "払います": ["レジ"],
    "返します": ["返却"],
    "出かけます": ["お出かけ"],
    "持って行きます": ["荷物"],
    "おふろ": ["お風呂"],
    "ですから": ["矢印"],
    "どうしましたか。": ["問診"],
    "かぜ": ["風邪"],
    "それから": ["矢印"],                    # dedup hands it a different arrow
    "お大事に": ["お見舞い"],

    "洗います": ["手洗い"],
    "弾きます": ["ピアノを弾く"],
    "歌います": ["歌う", "カラオケ"],
    "集めます": ["コレクション"],
    "捨てます": ["ゴミ箱"],
    "換えます": ["両替"],
    "へえ": ["驚く"],
    "それはおもしろいですね。": ["談笑"],
    "ほんとうですか。": ["驚く"],            # dedup gives a different surprise

    "登ります、上ります": ["登山"],
    "もうすぐ": ["砂時計"],
    "おかげさまで": ["お辞儀"],
    "体にいい": ["野菜"],                    # matches the example sentence

    "要ります": ["パスポート"],
    "調べます": ["虫眼鏡"],
    "君": ["少年"],
    "～君": ["少年"],                        # dedup gives a different boy
    "ううん": ["バツ"],
    "ことば": ["会話"],
    "そっち": ["案内"],
    "あっち": ["指差し"],
    "どっち": ["分かれ道"],                  # the established "which" idiom
    "おなかがいっぱいです": ["満腹"],
    "よかったら": ["どうぞ"],

    # -- Lessons 21-25 -------------------------------------------------------
    "勝ちます": ["ガッツポーズ"],
    "負けます": ["落ち込む"],
    "役に立ちます": ["便利"],                # 便利屋, the handyman
    "動きます": ["歯車"],
    "やめます": ["退職"],
    "気をつけます": ["注意"],
    "むだ": ["無駄遣い"],                    # money thrown down a drain
    "不便": ["困る"],
    "ほんとう": ["マル"],
    "うそ": ["ピノキオ"],
    "たぶん": ["悩む"],
    "ほんとうに": ["驚く"],
    "そんなに": ["バツ"],
    "久しぶりですね": ["挨拶"],
    "～でも飲みませんか": ["居酒屋"],
    "もう帰らないと": ["帰宅"],

    "はきます": ["靴"],
    "かぶります": ["帽子"],                  # dedup keeps it clear of ぼうし
    "わたしたち": ["グループ"],
    "えーと": ["考える人"],
    "お探しですか": ["接客"],
    "押し入れ": ["押入れ"],                  # the site spells it without the っ

    "回します": ["ハンドル"],
    "引きます": ["綱引き"],                  # tug of war
    "変えます": ["着替え"],
    "触ります": ["タッチパネル"],
    "歩きます": ["ウォーキング"],
    "渡ります": ["横断歩道"],
    "何回も": ["回数券"],                    # a book of many tickets

    "直します": ["修理"],
    "連れて行きます": ["手をつなぐ"],
    "連れて来ます": ["手をつなぐ"],
    "ほかに": ["一覧"],

    "考えます": ["考える人"],
    "着きます": ["空港"],
    "足ります": ["OKサイン"],
    "もしもし": ["電話"],
    "いろいろお世話になりました": ["お辞儀"],
    "頑張ります": ["ガッツポーズ"],
    "どうぞお元気で": ["手を振る"],

    # -- Lessons 01-06 -------------------------------------------------------
    # These lessons are mostly greetings, time words and the calendar, none of
    # which are drawable. Several words share a query on purpose and let
    # pick()'s URL deduplication hand each one a different picture - that is
    # the same trick the Lesson 11 counters use.
    "わたし": ["自己紹介"],
    "あなた": ["指差し"],
    "あの人": ["男性"],
    "何歳": ["年齢"],
    "初めまして": ["挨拶"],
    "～から来ました": ["世界地図"],
    "どうぞよろしくお願いします": ["お辞儀"],
    "失礼ですが": ["お辞儀"],
    "お名前は": ["名札"],
    "こちらは～さんです": ["紹介"],

    "あのう": ["悩む"],
    "えっ": ["驚く"],
    "どうもありがとうございます。": ["お辞儀"],
    "これからお世話になります": ["挨拶"],
    "こちらこそどうぞよろしくおねがいします。": ["お辞儀"],

    "そちら": ["案内"],
    "（お手洗い）": ["トイレ"],              # the parens survive search_term
    "お国": ["世界地図"],
    "何階": ["ビル"],
    "すみません。": ["お辞儀"],              # note the 。 - it is part of the term
    "どうも。": ["お辞儀"],
    "いらっしゃいませ。": ["接客"],
    "見せてください": ["商品"],

    "起きます": ["目覚まし時計"],
    "働きます": ["オフィス"],
    "終わります": ["ゴールテープ"],
    "何時": ["時計"],
    "何分": ["時計"],
    "午前": ["朝"],
    "午後": ["夕方"],
    "晩（夜）": ["夜"],
    "おととい": ["カレンダー"],
    "きのう": ["カレンダー"],
    "あさって": ["カレンダー"],
    "けさ": ["朝"],
    "今晩": ["夜"],
    "毎朝": ["朝食"],
    "毎晩": ["夜"],
    "何曜日": ["カレンダー"],
    "大変ですね": ["困る"],
    "何番": ["数字"],

    "行きます": ["出発"],
    "帰ります": ["帰宅"],
    "彼": ["男性"],
    "先週": ["カレンダー"],
    "今週": ["カレンダー"],
    "来週": ["カレンダー"],
    "先月": ["日めくりカレンダー"],
    "来月": ["日めくりカレンダー"],
    "去年": ["カレンダー"],
    "来年": ["カレンダー"],
    "何月": ["カレンダー"],
    "14日": ["スケジュール"],
    "何日": ["カレンダー"],
    "どうもありがとうございました。": ["お辞儀"],
    "どういたしまして。": ["お辞儀"],
    "急行": ["特急"],

    "吸います": ["喫煙"],
    "聞きます": ["ヘッドホン"],              # L23's ask-the-teacher is pinned
    "読みます": ["読書"],
    "書きます": ["書く"],
    "買います": ["買い物"],
    "撮ります": ["写真を撮る"],
    "昼ごはん": ["定食"],
    "時々": ["砂時計"],
    "ええ": ["マル"],
    "わかりました。": ["ひらめき"],
    "じゃ、またあした。": ["手を振る"],
}

# Escape hatch: words to leave deliberately imageless. Empty by design - the
# current policy is that an approximate illustration always beats none. Add a
# word here only if its stand-in turns out to actively mislead.
NO_IMAGE = frozenset()

# Lettering sets and icon sheets are not illustrations of the concept.
JUNK = ("文字", "タイトル", "アイコン", "マーク", "フレーム", "背景素材",
        "ライン", "囲み枠")

# いらすとや publishes long themed series - 紅葉のイラスト「象」,「猫」,「犬」,
# 「赤いもみじ」... The length penalty alone picks the shortest bracket, which
# is usually an animal rather than the thing being taught. These are picks
# made by eye after looking at the actual images.
TITLE_PREFERENCE = {
    "紅葉": "赤いもみじ",
    "海": "ヤシの木とビーチ",

    # Lessons 16-20: the query is right but the best-scoring title is not.
    "下ろします": "ATMを使う人",             # else the bare cash dispenser
    "返します": "テストを返す先生",           # else 返却口, a return slot
    "歌います": "カラオケを歌う女性",         # else a pair of singing birds
    "君": "少年の後ろ姿",
    "そっち": "道案内をしている警察官",
    "そちら": "道案内",
    "歩きます": "ウォーキングをする男性",     # else 水中ウォーキング, underwater

    # Lesson 26. Both were picked by eye off the review sheet: the 母艦 variant
    # of 宇宙船 reads as a grey naval battleship, and 交換's best-scoring hit is
    # 情報交換 - two people holding "i" icons, which says nothing about
    # "another". Changing a light bulb does.
    "宇宙船": "旅客機",
    "交換": "電球の交換",
}

# Within a series post every variant shares one title, so only the filename
# distinguishes them. いらすとや names them in romaji: position_boy1_ue.png,
# ..._shita, ..._migi, ..._hidari, ..._naka. That is the sole way to tell the
# 上 picture from the 下 one.
URL_PREFERENCE = {
    "上": "_ue",
    "下": "_shita",
    "右": "_migi",
    "左": "_hidari",
    "中": "_naka",
    "前": "_mae",
    # The 数字 hit is a set of numbered birthday candles, candle_number0..9,
    # all under one title. Left to deduplication alone, ひとつ drew the "9"
    # candle. The trailing dot keeps candle_number1 from matching ...10.
    "１つ": "candle_number1.",
    "２つ": "candle_number2.",
    "３つ": "candle_number3.",
    "４つ": "candle_number4.",
    "５つ": "candle_number5.",
    "６つ": "candle_number6.",
    "７つ": "candle_number7.",
    "８つ": "candle_number8.",
    "９つ": "candle_number9.",
    "１０": "card_heart_10",      # no candle for ten; a playing card instead
}

# 75 admits descriptive matches like お天気お姉さん for 天気 while still
# rejecting incidental mentions. The review page is the backstop.
MIN_SCORE = 75


def _get(url, timeout, tries=4):
    """Fetch a URL, retrying on the transient 5xx / reset failures.

    Paging the whole feed for several hundred terms is enough traffic that
    Blogger intermittently answers 500. That is not a permanent failure and
    must not abort a nine-lesson run, so back off and try again.
    """
    delay = 2.0
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as exc:
            code = getattr(exc, "code", None)
            permanent = code is not None and 400 <= code < 500 and code != 429
            if permanent or attempt == tries - 1:
                raise
            time.sleep(delay)
            delay *= 2
    raise AssertionError("unreachable")


def _page(query, start, n=50):
    url = (f"{FEED}?q={urllib.parse.quote(query)}&alt=json"
           f"&max-results={n}&start-index={start}")
    return json.loads(_get(url, timeout=30).decode("utf-8"))


def _harvest(query, cap=300):
    out, start = [], 1
    while start <= cap:
        got = _page(query, start).get("feed", {}).get("entry", [])
        if not got:
            break
        for e in got:
            content = e.get("content", {}).get("$t", "")
            urls = re.findall(r'src="(https://[^"]+?\.(?:png|jpe?g))"',
                              content, re.I)
            urls = [u for u in urls if "/s72-c/" not in u]
            # Series posts carry one image per variant under a single title -
            # 「上下左右中」 is five files, position_boy5_naka.png last. Taking
            # only the last handed 左 the centre picture. Emit every image as
            # its own candidate so deduplication and URL_PREFERENCE can choose.
            seen = set()
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    out.append((e["title"]["$t"], u))
        if len(got) < 50:
            break
        start += 50
        time.sleep(0.4)  # be gentle with someone else's server
    return out


def _score(title, term, alias=None):
    """Rank titles by how squarely they name the concept.

    A bare prefix match is NOT rewarded, so 春 cannot match 春巻き; only a
    prefix followed by a particle or separator counts. A loose containment
    match is scaled by term length, because a 3-character term appearing
    anywhere in a title is far stronger evidence than a single kanji.

    `alias` is the kana reading. Within a themed series the variant naming the
    reading (紅葉のイラスト「赤いもみじ」) is the one that actually teaches the
    word, so it beats the shorter but unrelated 「象」.
    """
    # Lettering sets and icon sheets are disqualified outright, not merely
    # penalised: "四季のイラスト文字" matches the ideal prefix and would
    # otherwise outscore every real illustration of the concept.
    if any(j in title for j in JUNK):
        return -9999

    s = -2 * len(title)
    ideal = f"{term}のイラスト"
    if title == ideal:
        s += 1000
    elif title.startswith(ideal):
        s += 600                         # 海のイラスト「うきわ」
    elif title.startswith(f"{term}の") or title.startswith(f"{term}・"):
        s += 300                         # 空港・飛行場のイラスト
    elif term in title:
        s += 60 * min(len(term), 4)      # 生け花をする女性のイラスト

    if alias and alias != term and alias in title:
        s += 80
    pref = TITLE_PREFERENCE.get(term)
    if pref and pref in title:
        s += 500
    return s


def queries_for(term):
    """The list of queries to try for a term, in order.

    Beyond the hand-written overrides there is one rule general enough to
    automate: a する-compound is filed under its noun half. 研究します returns
    nothing, 研究 returns 86 illustrations. The polite form never appears in a
    title, so it is only kept as a last resort.

    The two-character floor is what separates a real する-compound from a godan
    す verb that merely ends the same way: 研究/買い物/食事/散歩 keep a noun when
    します is removed, while 話します, 消します and 貸します would be cut down to a
    lone 話, 消, 貸 - those are handled by QUERY_OVERRIDE instead.
    """
    if term in QUERY_OVERRIDE:
        return QUERY_OVERRIDE[term]
    if term.endswith("します") and len(term) - 3 >= 2:
        return [term[:-3], term]
    return [term]


def candidates(term, cache_dir, alias=None):
    """Ranked [(score, title, url)] for a term, cached on disk.

    Each query is scored against both itself and the original word, since an
    override narrows the search but the original term is often what actually
    appears in the title (query 天気予報 still wants to match お天気お姉さん).
    Queries are tried in order and the first one that produces a usable match
    wins.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)
    slug = re.sub(r"\W+", "_", term)
    meta = cache_dir / f"{slug}.cands.json"

    if meta.exists():
        return json.loads(meta.read_text(encoding="utf-8"))

    best = []
    for query in queries_for(term):
        try:
            raw = _harvest(query)
        except Exception as exc:
            print(f"    ! search failed for {term} ({query}): {exc}")
            continue
        hint = URL_PREFERENCE.get(term)
        ranked = sorted(
            ((max(_score(t, query, alias), _score(t, term, alias))
              + (400 if hint and hint in u.rsplit("/", 1)[-1] else 0), t, u)
             for t, u in raw),
            reverse=True)
        if not ranked:
            continue
        if ranked[0][0] >= MIN_SCORE:
            best = ranked
            break
        # Keep whichever query produced the strongest candidate so far, rather
        # than whichever one happened to run first.
        if not best or ranked[0][0] > best[0][0]:
            best = ranked

    meta.write_text(json.dumps(best, ensure_ascii=False), encoding="utf-8")
    return best


def fetch(term, url, cache_dir, max_px=360):
    """Download, downscale and flatten one illustration. Returns (name, path)."""
    cache_dir = Path(cache_dir)
    slug = re.sub(r"\W+", "_", term)
    # The URL digest is part of the name because a term is not unique per note:
    # Lesson 11 has two います rows (have a child / stay in Japan). pick() hands
    # them different URLs, but a term-only filename made the second reuse the
    # first one's file and the two cards came out visually identical.
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    filename = f"irasutoya_{slug}_{digest}.png"
    path = cache_dir / filename
    if path.exists():
        return filename, path

    raw = _get(url, timeout=45)

    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    img.thumbnail((max_px, max_px), Image.LANCZOS)
    # Flatten onto white: Anki renders cards on light or dark backgrounds and a
    # stray alpha channel looks wrong on one of them.
    flat = Image.new("RGB", img.size, (255, 255, 255))
    flat.paste(img, mask=img.split()[3])
    flat.save(path, "PNG", optimize=True)
    return filename, path


def pick(term, cache_dir, used_urls, alias=None):
    """Best candidate not already claimed by another word.

    Deduplication matters: without it 冬 and 雪 both land on the same snowman
    and the two cards become visually identical.

    Two passes. The first demands a confident match. If nothing qualifies, the
    second accepts the strongest remaining candidate whatever it scores, so a
    word ends up with a roughly-related picture instead of a blank. Only
    disqualified entries (lettering sets, icon sheets) are never used.
    """
    ranked = candidates(term, cache_dir, alias)

    for score, title, url in ranked:
        if score < MIN_SCORE:
            break
        if url not in used_urls:
            return score, title, url

    for score, title, url in ranked:
        if score <= -9000:          # lettering/icon sheet, never usable
            continue
        if url not in used_urls:
            return score, title, url
    return None
