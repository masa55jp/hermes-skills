#!/usr/bin/env python3
"""
verify_export.py — 書き出したGodotプロジェクトが、エディタと同じように動くかを確かめる。

エディタと書き出し版は別のファイルシステムになる。いちばん刺さるのは
「元の .png がフォルダから消え、.import だけが残る」こと。拡張子で絞って
フレームを集めるコードは、エディタで16枚・書き出し版で0枚になる。
例外は出ない。画面から消えるだけ。

Usage:
  python3 verify_export.py [PROJECT_DIR] [--preset NAME] [--pck PATH]
                           [--boot-seconds N] [--json]

終了コード 0 = 全通過 / 1 = 未通過あり / 2 = 検査自体が実行できない
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

GODOT_CANDIDATES = [
    os.environ.get("GODOT", ""),
    "/Applications/Godot.app/Contents/MacOS/Godot",
    "/Applications/Godot_mono.app/Contents/MacOS/Godot",
]


def find_godot() -> str:
    for c in GODOT_CANDIDATES:
        if c and os.path.exists(c):
            return c
    for n in ("godot", "godot4", "Godot"):
        p = shutil.which(n)
        if p:
            return p
    sys.exit("2:godot が見つからない。GODOT=/path/to/godot を指定してください。")


# ---------------------------------------------------------------- プロジェクト側を読む
def read_preset(project: str, preset_name: str | None):
    """export_presets.cfg から (プリセット名, export_path) を返す。"""
    f = os.path.join(project, "export_presets.cfg")
    if not os.path.exists(f):
        sys.exit(f"2:{f} が無い。書き出しプリセットが未設定です。")
    raw = open(f, encoding="utf-8").read()
    blocks = re.split(r"\n(?=\[preset\.\d+\])", raw)
    for b in blocks:
        name = re.search(r'^name="([^"]*)"', b, re.M)
        path = re.search(r'^export_path="([^"]*)"', b, re.M)
        if not name:
            continue
        if preset_name and name.group(1) != preset_name:
            continue
        return name.group(1), (path.group(1) if path else "")
    sys.exit(f"2:プリセット '{preset_name}' が export_presets.cfg に無い。")


def autoload_paths(project: str) -> list[str]:
    f = os.path.join(project, "project.godot")
    if not os.path.exists(f):
        return []
    body = open(f, encoding="utf-8").read()
    sec = re.search(r"\[autoload\](.*?)(?=\n\[|\Z)", body, re.S)
    if not sec:
        return []
    return [m.replace("*", "") for m in re.findall(r'"\*?(res://[^"]+)"', sec.group(1))]


LISTING_API = re.compile(
    r"DirAccess\.get_files_at|DirAccess\.get_directories_at|DirAccess\.open"
    r"|\.get_files\(|\.get_directories\(|list_dir_begin")


def scanned_dirs(project: str) -> tuple[list[str], list[str]]:
    """(実行時に一覧される可能性が高いフォルダ, ただ参照されているだけのフォルダ)。

    フォルダ一覧のAPIを使っている .gd の中にある res:// のフォルダ文字列だけを
    「一覧される」側に入れる。明示パスで load しているだけのフォルダは、
    書き出し版でも普通に読めるので対象外。ここを分けないと誤検出になる。
    """
    scanned, plain = set(), set()
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in (".godot", ".git", "build")]
        for fn in files:
            if not fn.endswith(".gd"):
                continue
            try:
                text = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            # コメントを落としてから判定する。落とし穴を説明したコメントに
            # DirAccess.get_files_at() と書いてあるだけで誤検出したことがある。
            code = re.sub(r"#[^\n]*", "", text)
            lists = bool(LISTING_API.search(code))
            for lit in re.findall(r'"(res://[^"]*)"', code):
                p = lit.rstrip("/")
                if not p.startswith("res://") or len(p) <= len("res://"):
                    continue
                tail = p.rsplit("/", 1)[-1]
                if "." in tail or not tail:
                    continue
                (scanned if lists else plain).add(p)
    return sorted(scanned), sorted(plain - scanned)


def tool_scripts(project: str) -> list[str]:
    """@tool / EditorPlugin なスクリプト＝書き出し版では動かないもの。"""
    out = []
    for root, dirs, files in os.walk(project):
        dirs[:] = [d for d in dirs if d not in (".godot", ".git", "build")]
        for fn in files:
            if not fn.endswith(".gd"):
                continue
            p = os.path.join(root, fn)
            try:
                head = open(p, encoding="utf-8", errors="ignore").read(400)
            except OSError:
                continue
            if re.match(r"\s*@tool\b", head) or "extends EditorPlugin" in head:
                out.append("res://" + os.path.relpath(p, project).replace(os.sep, "/"))
    return out


# ---------------------------------------------------------------- 書き出し版に問い合わせる
PROBE = '''extends SceneTree

func _walk(p: String, acc: Array) -> void:
	for f in DirAccess.get_files_at(p):
		acc.append(p.path_join(f))
	for d in DirAccess.get_directories_at(p):
		_walk(p.path_join(d), acc)

func _initialize() -> void:
	var ok := ProjectSettings.load_resource_pack(%PCK%)
	print("R|pack_loaded|", ok)
	if not ok:
		quit(); return
	var all: Array = []
	_walk("res://", all)
	print("R|total|", all.size())
	for p in all:
		print("R|entry|", p)
	for p in %DIRS%:
		var files := DirAccess.get_files_at(p)
		var usable: Array = []
		for f in files:
			if not (f.ends_with(".import") or f.ends_with(".remap") or f.ends_with(".uid")):
				usable.append(f)
		print("R|dir|", p, "|", files.size(), "|", usable.size())
	quit()
'''


def probe(godot: str, pck: str, dirs: list[str]):
    tmp = tempfile.mkdtemp(prefix="godot-verify-")
    open(os.path.join(tmp, "project.godot"), "w", encoding="utf-8").write(
        'config_version=5\n[application]\nconfig/name="verify"\n')
    src = (PROBE.replace("%PCK%", json.dumps(pck))
                .replace("%DIRS%", "[" + ", ".join(json.dumps(d) for d in dirs) + "]"))
    open(os.path.join(tmp, "probe.gd"), "w", encoding="utf-8").write(src)
    r = subprocess.run([godot, "--headless", "--path", tmp, "--script", "probe.gd"],
                       capture_output=True, text=True, timeout=300)
    entries, dirinfo, loaded, total = [], {}, False, 0
    for line in (r.stdout or "").splitlines():
        if not line.startswith("R|"):
            continue
        parts = line.split("|")
        if parts[1] == "pack_loaded":
            loaded = parts[2].strip() == "true"
        elif parts[1] == "total":
            total = int(parts[2].strip())
        elif parts[1] == "entry":
            entries.append(parts[2].strip())
        elif parts[1] == "dir":
            dirinfo[parts[2].strip()] = (int(parts[3]), int(parts[4]))
    shutil.rmtree(tmp, ignore_errors=True)
    return loaded, total, entries, dirinfo


def boot(godot: str, pck: str, seconds: int) -> tuple[int, list[str]]:
    """書き出した pck をそのまま起動し、エラー行を数える。"""
    try:
        p = subprocess.run([godot, "--headless", "--main-pack", pck],
                           capture_output=True, text=True, timeout=seconds)
        out = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        out = ((e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")) \
            + ((e.stderr or b"").decode("utf-8", "replace") if isinstance(e.stderr, bytes) else (e.stderr or ""))
    bad = [l for l in out.splitlines()
           if re.search(r"SCRIPT ERROR|^ERROR:|Failed to load|Parse Error", l)]
    return len(bad), bad[:6]


# ---------------------------------------------------------------- 本体
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--preset", default=None, help="export_presets.cfg のプリセット名")
    ap.add_argument("--pck", default=None, help="pck を直接指定する")
    ap.add_argument("--boot-seconds", type=int, default=6)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    project = os.path.abspath(a.project)
    godot = find_godot()
    preset, export_path = read_preset(project, a.preset)

    pck = a.pck or os.path.join(project, os.path.splitext(export_path)[0] + ".pck")
    if not os.path.exists(pck):
        sys.exit(f"2:{pck} が無い。先に書き出してください。")

    dirs, plain_dirs = scanned_dirs(project)
    loaded, total, entries, dirinfo = probe(godot, pck, dirs)
    errs, err_lines = boot(godot, pck, a.boot_seconds)

    out_dir = os.path.dirname(export_path).strip("/")
    in_pack_out = [e for e in entries if out_dir and e.startswith(f"res://{out_dir}/")]
    autos = autoload_paths(project)
    tools = set(tool_scripts(project))
    tool_in_pack = sorted({e for e in entries
                           if re.sub(r"\.(remap|gdc)$", "", e).replace(".gdc", ".gd") in tools
                           or re.sub(r"\.remap$", "", e) in tools}
                          - set(autos))

    checks = []
    checks.append(("書き出した pack が読める", loaded, "" if loaded else "load_resource_pack が false"))

    empty = {d: v for d, v in dirinfo.items() if v[1] == 0}
    listed = {d: v for d, v in dirinfo.items() if v[0] > 0}
    broken = {d: v for d, v in listed.items() if v[1] == 0}
    checks.append((
        "実行時に走査するフォルダが空でない", not broken,
        "" if not broken else
        "; ".join(f"{d} は {v[0]}件あるが全部 .import/.remap（拡張子で絞ると0件）"
                  for d, v in broken.items())))

    checks.append(("書き出し先が pack の中に入っていない", not in_pack_out,
                   "" if not in_pack_out else f"{len(in_pack_out)}件: " + ", ".join(in_pack_out[:3])))
    checks.append((f"pack 単体で起動してエラー0件（{a.boot_seconds}秒）", errs == 0,
                   "" if errs == 0 else f"{errs}件: " + " / ".join(err_lines[:2])))

    if a.json:
        print(json.dumps({
            "project": project, "preset": preset, "pck": pck, "entries": total,
            "checks": [{"name": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
            "dirs": {k: {"entries": v[0], "usable": v[1]} for k, v in dirinfo.items()},
            "advice_editor_only_scripts": tool_in_pack,
            "dirs_referenced_but_not_listed": plain_dirs,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"== {os.path.basename(project)} / preset '{preset}' / {total} エントリ")
        print(f"   {pck}\n")
        for n, ok, d in checks:
            print(f"  [{'x' if ok else ' '}] {n}")
            if d:
                print(f"      → {d}")
        if dirinfo:
            print("\n  実行時に一覧されうるフォルダ（書き出し版での中身）")
            for d, (n, u) in sorted(dirinfo.items()):
                mark = "★" if (n > 0 and u == 0) else " "
                state = "pack に無い" if n == 0 else f"{n}件中 使えるファイル {u}件"
                print(f"   {mark} {d}  … {state}")
        if plain_dirs:
            print(f"\n  参考: 明示パスで読んでいるだけのフォルダ {len(plain_dirs)}件は対象外")
        if tool_in_pack:
            print(f"\n  助言: @tool / EditorPlugin なスクリプトが pack に {len(tool_in_pack)}件ある。")
            print("        書き出し版では動かないので、容量として無駄。ただし autoload が")
            print("        辿っている可能性があるため、除外したら必ず起動を測り直すこと。")
            for e in tool_in_pack[:5]:
                print(f"          {e}")
        bad = [n for n, ok, _ in checks if not ok]
        print()
        print("  全通過" if not bad else f"  未通過 {len(bad)}件: " + " / ".join(bad))
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as e:
        if isinstance(e.code, str) and e.code.startswith("2:"):
            print(e.code[2:], file=sys.stderr)
            sys.exit(2)
        raise
