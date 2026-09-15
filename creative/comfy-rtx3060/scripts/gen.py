#!/usr/bin/env python3
"""RTX3060 の ComfyUI で画像を1枚作って、手元に落とす。

  gen.py "プロンプト" -o out.png
  gen.py "プロンプト" -o out.png --model z-anime-distill --size 1024x1024
  gen.py --models              # 使えるモデルと既定値
  gen.py --ping                # 生存確認だけ

★ 繋がらないときは自分で gpu-mode を叩かず、人に頼むこと（SKILL.md 参照）。
"""
import argparse, json, os, sys, time, urllib.request, urllib.error

HOST = os.environ.get("COMFY_HOST", "http://100.127.163.116:8188")

# 検証済みの組み合わせ（2026-09-15 実測）: loader / vae / steps / cfg
MODELS = {
    "z-image-turbo":   ("UnetLoaderGGUF", "z-image-turbo-Q6_K.gguf",            "ae.safetensors",         8,  1.0),
    "z-image-base":    ("UnetLoaderGGUF", "z-image-base-Q6_K.gguf",             "ae.safetensors",        30,  3.5),
    "z-anime-distill": ("UNETLoader",     "z-anime-distill-8step-fp8.safetensors", "z-anime-ae.safetensors", 8, 1.0),
    "z-anime-base":    ("UnetLoaderGGUF", "z-anime-base-q8_0.gguf",             "z-anime-ae.safetensors", 30, 3.5),
}
CLIP = "qwen_3_4b_fp8_mixed.safetensors"


def api(path, obj=None, raw=False, timeout=60):
    url = HOST + path
    req = urllib.request.Request(url, data=json.dumps(obj).encode() if obj else None,
                                 headers={"Content-Type": "application/json"} if obj else {})
    r = urllib.request.urlopen(req, timeout=timeout)
    return r.read() if raw else json.loads(r.read())


def ping():
    try:
        api("/system_stats", timeout=6); return True
    except Exception:
        return False


DOWN = """RTX3060 の ComfyUI が起動していません。切り替えをお願いします:
  ssh llm@100.127.163.116
  gpu-mode status     # いま何が動いているか
  gpu-mode comfy      # 汎用（Z-Image 系）
  gpu-mode manga      # 漫画・イラスト（Z-Anime 系）
切り替えには数十秒〜数分かかります。
⚠ GPU は排他なので、自分で切り替えないこと（Gemma / Qwen を巻き込みます）。"""


def build(prompt, model, w, h, steps, cfg, seed, negative=""):
    kind, unet, vae, _, _ = MODELS[model]
    loader = {"class_type": kind, "inputs": ({"unet_name": unet} if kind == "UnetLoaderGGUF"
              else {"unet_name": unet, "weight_dtype": "fp8_e4m3fn"})}
    return {
        "1": loader,
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": CLIP, "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "4": {"class_type": "TextEncodeZImageOmni", "inputs": {"clip": ["2", 0], "prompt": prompt, "auto_resize_images": True}},
        "5": {"class_type": "TextEncodeZImageOmni", "inputs": {"clip": ["2", 0], "prompt": negative, "auto_resize_images": True}},
        "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
        "7": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
              "latent_image": ["6", 0], "seed": seed, "steps": steps, "cfg": cfg,
              "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "gen"}},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("-o", "--out", default="out.png")
    ap.add_argument("--model", default="z-image-turbo", choices=list(MODELS))
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--steps", type=int); ap.add_argument("--cfg", type=float)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--negative", default="")
    ap.add_argument("--models", action="store_true"); ap.add_argument("--ping", action="store_true")
    a = ap.parse_args()

    if a.models:
        print(f"{'モデル':18} {'ローダー':16} {'VAE':24} steps  cfg")
        for k, (kind, unet, vae, st, cfg) in MODELS.items():
            print(f"{k:18} {kind:16} {vae:24} {st:5}  {cfg}")
        print("\n★ z-anime 系は必ず z-anime-ae.safetensors。忘れると色が壊れる")
        return 0
    if a.ping:
        ok = ping(); print("ComfyUI: " + ("起動しています" if ok else "起動していません")); 
        if not ok: print("\n" + DOWN)
        return 0 if ok else 1
    if not a.prompt:
        ap.error("プロンプトを指定してください")
    if not ping():
        print(DOWN, file=sys.stderr); return 2

    w, h = (int(x) for x in a.size.lower().split("x"))
    _, _, _, dsteps, dcfg = MODELS[a.model]
    seed = a.seed or int(time.time() * 1000) % 2**31
    wf = build(a.prompt, a.model, w, h, a.steps or dsteps, a.cfg if a.cfg is not None else dcfg, seed, a.negative)

    try:
        pid = api("/prompt", {"prompt": wf, "client_id": "gen.py"})["prompt_id"]
    except urllib.error.HTTPError as e:
        print("投入に失敗:", e.read().decode("utf-8", "replace")[:400], file=sys.stderr); return 1
    print(f"投入: {a.model} {w}x{h} steps={a.steps or dsteps} seed={seed}")

    for _ in range(240):
        q = api("/queue")
        if not q.get("queue_running") and not q.get("queue_pending"):
            break
        time.sleep(2)
    h_ = api(f"/history/{pid}").get(pid, {})
    st = h_.get("status", {})
    if not st.get("completed"):
        for m in st.get("messages", []):
            if m[0] == "execution_error":
                print("実行エラー:", m[1].get("exception_message", "")[:300], file=sys.stderr)
        return 1
    imgs = [i for _, o in (h_.get("outputs") or {}).items() for i in o.get("images", [])]
    if not imgs:
        print("画像が返ってきませんでした", file=sys.stderr); return 1
    f = imgs[0]
    data = api(f"/view?filename={f['filename']}&subfolder={f.get('subfolder','')}&type={f.get('type','output')}",
               raw=True, timeout=120)
    open(a.out, "wb").write(data)
    print(f"✓ {a.out}  ({len(data):,} bytes)")
    print("\n★ 出来た画像を実際に見てから報告すること。見ずに「できました」と言わない。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
