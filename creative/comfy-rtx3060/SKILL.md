---
name: comfy-rtx3060
description: "この環境で画像を生成するときに読む。ComfyUI は Mac ではなく RTX3060（100.127.163.116:8188）にあり、Z-Image / Z-Image-Turbo / Z-Anime の4モデルが入っている。★GPU は排他で、gpu-mode で起動していないと届かない。イラスト・キャラクター・背景・アイキャッチ・漫画絵を作るとき、および ComfyUI に繋がらないときに最初に読む。汎用の ComfyUI 知識は comfyui スキルの担当。"
version: 1.0.0
author: dtn / Hermes Agent
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [comfyui, 画像生成, z-image, z-anime, rtx3060, 環境固有]
    related_skills: [comfyui, svg-character-design]
---

# この環境の ComfyUI（RTX3060）

**このスキルだけで画像生成が完結する。** 他のスキルを読みに行く必要はない。

⚠ 汎用の `comfyui` スキルは `127.0.0.1:8188`・SDXL/Flux 前提で、**この環境とは食い違う。**
ノードを自作したり、ComfyUI 自体を入れ直すときだけ、そちらを見る。

## 大前提 — GPU は排他。起動していないと届かない

```
ホスト  100.127.163.116:8188   （Tailscale。tailnet 内からのみ）
ヘルス  GET /system_stats
投入    POST /prompt
```

RTX3060 は **VRAM 12GB で、一度に1つのモデルしか動かせない。**
Gemma4-12B（:8080）/ Qwen3.5-9B（:8004）/ ComfyUI（:8188）は**同時に立たない。**

★★ **繋がらないときは、自分で切り替えない。人に頼む。**
`gpu-mode` は他のサービスを止めるので、エージェントが勝手に叩くと
誰かが使っている Gemma や Qwen を巻き込む。伝える内容:

```
RTX3060 の ComfyUI が起動していません。切り替えをお願いします:
  ssh llm@100.127.163.116
  gpu-mode status     # いま何が動いているか
  gpu-mode comfy      # 汎用（Z-Image 系）
  gpu-mode manga      # 漫画・イラスト（Z-Anime 系）
切り替えには数十秒〜数分かかります。
```

⚠ `comfy` と `manga` は**中身が同じ ComfyUI プロセス**で、違うのは既定モデルだけ。
ComfyUI はワークフロー単位でモデルを読むので、**どちらが起動していても4モデル全部使える。**
モードは意図の記録に近い。

## 入っているモデル（4つ）

| ファイル | ステップ | 用途 |
|---|---|---|
| `z-image-turbo-Q6_K.gguf` | **8** | 汎用・高速。下書き、大量生成、アイキャッチ |
| `z-image-base-Q6_K.gguf` | **30〜50** | 汎用・高品質。仕上げ |
| `z-anime-distill-8step-fp8.safetensors` | **8** | 漫画・イラスト・高速 |
| `z-anime-base-q8_0.gguf` | **30〜50** | 漫画・イラスト・高品質 |

**選び方**: 試行錯誤の段階は turbo / distill（8ステップ）、決まってから base（30〜50）。

## ★ 最短の使い方

```bash
python3 scripts/gen.py "プロンプト" -o out.png
python3 scripts/gen.py "プロンプト" -o out.png --model z-anime-distill --size 1024x1024
python3 scripts/gen.py --models     # モデルと既定値
python3 scripts/gen.py --ping       # 生存確認だけ
```

**ワークフローを組む必要はない。** モデル・VAE・ステップ・cfg の対応は
`scripts/gen.py` に検証済みの値で入っている。繋がらなければ人に頼む文面を出して止まる。

## ★★ `CheckpointLoaderSimple` は 0 件。それで正常

**ここを間違えると「モデルが空です」と誤報告する。**
Z-Image / Z-Anime は**チェックポイントではなく拡散モデル（unet）**として置かれている。
1ファイル完結の SDXL 型ではなく、**拡散モデル・VAE・テキストエンコーダを別々に読む**構成。

| モデル | 読むノード | VAE |
|---|---|---|
| `z-image-turbo-Q6_K.gguf` | `UnetLoaderGGUF` | `ae.safetensors` |
| `z-image-base-Q6_K.gguf` | `UnetLoaderGGUF` | `ae.safetensors` |
| `z-anime-base-q8_0.gguf` | `UnetLoaderGGUF` | **`z-anime-ae.safetensors`** |
| `z-anime-distill-8step-fp8.safetensors` | `UNETLoader`（`weight_dtype: fp8_e4m3fn`） | **`z-anime-ae.safetensors`** |

- テキストエンコーダ: `CLIPLoader` → `qwen_3_4b_fp8_mixed.safetensors` / `type: qwen_image`
- プロンプトのノードは **`TextEncodeZImageOmni`**（`CLIPTextEncode` ではない）
- 空の latent は **`EmptySD3LatentImage`**
- ⚠ `type` は実質無視されエンコーダ本体から判定される。ただし **`flux2` を指定すると
  次元不一致で落ちる**（`qwen_image` を使う）

自分でワークフローを組むなら `workflows/zimage.json` を雛形にする（`PROMPT_HERE` を置換）。

⚠ **Z-Anime を使うときは `z-anime-ae.safetensors` を VAE に指定する。** 専用VAEで、
これを忘れると色が壊れる。Z-Image 系とは共用しない。

## プロンプトの書き方

★ **Z-Anime はタグ式ではない。自然言語で書く。**
Danbooru風の `1girl, solo, blue_hair, ...` ではなく、文章で情景を書く設計。
Z-Image 系も同じく自然言語。

- 解像度 512×512〜2048×2048、アスペクト比は自由
- 8GB VRAM でも動く設計なので、12GB なら余裕がある

## 出所（記事にするときに要る）

- **Z-Image / Z-Image-Turbo は公式**。[Tongyi-MAI](https://huggingface.co/Tongyi-MAI)。
  最終更新 2026-01-28 / 01-30 で**それ以降 新版なし＝手元のものが最新**
- **Z-Anime は公式ではない**。[SeeSee21/Z-Anime](https://huggingface.co/SeeSee21/Z-Anime) が本家で、
  Z-Image Base を **LoRAマージではなくフルファインチューン**したアニメ特化版。
  ベースと同じ S3-DiT（6B）

## 手順

1. `python3 scripts/gen.py --ping` → 届かなければ**人に頼んで止まる**
2. `python3 scripts/gen.py "プロンプト" -o out.png --model <上の表から>`
3. **出来た画像を実際に見る。** 見ずに「できました」と言わない

## つまずきどころ

- ⚠ **tailnet 外からは到達できない。** 外部公開は未整備
- ⚠ **`comfy_image` MCP は `enabled: false`** で、向き先も別（`100.127.163.116:8188` を
  見てはいるが無効）。いまは curl で直接叩く
- ⚠ **画像生成中は Gemma も Qwen も止まっている。** 長いバッチを回す前に、
  他の作業が3060を使っていないか気にする
- ⚠ **`CheckpointLoaderSimple` が空でも異常ではない**（上記）。実際に Hermes がここで
  「モデルが空」と誤報告した（2026-09-15）
- ⚠ 3090（`100.117.137.5`）とは別のマシン。混同しない

## 検証済み（2026-09-15 実測）

4モデルすべてで実際に画像が出ることを確認した。

| モデル | 結果 |
|---|---|
| z-image-turbo（8step） | OK。「木のテーブルの赤いリンゴ」が正しく出た |
| z-image-base（30step） | OK |
| z-anime-distill（8step） | OK。アニメ調の教室の情景が出た |
| z-anime-base（30step） | OK |

CLIP の `type` は `qwen_image` / `lens` / `sd3` / `lumina2` のどれでも同じ絵になった。
`flux2` だけ次元不一致で落ちる。**`qwen_image` を使う。**

接続情報の原本は Obsidian のナレッジ「RTX3060エンドポイント_外部接続の参考」。
