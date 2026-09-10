"""
Minna no Nihongo (みんなの日本語) curriculum data.

Everything in this module is specific to this one textbook and this project
owner's exact lesson numbering: which words to skip, which いらすとや search
term to use when the literal word searches badly, extra vocabulary mined from
example sentences, and English translations for lessons sourced from a
read-only vault. Ships as a real, working example - point config.py's
CURRICULUM_MODULE elsewhere (see curriculum/blank.py) if you are building
decks from different material.
"""

# Words whose image search must be resolved per lesson, not per term.
#
# `search_term` strips the bracketed context gloss, so 入ります［大学に～］ and
# 入ります［おふろに～］ collapse to the same term and QUERY_OVERRIDE - keyed by
# term - cannot tell them apart. Entering a university and getting into a bath
# want completely different pictures, so the lesson has to be part of the key.
# This only affects the image search; the card still shows the textbook kanji.
TERM_OVERRIDE = {
    # Checked by eye, not by title. 乗り越し showed a man
    # panicking at having missed his stop, 駅のホーム was a bare platform
    # screen door, 順番 was two hands and no sequence, and 漫符 handed 特に a
    # pair of pink hearts.
    (16, "のります［でんしゃに～］"): "駆け込み乗車",
    (16, "おります［でんしゃを～］"): "電車の乗り降り",
    (16, "のりかえます"): "分かれ道",              # switching to another line
    (16, "まず"): "スタートライン",
    (16, "はいります［だいがくに～］"): "大学",     # 入学式 gave a cartoon bear
    (18, "とくに"): "スポットライト",
    (16, "でます［だいがくを～］"): "卒業式",       # else 改札鋏, a ticket punch
    (17, "ぬぎます"): "スリッパ",                  # slippers on = shoes off
    (17, "はいります［おふろに～］"): "お風呂",     # dedup keeps it clear of ［お］ふろ
    (20, "～くん"): "ランドセル",                  # else 少年院, a detention centre
    # 聞きます is also Lesson 6 vocabulary, where it means "listen" - keep the
    # classroom picture pinned to Lesson 23 so building 06 later doesn't
    # inherit it.
    (23, "ききます［せんせいに～］"): "手を挙げる",
    # Inherited Lesson 7's 送ります → 宅配便 and got a parcel delivery van for
    # "escort a person". Not a miss, so the coverage count never flagged it.
    (24, "おくります［ひとを～］"): "手を振る",
    # More of the same: the bracketed context is stripped, so these inherited an
    # earlier lesson's override and came out silently wrong. Every one of them
    # HAD an image, so the coverage count never flagged it - only reading the
    # titles did.
    (21, "あります［おまつりが～］"): "お祭り",     # else 机の上, books on a desk
    (22, "かけます［めがねを～］"): "眼鏡",         # else 電話, from L07 かけます
    (23, "でます［おつりが～］"): "お釣り",         # else 改札鋏, a ticket punch
    (25, "とります［としを～］"): "おじいさん",     # else コンビニ受け取り

    # ---- Lesson 26, the first Book II lesson ----
    # Three new failure modes show up here, all of them silent:
    #  * Book II writes alternative kanji with a 、 (見ます、診ます) where Book I
    #    used ／, and search_term only splits on ／ - so the raw term is a query
    #    that cannot match anything. Fixing search_term globally would move the
    #    images of L08 あつい, L17 2、3にち and L19 のぼります, so it is left
    #    alone and the terms are overridden here instead.
    #  * つごうが いい / きぶんが いい contain a space, same problem.
    #  * だします［ごみを～］ collapses to 出します and would inherit Lesson 16's
    #    picture; みます would inherit Lesson 06's 見ます = "watch".
    # Every query below was checked against the live site first (_queries11-13),
    # which is how 探し物, 方言, 今度, 手渡し, ゴミ置き場, こそあど, 何でも屋,
    # 別々, 新聞社, 間に合う and 滑り込み were all rejected - they return nothing.
    (26, "みます"): "添削",                        # a teacher checking a composition
    (26, "さがします"): "虫眼鏡",
    (26, "おくれます［じかんに～］"): "遅刻",
    (26, "まにあいます［じかんに～］"): "セーフ",    # the baseball umpire's "safe!"
    (26, "やります"): "腕まくり",
    (26, "さんかします［パーティーに～］"): "パーティー",
    (26, "もうしこみます"): "申請",
    (26, "つごうが いい"): "スケジュール",
    (26, "つごうが わるい"): "忙しい",
    (26, "きぶんが いい"): "温泉",                 # 元気/健康/笑顔 all came back junk
    (26, "きぶんが わるい"): "風邪",
    (26, "しんぶんしゃ"): "新聞記者",              # bare 新聞社 returns nothing
    (26, "ばしょ"): "地図",
    (26, "～べん"): "たこ焼き",                    # Osaka, to match おおさかべん
    (26, "こんど"): "カレンダー",
    (26, "ずいぶん"): "驚く人",
    (26, "いつでも"): "時計",
    (26, "どこでも"): "世界地図",
    (26, "だれでも"): "老若男女",
    (26, "なんでも"): "器用",                      # 器用貧乏 - the jack of all trades
    (26, "こんな～"): "説明",
    (26, "そんな～"): "指差し",
    (26, "あんな～"): "遠く",
    (26, "かたづきます［にもつが～］"): "片付け",
    (26, "ごみ"): "ゴミ箱",
    (26, "だします［ごみを～］"): "ゴミ出し",       # else 出します, from L16
    (26, "もえます［ごみが～］"): "焚き火",
    (26, "げつ・すい・きん"): "カレンダー",        # shares こんど's query on purpose;
                                                  # URL dedup gives each a different one
    (26, "おきば"): "ゴミ捨て場",
    # Caught by eye, not by title or score - see the review sheet. 並ぶ scored 82
    # on 間隔を空けて並ぶ人, which is a social-distancing picture, not "beside".
    (26, "よこ"): "商店街",                        # bare 横 gives 横向きの車
    (26, "びん"): "空き瓶",
    (26, "かん"): "空き缶",
    (26, "～がいしゃ"): "会社",
    # 連絡します auto-reduces to 連絡, whose only real hit is the ほうれんそう
    # business poster - a big green 相談 sign, unreadable as "contact".
    (26, "れんらくします"): "電話をする",
    (26, "こまったなあ。"): "困る",
    (26, "でんしメール"): "Eメール",
    (26, "べつの"): "交換",

    # L27 - four words share a bare word-string with an earlier lesson
    # (homophone, different kanji/meaning in every case - documented in
    # notes/Lesson 27.md). Each needs its own override or it silently
    # inherits the earlier lesson's picture.
    (27, "かいます"): "ペットショップ",             # else L06's 買います (shopping)
    (27, "できます［くうこうが～］"): "空港",        # "空港 工事" scored nothing
    (27, "つけます"): "リュックサック",              # else L14's つけます (a switch);
                                                     # "かばん ポケット" scored nothing
    (27, "いつか"): "将来の夢",                     # else L05's いつか (the 5th day)
    (27, "とります［やすみを～］"): "夏休み",        # shares 取ります with L14/L25
    # Rest caught by eye reading the review sheet, not by score - a passing
    # score doesn't mean a correct picture, and a zero score just means the
    # two-pass fallback fired.
    (27, "はしります［みちを～］"): "運転",          # blank - "道を走る" scored nothing
    (27, "きこえます［おとが～］"): "音符",          # blank - "聞こえます" scored nothing
    (27, "ひらきます［きょうしつを～］"): "黒板",     # "オープン"/"新規オープン"/"新装開店"/"生徒募集" all failed
    (27, "パーティールーム"): "誕生日パーティー",     # "パーティー会場" scored nothing
    (27, "ほかの"): "交換",                         # blank; reuses L26's べつの stand-in
    (27, "はっきり"): "視力検査",                    # "拡大鏡" scored nothing
    (27, "すばらしい"): "OKサイン",                  # blank; reuses established "good" stand-in
    (27, "たとえば"): "説明",                        # blank; reuses L26's こんな～ stand-in
    (27, "とびます"): "飛行機",                      # blank - "飛びます" scored nothing
    (27, "みえます［やまが～］"): "富士山",          # was ワイキキビーチ - a beach, not a mountain
    (27, "けしき"): "夜景",                          # "絶景"/"展望台"/"パノラマ"/"見晴らし" all wrong or
                                                     # nothing - パノラマ matched a 360-camera lens icon
    (27, "ひるま"): "太陽",                          # was ナルコレプシー(!); every daytime-specific try failed
    (27, "～ご"): "タイマー",                        # was 乳液 (skincare lotion)
    (27, "～しか"): "一つだけ",                      # was ハチドリ (a hummingbird)
    (27, "ほとんど"): "多い",                        # abstract quantifier; every specific try failed
    (27, "だいすき［な］"): "ハート",                # was セロリ (celery)
    (27, "そら"): "青空",                            # was 空の棚 - 空(から, empty) not 空(そら, sky)
    (27, "とり"): "小鳥",                            # was 鳥の肉屋 - a poultry shop sign, not a bird
    (27, "かたち"): "図形",                          # plain 形 matched 刑天 (a mythological figure with
                                                     # an axe) - character collision with 刑, not 形

    # L28 - three words collide with an earlier lesson on the search term.
    # やさしい is the dangerous one: L08 teaches 易しい "easy", L28 teaches
    # 優しい "gentle, kind" - identical word string, so without an override it
    # silently inherits L08's 低いハードル (a low hurdle = "easy") picture.
    (28, "やさしい"): "親切",
    # L02's ちがいます。 (with the 。) is "No, you're wrong"; L28's is "be
    # different". Separate notes, but search_term collapses both to 違います.
    (28, "ちがいます"): "比較",     # "間違い" gave 指差し呼称, a safety-check gesture
    # Calendar abbreviation, not the element - bare 土 returns soil and dirt.
    # "土曜日" then landed on one mascot from a 一週間のキャラクター series with
    # nothing marking it as Saturday - caught by opening the PNG, not the title.
    (28, "ど"): "日めくりカレンダー",

    # L28 misses - the literal verb/word form scored nothing at all.
    (28, "うれます［パンが～］"): "売り切れ",
    (28, "かみます"): "ガム",          # 咀嚼 scored nothing
    (28, "えらびます"): "選択",
    (28, "かよいます［だいがくに～］"): "通学",
    (28, "まじめ［な］"): "真面目",
    (28, "ちょうど いい"): "適量",      # "ぴったり" matched 目白押し, a jostling crowd
    (28, "たいてい"): "円グラフ",       # "日課" scored nothing
    (28, "ひにち"): "カレンダー",
    (28, "［ちょっと］おねがいが あるんですが。"): "お願いします",

    # L28 wrong picks - all had a plausible title and a passing score, and all
    # were caught by reading the title list rather than by any number. Four of
    # them meant something close to the OPPOSITE of the word.
    (28, "にんき"): "行列",        # was 人気のないお店 - 人気(ひとけ)がない, a DESERTED shop
    (28, "けいけん"): "ベテラン",   # was トラウマ - trauma, not "experience"
    (28, "えらい"): "表彰",        # was 黙殺 - ignoring someone, not "admirable"
    # "adding a topping" as the prop for "in addition". Earlier tries: ダビデと
    # ゴリアテ (nonsense), 追加 (a smart meter), 足し算 (nothing), プラス (a
    # Phillips screwdriver - reads as a tool, not a plus).
    (28, "それに"): "トッピング",
    (28, "おどります"): "盆踊り",   # 踊ります gave 琉球舞踊 at -18; 盆踊り scores 984
    (28, "それで"): "矢印",        # was 南京錠; reuses the established "therefore" stand-in
    (28, "しばらく"): "砂時計",     # was 熟成肉 (aged meat); "待ち時間" found nothing
    (28, "ねっしん［な］"): "一生懸命",  # was バンギャ - a visual-kei band fan
    (28, "しゅうかん"): "歯磨き",       # was 生活習慣病 (a disease poster); "ルーティン" found nothing
    (28, "ちから"): "力持ち",           # was 超能力 - psychic powers
    (28, "いろ"): "色鉛筆",            # was いろいろな色の舌 - coloured tongues
    (28, "あじ"): "味見",              # was 味覚異常 - a taste disorder
    (28, "しなもの"): "商品棚",         # was 納品書 - a delivery slip, i.e. paperwork
    (28, "ねだん"): "値札",            # was 買い叩く人 - haggling, not the price itself
    (28, "むすこさん"): "青年",         # was a father-and-son bath scene
    (28, "かいわ"): "談笑",            # was 会話をするカラス - talking crows
    (28, "おしらせ"): "掲示板",         # was a cedar tree announcing pollen season

    # ----------------------------------------------------------------------
    # L29 - the 自動詞 lesson, and the worst case for image search so far:
    # 37 of 44 rows need an override. Seventeen headwords are intransitive
    # verbs, whose polite/dictionary forms return only incidental image-search
    # matches - 26 of 44 rows found nothing at all on the first build. Every
    # stand-in below was tested against the live site before being committed.
    #
    # The trick that works for this lesson: don't search the verb, search the
    # OBJECT IN ITS RESULTING STATE. 消えます is invisible to the search but
    # 停電 (a blackout) is not; 破れます finds nothing but シュレッダー does.
    # ----------------------------------------------------------------------
    (29, "あきます［ドアが～］"): "ドア",
    (29, "しまります［ドアが～］"): "シャッター",
    (29, "つきます［でんきが～］"): "電球",        # bare つきます gave チョウザメ, a sturgeon
    (29, "きえます［でんきが～］"): "停電",
    (29, "こみます［みちが～］"): "渋滞",
    (29, "すきます［みちが～］"): "過疎",
    (29, "こわれます［いすが～］"): "故障",
    (29, "われます［コップが～］"): "割れたガラス",
    (29, "おれます［きが～］"): "台風",            # 倒木 / 折れた木 both found nothing
    (29, "やぶれます［かみが～］"): "シュレッダー",
    (29, "よごれます［ふくが～］"): "泥だらけ",
    (29, "つきます［ポケットが～］"): "ポケット",   # else it inherits the OTHER つきます
    (29, "はずれます［ボタンが～］"): "ボタン",
    (29, "とまります［エレベーターが～］"): "エレベーター",
    (29, "まちがえます"): "バツ",
    (29, "おとします"): "落とし物",               # bare 落とします gave ネムルト山, a mountain
    (29, "かかります［かぎが～］"): "南京錠",
    (29, "［お］ちゃわん"): "茶碗",
    (29, "ガラス"): "窓ガラス",                   # was ガラスの靴 - Cinderella's slipper
    (29, "ふくろ"): "レジ袋",                     # was 袋のネズミ - an idiom, a rat in a bag
    (29, "えだ"): "枯れ木",                       # was 枝毛 - split ends of HAIR
    (29, "この へん"): "住宅街",
    (29, "～へん"): "地図",
    (29, "このくらい"): "定規",                   # was 山積みのプレゼント
    (29, "おさきに どうぞ。"): "どうぞ",
    (29, "［ああ、］よかった。"): "嬉しい",
    (29, "いまの でんしゃ"): "電車",
    (29, "～がわ"): "左右",                       # was 退職願 - a resignation letter (側→願)
    (29, "おぼえて いません。"): "物忘れ",
    (29, "あみだな"): "電車の座席",               # 網棚 itself finds nothing; this is a
                                                  # passenger stowing luggage on a train
    (29, "たしか"): "考える人",
    (29, "えきまえ"): "駅",
    (29, "たおれます"): "転ぶ",
    (29, "はり"): "掛け時計",                     # was 釣り針 - a FISHING hook
    (29, "さします"): "指差し",                   # was 天邪鬼
    (29, "にし"): "方位",                         # was 西之島新島, an island; 方位 gives a compass
    (29, "ほう"): "矢印",
}


# --------------------------------------------------------------------------
# Filtering: katakana loanwords transparent from English, and Japanese food
# words that are already English words. Greetings and the ~肉 compounds are
# deliberately kept.
# --------------------------------------------------------------------------
SKIP = {
    "ホテル": "katakana-transparent",
    "パーティー": "katakana-transparent",
    "レモン": "katakana-transparent",
    "すきやき": "food-known-in-english",
    "さしみ": "food-known-in-english",
    "［お］すし": "food-known-in-english",
    "おすし": "food-known-in-english",
    "てんぷら": "food-known-in-english",

    # Lessons 07-15. Only exact phonetic equivalents of the English word are
    # dropped. Deliberately KEPT because the Japanese form still has to be
    # learned even once you know the root: パソコン, ケータイ, ホッチキス,
    # セロテープ, パンチ, コンビニ, ビル, ポスト, ソフト, アルバイト, カラオケ,
    # エアコン, ナンプラー (Thai, not English).
    "スプーン": "katakana-transparent",       # L07
    "ナイフ": "katakana-transparent",
    "フォーク": "katakana-transparent",
    "メール": "katakana-transparent",
    "シャツ": "katakana-transparent",
    "プレゼント": "katakana-transparent",
    "クリスマス": "katakana-transparent",
    # ハンサム is a direct phonetic equivalent but is deliberately KEPT: it is
    # one of the な-adjectives Lesson 08 is built around teaching.
    "レストラン": "katakana-transparent",       # L08
    "スポーツ": "katakana-transparent",        # L09
    "ダンス": "katakana-transparent",
    "クラシック": "katakana-transparent",
    "ジャズ": "katakana-transparent",
    "コンサート": "katakana-transparent",
    "チケット": "katakana-transparent",
    "パンダ": "katakana-transparent",          # L10
    "テーブル": "katakana-transparent",
    "ベッド": "katakana-transparent",
    "ドア": "katakana-transparent",
    "スイッチ": "katakana-transparent",
    "ATM": "katakana-transparent",
    "コーナー": "katakana-transparent",
    "サンドイッチ": "katakana-transparent",     # L11
    "カレー［ライス］": "katakana-transparent",
    "アイスクリーム": "katakana-transparent",
    "クラス": "katakana-transparent",
    "プール": "katakana-transparent",          # L13
    "スキー": "katakana-transparent",
    "パスポート": "katakana-transparent",       # L14
    "カタログ": "katakana-transparent",         # L15
    "サービス": "katakana-transparent",         # L16
    "ジョギング": "katakana-transparent",
    "シャワー": "katakana-transparent",
    "キャッシュカード": "katakana-transparent",
    "ボタン": "katakana-transparent",
    "ピアノ": "katakana-transparent",           # L18
    "－メートル": "katakana-transparent",
    "インターネット": "katakana-transparent",
    "ゴルフ": "katakana-transparent",           # L19
    "ダイエット": "katakana-transparent",
    "ビザ": "katakana-transparent",             # L20
    "ニュース": "katakana-transparent",         # L21
    "デザイン": "katakana-transparent",
    "カンガルー": "katakana-transparent",
    "コート": "katakana-transparent",           # L22
    "セーター": "katakana-transparent",
    "スーツ": "katakana-transparent",
    "ケーキ": "katakana-transparent",
    "ロボット": "katakana-transparent",
    "ユーモア": "katakana-transparent",
    "ダイニングキッチン": "katakana-transparent",
    "サイズ": "katakana-transparent",           # L23
    "ホームステイ": "katakana-transparent",      # L24
    "チャンス": "katakana-transparent",         # L25
    "ボランティア": "katakana-transparent",      # L26 - first Book II lesson
    "ガス": "katakana-transparent",
    "ペット": "katakana-transparent",           # L27 (ロボット already above, L22)
    "ポケット": "katakana-transparent",
    "ガム": "katakana-transparent",             # L28 (ホームステイ already above, L24)
    "ボーナス": "katakana-transparent",
    "ドラマ": "katakana-transparent",
    # Deliberately KEPT in L28: メモします. メモ alone would fail the katakana
    # test, but a `katakana + します` verb compound is a Japanese construction
    # that still has to be learned - same reasoning that kept L14's コピーします.
    # Deliberately KEPT in L26: でんしメール. メール alone is dropped above, but
    # 電子メール is a Japanese compound and the 電子 half still has to be learned.
    # 柔道 is also kept: "judo" is an English word, which is the すし/さしみ test,
    # but unlike すし it is written in kanji here and that kanji has to be
    # learned. Flagged to Fares rather than dropped on my own authority - the
    # same open question as アニメ/マンガ above.

    # Japanese words that entered English intact, the すし/さしみ category.
    "アニメ": "loanword-known-in-english",      # L21
    "マンガ": "loanword-known-in-english",

    # Lessons 02-06. Same test as always - dropped only when the Japanese form
    # is the English word. Deliberately KEPT: シャープペンシル (a Japanese
    # coinage, not "mechanical pencil"), テレビ, デパート, スーパー (all clipped,
    # so the Japanese form still has to be learned), パン (Portuguese) and
    # ビール (Dutch), neither of which is the English word.
    "ノート": "katakana-transparent",           # L02
    "カード": "katakana-transparent",
    "ボールペン": "katakana-transparent",
    "CD": "katakana-transparent",
    "ラジオ": "katakana-transparent",
    "カメラ": "katakana-transparent",
    "コンピューター": "katakana-transparent",
    "チョコレート": "katakana-transparent",
    "コーヒー": "katakana-transparent",
    "ロビー": "katakana-transparent",           # L03
    "エレベーター": "katakana-transparent",
    "エスカレーター": "katakana-transparent",
    "ネクタイ": "katakana-transparent",
    "ワイン": "katakana-transparent",
    "バス": "katakana-transparent",             # L05
    "タクシー": "katakana-transparent",
    "ジュース": "katakana-transparent",         # L06
    "レポート": "katakana-transparent",
    "ビデオ": "katakana-transparent",
    "テニス": "katakana-transparent",
    "サッカー": "katakana-transparent",

    # Textbook drill scenery rather than vocabulary.
    "アジアストア": "proper-noun-not-vocabulary",
    "とうきょうディズニーランド": "proper-noun-not-vocabulary",
}



# Words that appear only inside example sentences and never get a vocabulary
# row of their own. Mined by hand and confirmed not to duplicate a row in any
# other lesson note; the examples are the very sentences they were found in.
# Two of those sentences belonged to words that SKIP drops (ホテル, レモン), so
# without these rows the sentences would be lost from the deck entirely.
EXTRA = {
    12: [
        {"word": "さきます", "kanji": "咲きます", "meaning": "to bloom",
         "example": "はるにさくらがさきます。"},
        {"word": "とまります", "kanji": "泊まります",
         "meaning": "to stay overnight", "example": "ホテルにとまります。"},
        {"word": "いれます", "kanji": "入れます", "meaning": "to put in, add",
         "example": "レモンをいれます。"},
    ],
}



# English translations of the example sentences, for lessons whose source note
# lives in the read-only Obsidian vault (07-15) and so cannot carry a 5th
# ExampleEN table column the way notes/ lessons do. Keyed by (lesson, word).
# Lessons sourced from notes/ get the translation as a table column instead -
# see Lesson 26 for the pattern.
EXAMPLE_EN_OVERRIDE = {
    (7, "きります"): "I cut paper.",
    (7, "おくります"): "I send a letter.",
    (7, "あげます"): "I give a present.",
    (7, "もらいます"): "I receive a present.",
    (7, "かします"): "I lend money.",
    (7, "かります"): "I borrow money.",
    (7, "おしえます"): "I teach Japanese.",
    (7, "ならいます"): "I learn Japanese.",
    (7, "かけます"): "I make a phone call.",
    (7, "て"): "I eat with my hands.",
    (7, "はし"): "I eat ramen with chopsticks.",
    (7, "スプーン"): "I eat with a spoon.",
    (7, "ナイフ"): "I cut bread with a knife.",
    (7, "フォーク"): "I eat with a fork.",
    (7, "はさみ"): "I cut paper with scissors.",
    (7, "パソコン"): "I send an email on my computer.",
    (7, "ケータイ"): "I make a phone call on my mobile phone.",
    (7, "メール"): "I send an email.",
    (7, "ねんがじょう"): "I send a New Year's card.",
    (7, "パンチ"): "I punch a hole in the paper with a hole punch.",
    (7, "ホッチキス"): "I staple the paper with a stapler.",
    (7, "セロテープ"): "I stick it with sellotape.",
    (7, "けしゴム"): "I erase the writing with an eraser.",
    (7, "かみ"): "I cut paper.",
    (7, "はな"): "I give flowers.",
    (7, "シャツ"): "I receive a shirt.",
    (7, "プレゼント"): "I give a present.",
    (7, "にもつ"): "I send luggage.",
    (7, "おかね"): "I lend money.",
    (7, "きっぷ"): "I buy a ticket.",
    (7, "クリスマス"): "A Christmas present.",
    (7, "ちち"): "I give my father a present.",
    (7, "はは"): "I give my mother flowers.",
    (7, "おとうさん"): "How is your father?",
    (7, "おかあさん"): "Please give my regards to your mother.",
    (7, "もう"): "Have you sent it already?",
    (7, "まだ"): "I haven't sent it yet.",
    (7, "これから"): "I'll eat from now.",

    (8, "ハンサム [な]"): "That person is handsome.",
    (8, "きれい [な]"): "It's a beautiful flower.",
    (8, "しずか [な]"): "It's a quiet town.",
    (8, "にぎやか [な]"): "It's a lively town.",
    (8, "ゆうめい [な]"): "A famous restaurant.",
    (8, "しんせつ [な]"): "He is a kind person.",
    (8, "げんき [な]"): "I am well.",
    (8, "ひま [な]"): "I am free today.",
    (8, "べんり [な]"): "A mobile phone is convenient.",
    (8, "すてき [な]"): "That's a nice shirt, isn't it?",
    (8, "おおきい"): "It's a big computer.",
    (8, "ちいさい"): "It's a small mobile phone.",
    (8, "あたらしい"): "It's a new shirt.",
    (8, "ふるい"): "It's an old computer.",
    (8, "いい (よい)"): "It's nice weather, isn't it?",
    (8, "わるい"): "It's bad weather, isn't it?",
    (8, "あつい"): "It's hot today.",
    (8, "さむい"): "It's cold today.",
    (8, "つめたい"): "I drink cold water.",
    (8, "むずかしい"): "Japanese is difficult.",
    (8, "やさしい"): "This homework is easy.",
    (8, "たかい"): "This computer is expensive.",
    (8, "やすい"): "This shirt is cheap.",
    (8, "ひくい"): "The mountain is low.",
    (8, "おもしろい"): "I watch an interesting movie.",
    (8, "おいしい"): "The ramen is delicious.",
    (8, "いそがしい"): "I'm busy today.",
    (8, "たのしい"): "Work is enjoyable.",
    (8, "しろい"): "I buy a white shirt.",
    (8, "くろい"): "I buy a black shirt.",
    (8, "あかい"): "I give red flowers.",
    (8, "あおい"): "I buy a blue shirt.",
    (8, "さくら"): "I look at the cherry blossoms.",
    (8, "やま"): "I go to the mountain.",
    (8, "まち"): "It's my town.",
    (8, "たべもの"): "It's delicious food.",
    (8, "ところ"): "It's a quiet place.",
    (8, "りょう"): "It's my dormitory.",
    (8, "レストラン"): "It's a famous restaurant.",
    (8, "せいかつ"): "Life in Japan.",
    (8, "[お]しごと"): "I do work.",
    (8, "どう"): "How is life in Japan?",
    (8, "どんな～"): "What kind of house is it?",
    (8, "とても"): "It's very delicious.",
    (8, "あまり"): "It's not very delicious.",
    (8, "～が、～"): "Japanese food is delicious, but expensive.",

    (9, "わかります"): "I understand Japanese.",
    (9, "あります"): "There is a car.",
    (9, "すき〔な〕"): "I like soccer.",
    (9, "きらい〔な〕"): "I dislike vegetables.",
    (9, "じょうず〔な〕"): "I am good at English.",
    (9, "へた〔な〕"): "I am poor at dancing.",
    (9, "のみもの"): "Water is a drink.",
    (9, "りょうり"): "I cook.",
    (9, "スポーツ"): "I play sports.",
    (9, "やきゅう"): "I play baseball.",
    (9, "ダンス"): "I dance.",
    (9, "りょこう"): "I travel.",
    (9, "おんがく"): "I listen to music.",
    (9, "うた"): "I sing a song.",
    (9, "クラシック"): "I listen to classical music.",
    (9, "ジャズ"): "I listen to jazz.",
    (9, "コンサート"): "I go to a concert.",
    (9, "カラオケ"): "I do karaoke.",
    (9, "かぶき"): "I watch kabuki.",
    (9, "え"): "I draw a picture.",
    (9, "じ"): "I write characters.",
    (9, "かんじ"): "I study kanji.",
    (9, "ひらがな"): "I learn hiragana.",
    (9, "かたかな"): "I learn katakana.",
    (9, "ローマじ"): "I write in the Roman alphabet.",
    (9, "こまかいおかね"): "I have small change.",
    (9, "チケット"): "I buy a ticket.",
    (9, "じかん"): "I have time.",
    (9, "ようじ"): "I have an errand.",
    (9, "やくそく"): "I make a promise.",
    (9, "アルバイト"): "I do a part-time job.",
    (9, "ごしゅじん"): "Your husband is a teacher.",
    (9, "おっと / しゅじん"): "My husband is a company employee.",
    (9, "おくさん"): "Your wife is beautiful.",
    (9, "つま / かない"): "My wife is a teacher.",
    (9, "こども"): "I have a child.",
    (9, "よく"): "I often watch movies.",
    (9, "だいたい"): "I mostly understand.",
    (9, "たくさん"): "There are many.",
    (9, "すこし"): "I understand a little.",
    (9, "ぜんぜん"): "I don't understand at all.",
    (9, "はやく"): "I go early.",
    (9, "～から"): "Because it's raining, I won't go.",
    (9, "どうして"): "Why aren't you coming?",

    (10, "あります"): "There is a chair.",
    (10, "います"): "There is a dog.",
    (10, "いろいろ〔な〕"): "Various people.",
    (10, "おとこのひと"): "There is a man.",
    (10, "おんなのひと"): "There is a woman.",
    (10, "おとこのこ"): "There is a boy.",
    (10, "おんなのこ"): "There is a girl.",
    (10, "いぬ"): "There is a dog.",
    (10, "ねこ"): "There is a cat.",
    (10, "パンダ"): "There is a panda.",
    (10, "ぞう"): "There is an elephant.",
    (10, "き"): "There is a tree.",
    (10, "もの"): "There is something on the desk.",
    (10, "でんち"): "There is a battery.",
    (10, "はこ"): "There is a box.",
    (10, "スイッチ"): "I turn on the switch.",
    (10, "れいぞうこ"): "There is a refrigerator.",
    (10, "テーブル"): "There is a table.",
    (10, "ベッド"): "There is a bed.",
    (10, "たな"): "There are books on the shelf.",
    (10, "ドア"): "I open the door.",
    (10, "まど"): "I open the window.",
    (10, "ポスト"): "There is a postbox.",
    (10, "ビル"): "There is a tall building.",
    (10, "ATM"): "I withdraw money at the ATM.",
    (10, "コンビニ"): "There is a convenience store.",
    (10, "こうえん"): "I play in the park.",
    (10, "きっさてん"): "I drink coffee at the café.",
    (10, "～や"): "A bakery.",
    (10, "のりば"): "A taxi stand.",
    (10, "けん"): "Kanagawa Prefecture.",
    (10, "うえ"): "It's on the desk.",
    (10, "した"): "It's under the chair.",
    (10, "まえ"): "In front of the school.",
    (10, "うしろ"): "Behind the car.",
    (10, "みぎ"): "It's on the right.",
    (10, "ひだり"): "It's on the left.",
    (10, "なか"): "It's inside the box.",
    (10, "そと"): "It's outside the house.",
    (10, "となり"): "Next to the station.",
    (10, "ちかく"): "Near the school.",
    (10, "あいだ"): "Between the school and the bank.",
    (10, "～や～など"): "There are cats, dogs, and so on.",
    (10, "［どうも］すみません。"): "Thank you very much.",
    (10, "ナンプラー"): "I use fish sauce.",
    (10, "コーナー"): "The book section.",
    (10, "いちばんした"): "The bottom of the shelf.",
    (10, "とうきょうディズニーランド"): "I go to Tokyo Disneyland.",
    (10, "アジアストア"): "I buy it at Asia Store.",

    (11, "います［こどもが～］"): "I have a child.",
    (11, "います［にほんに～］"): "I am in Japan.",
    (11, "かかります"): "It takes time. / It costs money.",
    (11, "やすみます［かいしゃを～］"): "I take a day off work.",
    (11, "ひとつ"): "One apple, please.",
    (11, "ふたつ"): "Two apples, please.",
    (11, "みっつ"): "Three apples, please.",
    (11, "よっつ"): "Four apples, please.",
    (11, "いつつ"): "Five apples, please.",
    (11, "むっつ"): "Six apples, please.",
    (11, "ななつ"): "Seven apples, please.",
    (11, "やっつ"): "Eight apples, please.",
    (11, "ここのつ"): "Nine apples, please.",
    (11, "とお"): "Ten apples, please.",
    (11, "いくつ"): "How many apples are there?",
    (11, "ひとり"): "I'll go alone.",
    (11, "ふたり"): "We'll go, the two of us.",
    (11, "－にん"): "I have three friends.",
    (11, "－だい"): "There are two cars.",
    (11, "－まい"): "I bought three stamps.",
    (11, "－かい"): "I go there once.",
    (11, "りんご"): "I eat an apple.",
    (11, "みかん"): "I eat a mandarin orange.",
    (11, "サンドイッチ"): "I eat a sandwich.",
    (11, "カレー［ライス］"): "I eat curry rice.",
    (11, "アイスクリーム"): "I eat ice cream.",
    (11, "きって"): "I buy a stamp.",
    (11, "はがき"): "I write a postcard.",
    (11, "ふうとう"): "I buy an envelope.",
    (11, "りょうしん"): "My parents are in Japan.",
    (11, "きょうだい"): "I have two siblings.",
    (11, "あに"): "My elder brother is a teacher.",
    (11, "おにいさん"): "Your elder brother is a student.",
    (11, "あね"): "My elder sister is an engineer.",
    (11, "おねえさん"): "Your elder sister is beautiful.",
    (11, "おとうと"): "My younger brother is a high school student.",
    (11, "おとうとさん"): "How old is your younger brother?",
    (11, "いもうと"): "My younger sister is a student.",
    (11, "いもうとさん"): "Where is your younger sister?",
    (11, "がいこく"): "I'll go abroad.",
    (11, "りゅうがくせい"): "I am an international student.",
    (11, "クラス"): "There is a class.",
    (11, "－じかん"): "I study for two hours.",
    (11, "－しゅうかん"): "I traveled for a week.",
    (11, "－かげつ"): "I was in Japan for two months.",
    (11, "－ねん"): "I studied for three years.",
    (11, "～ぐらい"): "I study for about an hour.",
    (11, "どのくらい"): "How long will you be in Japan?",
    (11, "ぜんぶで"): "It's 1000 yen in total.",
    (11, "みんな"): "Everyone is here.",
    (11, "～だけ"): "Only one person will go.",

    (12, "かんたん[な]"): "It's easy homework.",
    (12, "ちかい"): "The station is near.",
    (12, "とおい"): "The park is far.",
    (12, "はやい"): "The car is fast. / I get up early in the morning.",
    (12, "おそい"): "The bus is slow.",
    (12, "おおい"): "This shop has many people.",
    (12, "すくない"): "This room has few people.",
    (12, "あたたかい"): "It's warm today.",
    (12, "すずしい"): "Mornings are cool.",
    (12, "あまい"): "This cake is sweet.",
    (12, "からい"): "The curry is spicy.",
    (12, "おもい"): "This bag is heavy.",
    (12, "かるい"): "This bag is light.",
    (12, "いい"): "I'd prefer coffee.",
    (12, "きせつ"): "My favorite season is summer.",
    (12, "はる"): "Cherry blossoms bloom in spring.",
    (12, "なつ"): "Summer is hot.",
    (12, "あき"): "I look at the autumn leaves in fall.",
    (12, "ふゆ"): "Winter is cold.",
    (12, "てんき"): "How's the weather today?",
    (12, "あめ"): "It's raining.",
    (12, "ゆき"): "It will snow.",
    (12, "くもり"): "It's cloudy today.",
    (12, "ホテル"): "I stay at a hotel.",
    (12, "くうこう"): "I go to the airport.",
    (12, "うみ"): "I swim in the sea.",
    (12, "せかい"): "I want to travel the world.",
    (12, "パーティー"): "I have a party.",
    (12, "[お]まつり"): "I go to the festival.",
    (12, "すきやき"): "I eat sukiyaki.",
    (12, "さしみ"): "I like sashimi.",
    (12, "［お］すし"): "I eat sushi.",
    (12, "てんぷら"): "I make tempura.",
    (12, "ぶたにく"): "I buy pork.",
    (12, "とりにく"): "I cook chicken.",
    (12, "ぎゅうにく"): "Beef is expensive.",
    (12, "レモン"): "I add lemon.",
    (12, "いけばな"): "I do flower arranging.",
    (12, "もみじ"): "I look at the autumn leaves in fall.",
    (12, "どちら"): "Which do you like?",
    (12, "どちらも"): "I like both.",
    (12, "いちばん"): "It's my favorite dish.",
    (12, "ずっと"): "This one is far cheaper.",
    (12, "はじめて"): "I'll go to Japan for the first time.",
    (12, "ただいま"): "I'm home.",
    (12, "おかえりなさい"): "Welcome home.",
    (12, "つかれました"): "I'm tired.",
    (12, "さきます"): "Cherry blossoms bloom in spring.",
    (12, "とまります"): "I stay at a hotel.",
    (12, "いれます"): "I add lemon.",

    (13, "あそびます"): "I play with a friend.",
    (13, "およぎます"): "I swim in the pool.",
    (13, "むかえます"): "I go to meet a friend at the station.",
    (13, "つかれます"): "I got tired.",
    (13, "けっこんします"): "I'll get married next year.",
    (13, "かいものします"): "I shop at the department store.",
    (13, "しょくじします"): "I have a meal at a restaurant.",
    (13, "さんぽします"): "I take a walk in the park.",
    (13, "たいへん［な］"): "It's a tough job.",
    (13, "ほしい"): "I want a car.",
    (13, "ひろい"): "This room is spacious.",
    (13, "せまい"): "The room is narrow.",
    (13, "プール"): "I swim in the pool.",
    (13, "かわ"): "I go fishing in the river.",
    (13, "びじゅつ"): "I study fine arts.",
    (13, "つり"): "I go fishing.",
    (13, "スキー"): "I go skiing.",
    (13, "しゅうまつ"): "I rest on the weekend.",
    (13, "［お］しょうがつ"): "I go home for New Year's.",
    (13, "～ごろ"): "I get up around 7 o'clock.",
    (13, "なにか"): "I want to eat something.",
    (13, "どこか"): "Are you going somewhere?",
    (13, "のどがかわきます"): "I got thirsty.",
    (13, "おなかがすきます"): "I got hungry.",
    (13, "そうしましょう"): "Let's do that.",
    (13, "ごちゅうもんは？"): "May I take your order?",
    (13, "ていしょく"): "A set meal, please.",
    (13, "ぎゅうどん"): "I eat a beef bowl.",
    (13, "～でございます"): "Here is the menu.",
    (13, "べつべつに"): "Separately, please.",

    (14, "つけます"): "I turn on the light.",
    (14, "けします"): "I turn off the light.",
    (14, "あけます"): "I open the door.",
    (14, "しめます"): "I close the door.",
    (14, "いそぎます"): "I hurry there.",
    (14, "まちます"): "I wait for a friend.",
    (14, "もちます"): "I hold the bag.",
    (14, "とります"): "Please pass the salt.",
    (14, "てつだいます"): "I help with the work.",
    (14, "よびます"): "I call a taxi.",
    (14, "はなします"): "I speak in Japanese.",
    (14, "つかいます"): "I use a computer.",
    (14, "とめます"): "I park the car.",
    (14, "みせます"): "I show a photo.",
    (14, "おしえます［じゅうしょを～］"): "I tell you my address.",
    (14, "すわります"): "I sit on the chair.",
    (14, "たちます"): "Please stand up.",
    (14, "はいります［きっさてんに～］"): "I enter the café.",
    (14, "でます［きっさてんを～］"): "I leave the café.",
    (14, "ふります［あめが～］"): "It rains.",
    (14, "コピーします"): "I copy the printout.",
    (14, "でんき"): "I turn on the light.",
    (14, "エアコン"): "I turn on the air conditioner.",
    (14, "パスポート"): "I show my passport.",
    (14, "なまえ"): "I write my name.",
    (14, "じゅうしょ"): "I tell you my address.",
    (14, "ちず"): "I look at the map.",
    (14, "しお"): "Please pass the salt.",
    (14, "さとう"): "I put sugar in the coffee.",
    (14, "もんだい"): "There's a question.",
    (14, "こたえ"): "I say the answer.",
    (14, "よみかた"): "Please teach me how to read the kanji.",
    (14, "～かた"): "I teach the way to use it.",
    (14, "まっすぐ"): "Please go straight.",
    (14, "ゆっくり"): "Please speak slowly.",
    (14, "すぐ"): "I'll go immediately.",
    (14, "また"): "Let's meet again.",
    (14, "あとで"): "I'll call later.",
    (14, "もうすこし"): "A little more, please.",
    (14, "もう～"): "Please say it once more.",
    (14, "さあ"): "Well then, let's go.",
    (14, "あれ？"): "Huh? My wallet isn't here.",
    (14, "信号を右へ曲がってください"): "Turn right at the traffic lights.",
    (14, "これで おねがいします"): "I'd like to pay with this, please.",
    (14, "おつり"): "I receive the change.",

    (15, "おきます"): "I put the book on the desk.",
    (15, "つくります"): "I make a dish.",
    (15, "うります"): "The shop sells shoes.",
    (15, "しります"): "I got to know their name.",
    (15, "すみます"): "I live in Tokyo.",
    (15, "けんきゅうします"): "I do research at university.",
    (15, "しりょう"): "I collect materials.",
    (15, "カタログ"): "I look at the catalogue.",
    (15, "じこくひょう"): "I check the timetable.",
    (15, "ふく"): "I buy new clothes.",
    (15, "せいひん"): "This product is famous.",
    (15, "ソフト"): "I install the software.",
    (15, "でんしじしょ"): "I use an electronic dictionary.",
    (15, "けいざい"): "I study economics.",
    (15, "しやくしょ"): "I go to city hall.",
    (15, "こうこう"): "I graduated from high school.",
    (15, "はいしゃ"): "I go to the dentist.",
    (15, "どくしん"): "He is single.",
    (15, "すみません"): "I'm sorry, I'm late.",
    (15, "みなさん"): "Hello, everyone.",
    (15, "おもいだします"): "I remember my childhood.",
    (15, "いらっしゃいます"): "The teacher is here.",
}
