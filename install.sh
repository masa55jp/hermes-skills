#!/usr/bin/env bash
# ~/.hermes/skills/ に配置する。既存のカテゴリを丸ごと上書きせず、
# このリポジトリが持つスキルのフォルダだけを同期する。
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"

for s in game-design/game-design-doc creative/svg-character-design creative/svg-game-ui creative/svg-tileset godot/godot-web-export media/japanese-narration; do
  mkdir -p "$DST/$s"
  COPYFILE_DISABLE=1 rsync -rlt --delete \
    --exclude='.DS_Store' --exclude='._*' --exclude='__pycache__' \
    --exclude='compare/' \
    "$SRC/$s/" "$DST/$s/"
  echo "installed  $s"
done

# カテゴリ説明は、まだ無いときだけ置く（他人のスキルと同居しているため）
for c in game-design godot media; do
  [ -f "$DST/$c/DESCRIPTION.md" ] || cp "$SRC/$c/DESCRIPTION.md" "$DST/$c/"
done

echo
echo "svg-character-design / svg-game-ui / svg-tileset はラスタライザを1つと Pillow を必要とします:"
echo "  brew install resvg librsvg && pip3 install pillow"
echo "godot-web-export は Godot 4.x を使います（GODOT 環境変数 / PATH / Godot.app を自動で探索）"
echo "japanese-narration は say-ja を PATH に置く必要があります:"
echo "  cp media/japanese-narration/scripts/say-ja ~/.local/bin/ && chmod +x ~/.local/bin/say-ja"
