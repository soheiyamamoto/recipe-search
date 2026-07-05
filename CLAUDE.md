# CLAUDE.md

## レシピ検索帳(recipe-search)の規約
- 配布物は src/sanpiryoron_seasonal_recipes.html の単一ファイル。外部依存は
  Google Fonts のみ(オフラインでもレイアウト崩れなしで動作すること)。
- スマホ対応の付属物として src/manifest.webmanifest と src/icons/(PWA・
  ホーム画面アイコン)を併置。HTML 単体でも(アイコン無しで)動作すること。
- 公開は GitHub Pages(.github/workflows/pages.yml)。src/ のみ公開し、
  sanpiryoron_seasonal_recipes.html を index.html として配信。docs/ は非公開。
- レシピデータは HTML 内の // ===RECIPES_START=== 〜 // ===RECIPES_END===
  区間のみ。手編集せず tools/update_recipes.py 経由で更新する。
- update_recipes.py の除外ルール:
  (1) description が「↓詳しいレシピは本編」で始まる行 = ショート版として除外
  (2) EXCLUDE_KEYWORDS(生配信・密着など)に一致するタイトル = 企画動画として除外
- 材料辞書 MATERIAL_DICT / 季節辞書 SEASON_KEYWORDS の追補は update_recipes.py
  内で行い、変更時は docs/spec_recipe-search.md の辞書一覧も更新する(doc-updater)。
- エンコーディングは UTF-8 BOM(CSV/HTML/ps1 とも)。
- 動作確認はブラウザで開き「検索・季節タブ・件数表示・0件表示」の4点を目視確認。
