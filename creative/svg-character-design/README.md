# svg-character-design — Hermes Agent 用スキル

ゲームキャラクター／マスコット／クリーチャーを **手書きSVG** で高品質に描かせるためのスキルです。
Qwen3.8-27B クラスのローカルモデルを想定し、「いきなり描く」のではなく
**ブリーフ → シルエット → レイヤー計画 → 描画 → レンダリング → 7項目チェック → 修正(最大3回)** の
固定パイプラインで品質を安定させます。Qwen3.8 は画像入力に対応しているので、
`scripts/render_preview.py` が出力する PNG をモデル自身に見せて自己批評させるのが肝です。

## インストール（Hermes）
```bash
cp -r svg-character-design ~/.hermes/skills/creative/svg-character-design
# もしくは
hermes skills install ./svg-character-design
```
`~/.hermes/skills/` 直下でも構いません。認識されているかは `hermes skills list` で確認できます。

## 依存
- python3 + `pip install cairosvg pillow`（または librsvg の `rsvg-convert` / `resvg` / `inkscape`）
- レンダラーが無くても lint だけは動きます。

## 構成
```
SKILL.md                        本体（ワークフロー・構築ルール・アンチパターン）
references/anatomy-and-proportions.md  頭身・顔・手足の比率
references/color-and-light.md          パレット設計・セルシェード・影色の作り方
references/style-presets.md            chibi / kawaii / JRPG / dark-fantasy / mech など
references/svg-techniques.md           path・symbol/use・clipPath・ミラーの書き方
references/quality-checklist.md        レンダリング後のチェックリスト
scripts/render_preview.py       SVG→PNG コンタクトシート + lint + CSS変数インライン化
assets/character-skeleton.svg   レイヤー構造のテンプレート
assets/example-chibi-knight.svg 全ルールを満たした完成例
evals/evals.json                動作確認用テストプロンプト
```

## 使い方の例
- 「パズルゲーム用のかわいいスライムのマスコットをSVGで」
- 「JRPG風の剣士、青白衣装、3/4視点でキャラ選択画面用に」
- 「このロボットのSVG、腕が浮いてるし平面的。デザインは変えずに直して」

## ローカルモデル向けのコツ
- `thinking` を有効にすると Step1〜3 の計画品質が上がります。
- 1回で完璧を狙わせず、必ず `render_preview.py` → チェックリスト → 修正 のループを回させる。
- 同じ世界観のキャラを複数作るときは、1体目のパレットとアウトライン方針を明示して引き継がせる。
