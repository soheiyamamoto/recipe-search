# レシピ検索帳 — Claude Code パイプライン組み込みガイド

対象: 笠原流 旬のレシピ検索帳(単一HTML) の定常更新を、既存の8段階パイプライン
(spec-writer / code-reviewer / doc-updater サブエージェント構成) に載せるための手順書。

---

## 1. リポジトリ構成(推奨)

既存の「docs/ に仕様、src/ に実装」の規約に合わせた構成です。

```
recipe-search/
├── CLAUDE.md                     # 下記スニペットを追記
├── docs/
│   ├── spec_recipe-search.md     # 本体仕様(spec-writerが管理)
│   └── pipeline_integration.md   # 本書
├── src/
│   └── sanpiryoron_seasonal_recipes.html   # 配布物 = 実装(単一HTML)
├── tools/
│   ├── update_recipes.py         # CSV → HTML 反映(除外・季節・材料の自動判定)
│   ├── Get-SanpiVideoList.ps1    # YouTube Data API → CSV(代替取得手段)
│   └── Convert-CsvToRecipeHtml.ps1
└── data/
    └── youtube_uploads_YYYYMMDD.csv   # 取得したCSV(gitignore推奨: 生成物のため)
```

- 単一HTMLが配布物そのものなので、この案件では `src/` = `dist/` を兼ねます。
  人事名簿システムのような src/dist 分離は不要です。
- `data/` のCSVは再取得可能な生成物なので、コミット対象外(.gitignore)を推奨。
  ※実在の動画情報のみで個人情報は含まないため、履歴管理したい場合はコミットしても可。

## 2. CLAUDE.md 追記スニペット

```markdown
## レシピ検索帳(recipe-search)の規約
- 配布物は src/sanpiryoron_seasonal_recipes.html の単一ファイル。外部依存は
  Google Fonts のみ(オフラインでもレイアウト崩れなしで動作すること)。
- レシピデータは HTML 内の // ===RECIPES_START=== 〜 // ===RECIPES_END===
  区間のみ。手編集せず tools/update_recipes.py 経由で更新する。
- update_recipes.py の除外ルール:
  (1) description が「↓詳しいレシピは本編」で始まる行 = ショート版として除外
  (2) EXCLUDE_KEYWORDS(生配信・密着など)に一致するタイトル = 企画動画として除外
- 材料辞書 MATERIAL_DICT / 季節辞書 SEASON_KEYWORDS の追補は update_recipes.py
  内で行い、変更時は docs/spec_recipe-search.md の辞書一覧も更新する(doc-updater)。
- エンコーディングは UTF-8 BOM(CSV/HTML/ps1 とも)。
- 動作確認はブラウザで開き「検索・季節タブ・件数表示・0件表示」の4点を目視確認。
```

## 3. 8段階パイプラインへのマッピング

段階名は現行パイプラインの呼称に合わせて読み替えてください(要調整箇所)。

| 段階 | この案件での作業 | 担当サブエージェント |
|---|---|---|
| 1. 要求整理 | 更新要望(新着反映/辞書追加/UI改修)を1行で記録 | メイン |
| 2. 仕様化 | spec_recipe-search.md へ差分仕様を追記(辞書変更は新旧対比表) | spec-writer |
| 3. 設計確認 | マーカー区間方式・除外ルールへの影響有無をチェック | spec-writer |
| 4. 実装 | update_recipes.py 実行 or HTML/辞書の修正 | メイン(Claude Code) |
| 5. 自己検証 | 反映件数ログ確認 + node での配列パース確認 + ブラウザ4点確認 | メイン |
| 6. レビュー | git diff をレビュー(件数の増減が想定通りか、除外漏れがないか) | code-reviewer |
| 7. ドキュメント更新 | 仕様書の辞書一覧・件数・最終更新日を同期 | doc-updater |
| 8. リリース | コミット & 配布(LINE共有 / GitHub Pages等) | メイン |

## 4. 定常運用(週次更新)の実行手順

チャンネルは毎週水・土 19時更新のため、**週1回(日曜など)の実行**で十分です。

```bash
# Claude Code へのワンショット指示例
「data/ に最新の youtube_uploads_*.csv を置いた。
 tools/update_recipes.py で src/ のHTMLに反映し、
 反映件数と除外件数を報告、diff で新規追加分のタイトル一覧を見せて。
 タグ無し(materials空)の新着があれば辞書追補案も提示して。」
```

チェックポイント:
1. 反映件数が前回より減っていないか(減少 = 除外ルールの誤爆疑い)
2. 新着のうち「タグ無し」が多い場合は MATERIAL_DICT に材料を追補
3. 季節の自動判定が不自然な新着は、CSVの season 列に手動値を入れて再実行

## 5. 自動判定の仕様(要点)

- **季節**: タイトル内キーワード(筍→春、ゴーヤ→夏、ブリ・鍋→冬 等)を優先し、
  該当なしは公開月で判定(3〜5月=春 / 6〜8月=夏 / 9〜11月=秋 / 12〜2月=冬)。
  現状「通年(all)」は自動では付与されないため、定番料理を通年にしたい場合は
  CSVの season 列に all を指定する。
- **材料**: タイトルから MATERIAL_DICT(約60項目、表記ゆれ込み)に一致する語を
  抽出しタグ最大3件。検索キーワードには表記ゆれ全体を登録するため、
  「ぶり」「鰤」いずれの入力でもヒットする。
- **CSV手動列の優先**: season / materials / exclude 列に値がある行は自動判定より優先。

## 6. 将来のSkill化候補

「CSV→単一HTML反映」の型は、検討中の単一HTMLツール標準Skillと相性が良いため、
以下をSkill化パラメータとして切り出すと他ツール(釣行記録など)へ転用できます:
データマーカー区間方式 / 除外キーワード辞書 / タグ辞書 / UTF-8 BOM入出力。
