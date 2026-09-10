#!/usr/bin/env bash
# selftest.sh — verify_export.py が「落ちるべきときに落ちる」ことを確かめる。
#
# わざとバグのある最小プロジェクト（フォルダを一覧して .png を集める）を作り、
# 書き出して検査にかける。終了コード1が返れば検査は生きている。
# 一度も落ちるところを見ていない検査は信用できない。
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GODOT="${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}"
command -v "$GODOT" >/dev/null 2>&1 || [ -x "$GODOT" ] || GODOT="$(command -v godot || true)"
[ -n "$GODOT" ] && [ -x "$GODOT" ] || { echo "godot が見つからない。GODOT=/path/to/godot を指定してください。"; exit 2; }

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
mkdir -p "$T/assets/frames" "$T/scripts" "$T/build/web"

# 1x1 の透明PNG（base64）を3枚置く
B64='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
for i in 1 2 3; do
  printf '%s' "$B64" | base64 --decode > "$T/assets/frames/frame_00000$i.png"
done

cat > "$T/project.godot" <<'P'
config_version=5
[application]
config/name="selftest"
run/main_scene="res://main.tscn"
config/features=PackedStringArray("4.7")
P
cat > "$T/scripts/loader.gd" <<'P'
extends Node2D

func _ready() -> void:
	var dir := "res://assets/frames"
	var got: Array = []
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".png"):
			got.append(f)
	print("frames found: ", got.size())
P
cat > "$T/main.tscn" <<'P'
[gd_scene load_steps=2 format=3]
[ext_resource type="Script" path="res://scripts/loader.gd" id="1"]
[node name="Main" type="Node2D"]
script = ExtResource("1")
P
cat > "$T/export_presets.cfg" <<'P'
[preset.0]
name="Web"
platform="Web"
runnable=true
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path="build/web/index.html"
[preset.0.options]
P

"$GODOT" --headless --path "$T" --import >/dev/null 2>&1
"$GODOT" --headless --path "$T" --export-release "Web" build/web/index.html >/dev/null 2>&1
[ -f "$T/build/web/index.pck" ] || { echo "書き出しに失敗。Web用のテンプレートが入っているか確認してください。"; exit 2; }

echo "── わざとバグのあるプロジェクトを検査する"
python3 "$HERE/verify_export.py" "$T" --preset Web
rc=$?
echo
if [ "$rc" -eq 1 ]; then
  echo "OK  検査は生きている（終了コード 1 で落ちた）"
  exit 0
fi
echo "NG  落ちるべき場面で落ちなかった（終了コード $rc）。verify_export.py 側が壊れている。"
exit 1
