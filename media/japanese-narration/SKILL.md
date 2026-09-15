---
name: japanese-narration
description: "日本語のナレーション音声を作る。動画のナレーション、読み上げ、ボイスオーバー、「喋らせて」「音声にして」と言われたときに使う。既定は RTX3090 の MioTTS（実時間の7〜8倍速・任意の声を複製できる）で、届かなければ Mac の Irodori-TTS に自動で切り替わる。どちらもローカルで、クラウドAPIを使わない。★読み間違いは聞かないと気づけないので、生成したら必ず書き起こしで照合する工程まで含める。"
version: 2.0.0
author: dtn / Hermes Agent
license: MIT
platforms: [macos]
dependencies:
  - say-ja（~/.local/bin/say-ja）
  - MioTTS（RTX3090 の 100.117.137.5:8021。落ちていたら人に起動を頼む）
  - フォールバック用に ~/.venvs/hf-mlx-audio と ~/dev/hyperframes-test
metadata:
  hermes:
    tags: [tts, 音声, ナレーション, 日本語, miotts, irodori, 声質複製, オフライン]
    related_skills: [media-use, hyperframes-audio]
---

# 日本語ナレーションを作る

**`say-ja` を呼ぶだけ。エンジンの選択は自動。**

```bash
say-ja "読み上げる文章です。" -o out.wav        # 1本
say-ja --voice male "文章です。" -o out.wav      # 男性の声
say-ja --ref 見本.wav "文章です。" -o out.wav    # ★任意の声を複製
say-ja --lines lines.json --out vo/             # まとめて → vo/01.wav …
say-ja --list                                   # 声の一覧
say-ja --check vo/*.wav                         # ★書き起こして照合（必須）
```

`lines.json`: `[["01","一文目。二文目。"], ["02","次のカット。"]]`

## エンジンは2つある（自動で切り替わる）

| | **MioTTS（既定）** | Irodori（フォールバック） |
|---|---|---|
| 場所 | RTX3090 `100.117.137.5:8021` | この Mac |
| 速度 | **実時間の7〜8倍**（28秒を3〜4秒） | 等速（3.5秒を約5秒） |
| 声 | `jp_female` `jp_male` `en_female` `en_male` | `female` `male` |
| **声の複製** | **できる（`--ref`）** | できない |
| 出力 | 44.1kHz モノラル | 48kHz |
| 必要なもの | tailnet ＋ 3090 が起動していること | 何も要らない |

`say-ja` は MioTTS の生存を確認し、届かなければ Mac 側に切り替えて「切り替えます」と告げる。
**普段はエンジンを意識しなくてよい。** 明示するなら `--engine mio` / `--engine local`。

## 声を複製する（MioTTS だけ）

```bash
ffmpeg -i 元音声.wav -ac 1 -ss 5 -t 15 見本.wav   # モノラルで10〜15秒を切り出す
say-ja --ref 見本.wav "読ませたい文章" -o out.wav
```

- サーバ側で自動リサンプル・モノラル化されるので、形式は気にしなくてよい
- ⚠ **見本は10〜15秒が安全圏。長すぎると末尾が壊れる**（39秒の見本で最後の一文が
  2回繰り返される不具合が出ている）
- `--temp` で印象が変わる。**0.4 が落ち着いた既定**、0.7 が標準、1.0 は抑揚が強く幼い

## ★台本のルール（守らないと読み間違える）

書く前に必ず適用する。**モデルの設定では直らない。原稿を直す。**

- **アルファベットの略語はカタカナに開く。** `HTML` → `エイチティーエムエル`、
  `AI` → `エーアイ`、`3D` → `スリーディー`
- **固有名詞・地名も読み違える。** 不安ならかなに開く
- **締めの一文を短くしない。** 短いと末尾に幻聴（原稿に無い発話）が出る
- **言い換えの効く熟語は平易な語に。** 「原価」が「玄関」と読まれた実例がある
- **ゆっくり／囁くといった指定は書かない。** 文節がまるごと脱落することがある

## 通過条件（満たすまで「できました」と言わない）

1. **`say-ja --check` を実行した。** 生成しただけで終わらせない
2. 書き起こしと原稿を突き合わせ、**別の語に化けていない**
3. **原稿に無い発話（幻聴）が無い**
4. **文節がまるごと消えていない**

⚠ 句読点の有無や同音の漢字違いは問題ない。**読みが同じなら正しく喋れている。**
直すのは、化けている・増えている・消えている、の3つだけ。

## MioTTS が落ちているとき

⚠ **MioTTS は systemd 化されていないので、3090 を再起動すると消える。**
`say-ja` は自動で Mac 側に落ちるので作業は止まらないが、速度と声の複製は使えなくなる。

**エージェントが勝手に起こさない。人に頼む。** 3090 は本番の推論エンジンと同居していて、
起動の順序を誤ると本番側を巻き込む。伝える内容:

```
MioTTS(3090) が落ちています。起こしてください:
  ssh llm@100.117.137.5
  docker start miotts-llama
  cd ~/MioTTS-Inference && MIOTTS_PORT=8021 setsid nohup ~/.local/bin/uv run python run_server.py \
    --llm-base-url http://127.0.0.1:8022/v1 --llm-model Aratako/MioTTS-GGUF \
    --port 8021 --device cuda < /dev/null > ~/miotts_codec.log 2>&1 &
```

手順の詳細は Obsidian のナレッジ「MioTTS音声合成_tailnet経由の使い方」。

## つまずきどころ

- ⚠ **`python3 tools/tts.py` を直接叩かない。** システムの python では
  `AttributeError: module 'mlx.core' has no attribute 'float32'` で落ちる。必ず `say-ja` を呼ぶ
- ⚠ **MioTTS は Mac では動かない。** CUDA 前提の実装なので、必ず3090側
- ⚠ **OpenAI互換の `/v1/audio/speech`（:8014）は localhost 固定**で外から叩けない。
  tailnet からはネイティブAPI（:8021 `/v1/tts`）を使う
- ⚠ **oMLX（127.0.0.1:3005）の Irodori は読み込みに失敗する**
  （`Received 516 parameters not in model: ...wk_caption...`）。使わない
- ⚠ **NAS（SMB）上のパスに直接書き出せない。** ローカルに出してから移す

## 動画に載せるとき

HyperFrames のパイプラインは `~/dev/hyperframes-test/README.md`。
音量バランス・ダッキング・フェードは `hyperframes-audio` の担当で、このスキルの範囲外。
