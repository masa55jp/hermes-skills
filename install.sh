#!/usr/bin/env bash
# ~/.hermes/skills/ に配置する。既存のカテゴリを丸ごと上書きせず、
# このリポジトリが持つスキルのフォルダだけを同期する。
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DST="${HERMES_SKILLS_DIR:-$HOME/.hermes/skills}"

for s in game-design/game-design-doc creative/svg-character-design; do
  mkdir -p "$DST/$s"
  COPYFILE_DISABLE=1 rsync -rlt --delete \
    --exclude='.DS_Store' --exclude='._*' --exclude='__pycache__' \
    "$SRC/$s/" "$DST/$s/"
  echo "installed  $s"
done

# カテゴリ説明は、まだ無いときだけ置く（他人のスキルと同居しているため）
[ -f "$DST/game-design/DESCRIPTION.md" ] || cp "$SRC/game-design/DESCRIPTION.md" "$DST/game-design/"

echo
echo "svg-character-design はラスタライザを1つ必要とします:"
echo "  brew install resvg librsvg"
