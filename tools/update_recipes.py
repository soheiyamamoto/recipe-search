#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_recipes.py
YouTubeアップロード一覧CSVからレシピ検索帳HTMLの RECIPES_START〜END 区間を再生成する。

対応CSV列: title, video_id, published_at, url, description
          (任意列: season, materials, exclude があれば優先)
除外ルール:
  1. description が「↓詳しいレシピは本編」で始まる = ショート版(本編と重複)
  2. タイトルに企画系キーワード(生配信・密着など)を含む
"""
import csv, re, sys
from datetime import datetime

CSV_PATH  = sys.argv[1] if len(sys.argv) > 1 else 'youtube_uploads.csv'
HTML_PATH = sys.argv[2] if len(sys.argv) > 2 else 'sanpiryoron_seasonal_recipes.html'

# ---- 材料辞書 (表示タグ: 検索キーワード群) ----
MATERIAL_DICT = {
    'ブリ': ['ブリ','ぶり','鰤'], '鯖': ['サバ','さば','鯖'],
    '鮭': ['鮭','サーモン'], 'アジ': ['アジ','あじ','鯵'],
    'イワシ': ['イワシ','いわし','鰯'], 'サンマ': ['サンマ','さんま','秋刀魚'],
    'タラ': ['タラ','たら','鱈'], 'カツオ': ['カツオ','かつお','鰹'],
    'マグロ': ['マグロ','まぐろ','鮪'], 'タイ': ['鯛'],
    'イカ': ['イカ','いか'], 'エビ': ['エビ','えび','海老'],
    'タコ': ['タコ','たこ','蛸'], 'アサリ': ['アサリ','あさり'],
    '牡蠣': ['牡蠣','カキ','かき'], 'ホタテ': ['ホタテ','帆立'],
    'うなぎ': ['うなぎ','ウナギ','鰻'], 'しらす': ['しらす','ちりめん'],
    '鶏肉': ['鶏','チキン','地鶏','手羽','ささみ','むね','親子丼','唐揚げ','から揚げ','焼き鳥','よだれ鶏'],
    '豚肉': ['豚','ポーク','とんかつ','トンカツ','生姜焼き','しょうが焼き','角煮','チャーシュー','焼豚'],
    '牛肉': ['牛','ビーフ','すき焼き','ステーキ','ハンバーグ','ローストビーフ'],
    'ひき肉': ['ひき肉','挽き肉','ミンチ','そぼろ','つくね','ミートボール','餃子','ぎょうざ','メンチ','麻婆'],
    '卵': ['卵','たまご','玉子','オムレツ','だし巻き','茶碗蒸し','かに玉','天津'],
    '豆腐': ['豆腐','とうふ','厚揚げ','油揚げ'],
    '大根': ['大根','だいこん','おでん'], 'かぶ': ['かぶ','カブ','蕪'],
    'じゃがいも': ['じゃがいも','ジャガイモ','ポテト','新じゃが','肉じゃが','コロッケ'],
    'さつまいも': ['さつまいも','サツマイモ','スイートポテト','大学芋'],
    '里芋': ['里芋','さといも'], '長芋': ['長芋','山芋','とろろ'],
    '人参': ['人参','にんじん','ニンジン'], '玉ねぎ': ['玉ねぎ','たまねぎ','新玉ねぎ'],
    '長ねぎ': ['長ねぎ','ねぎ','ネギ'], 'キャベツ': ['キャベツ','春キャベツ'],
    '白菜': ['白菜','はくさい'], 'レタス': ['レタス'],
    'ほうれん草': ['ほうれん草','ほうれんそう'], '小松菜': ['小松菜'],
    'ニラ': ['ニラ','にら'], 'ピーマン': ['ピーマン','パプリカ'],
    'なす': ['なす','ナス','茄子'], 'トマト': ['トマト','ミニトマト'],
    'きゅうり': ['きゅうり','キュウリ','胡瓜'], 'ゴーヤ': ['ゴーヤ'],
    'かぼちゃ': ['かぼちゃ','カボチャ','南瓜'], 'ごぼう': ['ごぼう','ゴボウ','きんぴら'],
    'れんこん': ['れんこん','レンコン','蓮根'], '筍': ['筍','たけのこ','タケノコ'],
    'アスパラ': ['アスパラ'], 'ブロッコリー': ['ブロッコリー'],
    'もやし': ['もやし'], '枝豆': ['枝豆'], 'とうもろこし': ['とうもろこし','コーン'],
    'オクラ': ['オクラ'], '春雨': ['春雨'], '大葉': ['大葉','しそ','紫蘇'],
    'きのこ': ['きのこ','しめじ','舞茸','まいたけ','エリンギ','しいたけ','椎茸','えのき','マッシュルーム','なめこ'],
    '米・ご飯': ['ご飯','ごはん','炊き込み','丼','チャーハン','炒飯','おにぎり','雑炊','おかゆ','寿司','ちらし','カレー','オムライス','ピラフ','TKG','卵かけ'],
    '麺類': ['うどん','そば','蕎麦','ラーメン','らーめん','パスタ','スパゲ','焼きそば','そうめん','にゅうめん','タンメン','冷やし中華'],
    '味噌汁・汁物': ['味噌汁','みそ汁','豚汁','スープ','お吸い物','けんちん'],
    '鍋': ['鍋','しゃぶ','おでん','ポトフ','すき焼き'],
    'だし': ['だし','出汁','煮干し'],
    '弁当': ['弁当'], '常備菜': ['常備菜','作り置き'],
    'デザート': ['プリン','スイートポテト','ぜんざい','おしるこ','わらび餅','アイス','ケーキ'],
}

SEASON_KEYWORDS = {
    'spring': ['春','筍','たけのこ','菜の花','新玉ねぎ','新じゃが','春キャベツ','アスパラ','桜','ひな祭り','こどもの日','初鰹','山菜','ふき'],
    'summer': ['夏','ゴーヤ','そうめん','冷やし','冷製','梅','土用','うなぎ','枝豆','とうもろこし','スタミナ','オクラ','ミョウガ','みょうが','BBQ','バーベキュー'],
    'autumn': ['秋','さんま','秋刀魚','栗','さつまいも','スイートポテト','新米','月見','戻り鰹','里芋','きのこ'],
    'winter': ['冬','鍋','おでん','ブリ','ぶり','鰤','牡蠣','年末','正月','おせち','年越し','クリスマス','雑煮','七草','大晦日','ぜんざい','白菜'],
}

# レシピ以外の企画動画キーワード (適宜編集)
EXCLUDE_KEYWORDS = ['生配信','密着','発売','舞台裏','フェス','サミット','ついて行った',
                    'オープン初日','市場で食材探し','突破ライブ','ありがとう！生配信']

def guess_season(title, published_at):
    for s, kws in SEASON_KEYWORDS.items():
        if any(kw in title for kw in kws):
            return s
    try:
        m = datetime.fromisoformat(published_at.replace('Z', '+00:00')).month
    except Exception:
        return 'all'
    return {3:'spring',4:'spring',5:'spring',6:'summer',7:'summer',8:'summer',
            9:'autumn',10:'autumn',11:'autumn'}.get(m, 'winter')

def extract_materials(title):
    tags, kws = [], []
    for tag, keywords in MATERIAL_DICT.items():
        if any(kw in title for kw in keywords):
            tags.append(tag)
            kws.extend(keywords)
    seen = set()
    kws = [k for k in kws if not (k in seen or seen.add(k))]
    return tags[:3], kws

def clean_desc(desc, limit=80):
    if not desc:
        return ''
    line = desc.replace('\r', '').split('\n')[0].strip()
    if re.match(r'^(↓|http|■?チャンネル登録|※)', line):
        return ''
    return line[:limit] + ('…' if len(line) > limit else '')

def esc(s):
    return (s or '').replace('\\', '\\\\').replace("'", "\\'")

rows, skipped_short, skipped_plan = [], 0, 0
with open(CSV_PATH, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        title = (row.get('title') or '').strip()
        desc  = row.get('description') or ''
        if not title:
            continue
        if (row.get('exclude') or '').strip():
            skipped_plan += 1; continue
        if desc.startswith('↓詳しいレシピは本編'):
            skipped_short += 1; continue
        if any(kw in title for kw in EXCLUDE_KEYWORDS):
            skipped_plan += 1; continue

        season = (row.get('season') or '').strip().lower() \
                 or guess_season(title, row.get('published_at') or row.get('publishedAt') or '')
        if (row.get('materials') or '').strip():
            kws = row['materials'].split()
            tags = kws[:3]
        else:
            tags, kws = extract_materials(title)

        rows.append(dict(season=season, title=title,
                         url=row.get('url') or f"https://www.youtube.com/watch?v={row.get('video_id') or row.get('videoId')}",
                         desc=clean_desc(desc), tags=tags, kws=kws,
                         published=row.get('published_at') or ''))

# 新しい動画が上に来るように公開日降順
rows.sort(key=lambda r: r['published'], reverse=True)

entries = []
for r in rows:
    kws_js  = ', '.join(f"'{esc(k)}'" for k in r['kws'])
    tags_js = ', '.join(f"'{esc(t)}'" for t in r['tags'])
    entries.append(
        "    {\n"
        f"      season: '{r['season']}',\n"
        f"      title: '{esc(r['title'])}',\n"
        f"      url: '{esc(r['url'])}',\n"
        f"      desc: '{esc(r['desc'])}',\n"
        f"      materials: [{kws_js}],\n"
        f"      tags: [{tags_js}]\n"
        "    }"
    )

block = ("  // ===RECIPES_START===\n  const recipes = [\n"
         + ",\n".join(entries)
         + "\n  ];\n  // ===RECIPES_END===")

with open(HTML_PATH, encoding='utf-8-sig') as f:
    html = f.read()

pattern = re.compile(r'[ \t]*// ===RECIPES_START===.*?// ===RECIPES_END===', re.S)
if not pattern.search(html):
    sys.exit('マーカー RECIPES_START / RECIPES_END が見つかりません')
html = pattern.sub(lambda m: block, html)

with open(HTML_PATH, 'w', encoding='utf-8-sig') as f:
    f.write(html)

print(f'反映: {len(rows)}件 / 除外: ショート版 {skipped_short}件, 企画動画等 {skipped_plan}件')
