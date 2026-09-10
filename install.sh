#!/usr/bin/env bash
# ~/.hermes/skills/ に配置する。既存のカテゴリを丸ごと上書きせず、
# このリポジトリが持つスキルのフォルダだけを同期する。
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"

for s in game-design/game-design-doc creative/svg-character-design godot/godot-web-export; do
  mkdir -p "$DST/$s"
  COPYFILE_DISABLE=1 rsync -rlt --delete \
    --exclude='.DS_Store' --exclude='._*' --exclude='__pycache__' \
    --exclude='compare/' \
    "$SRC/$s/" "$DST/$s/"
  echo "installed  $s"
done

# カテゴリ説明は、まだ無いときだけ置く（他人のスキルと同居しているため）
for c in game-design godot; do
  [ -f "$DST/$c/DESCRIPTION.md" ] || cp "$SRC/$c/DESCRIPTION.md" "$DST/$c/"
done

echo
echo "svg-character-design はラスタライザを1つ必要とします:"
echo "  brew install resvg librsvg"
echo "godot-web-export は Godot 4.x を使います（GODOT 環境変数 / PATH / Godot.app を自動で探索）"
