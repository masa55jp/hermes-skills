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

`comfyui` スキルは汎用の総合ガイドで、**既定が `127.0.0.1:8188`・SDXL/Flux 前提**。
この環境とは食い違うので、**先にこちらを読む。** 手順やAPIの詳細は向こうに任せる。

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

1. **生存確認**: `curl -s -m 5 http://100.127.163.116:8188/system_stats`
   → 届かなければ上の文面で人に頼む。**ここで止まる**
2. ワークフローJSON（API形式）を用意する。組み立て方は `comfyui` スキル
3. モデルとVAEを上の表から選ぶ。Z-Anime なら VAE を忘れない
4. `POST /prompt` で投入
5. 出てきた画像を**実際に見る**。見ずに「できました」と言わない

## つまずきどころ

- ⚠ **tailnet 外からは到達できない。** 外部公開は未整備
- ⚠ **`comfy_image` MCP は `enabled: false`** で、向き先も別（`100.127.163.116:8188` を
  見てはいるが無効）。いまは curl で直接叩く
- ⚠ **画像生成中は Gemma も Qwen も止まっている。** 長いバッチを回す前に、
  他の作業が3060を使っていないか気にする
- ⚠ 3090（`100.117.137.5`）とは別のマシン。混同しない

接続情報の原本は Obsidian のナレッジ「RTX3060エンドポイント_外部接続の参考」。
