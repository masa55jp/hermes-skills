---
name: japanese-narration
description: "日本語のナレーション音声を手元のMacで作る（Irodori-TTS v4.1 Small / MLX / 無料・オフライン）。動画のナレーション、読み上げ、ボイスオーバー、「喋らせて」「音声にして」と言われたときに使う。声は女性・男性の2種類から選ぶ。★読み間違いは聞かないと気づけないので、生成したら必ず書き起こしで照合する工程まで含める。"
version: 1.0.0
author: dtn / Hermes Agent
license: MIT
platforms: [macos]
dependencies:
  - say-ja（~/.local/bin/say-ja。内部で ~/.venvs/hf-mlx-audio と ~/dev/hyperframes-test/tools を使う）
metadata:
  hermes:
    tags: [tts, 音声, ナレーション, 日本語, mlx, irodori, オフライン]
    related_skills: [media-use, hyperframes-audio]
---

# 日本語ナレーションを作る

手元の Mac だけで日本語の音声を作る。**クラウドAPIを使わない。無料。オフラインで動く。**
モデルは Irodori-TTS v4.1 Small（MLX 8bit）。日本語の読み精度で他のローカルTTSより良い。

## 使い方

```bash
say-ja "読み上げる文章です。" -o out.wav        # 1本
say-ja --voice male "文章です。" -o out.wav      # 男性の声
say-ja --lines lines.json --out vo/             # まとめて → vo/01.wav, vo/02.wav …
say-ja --list                                   # 声の一覧
say-ja --check vo/*.wav                         # ★書き起こして照合（必須）
```

`lines.json` の形式:

```json
[["01","一文目。二文目。"], ["02","次のカット。"]]
```

## 声

| | |
|---|---|
| `female`（既定） | 20代前半の女性。ショート動画向け。明るく歯切れよく早口 |
| `male` | テック系YouTuber風の25歳男性。滑舌がよく、少し前のめり |

声は参照音声で固定されるので、同じ声で何本作っても揺れない。

## ★台本のルール（守らないと読み間違える）

これを守らないと事故る。**書く前に必ず適用すること。**

- **アルファベットの略語はカタカナに開く。** `HTML` → `エイチティーエムエル`、
  `AI` → `エーアイ`、`3D` → `スリーディー`
- **固有名詞・地名も読み違える。** 不安ならかなに開く
- **締めの一文を短くしない。** 短いと末尾に幻聴（原稿に無い発話）が出る
- **言い換えの効く熟語は平易な語に。** 「原価」が「玄関」と読まれた実例がある
- **ゆっくり／囁くといった指定は書かない。** 文節がまるごと脱落することがある

## 通過条件（満たすまで「できました」と言わない）

1. **`say-ja --check` を実行した。** 生成しただけで終わらせない
2. 書き起こしと原稿を突き合わせ、**別の語に化けていない**ことを確認した
3. **原稿に無い発話（幻聴）が無い**ことを確認した
4. **文節がまるごと消えていない**ことを確認した

⚠ 句読点の有無や同音の漢字違いは問題ない。**読みが同じなら正しく喋れている。**
直すのは、化けている・増えている・消えている、の3つだけ。

読み間違いが出たら、**台本のルールに従って原稿を書き直してから作り直す。**
モデルの設定では直らない。

## 実測（M1 Max 64GB）

| | |
|---|---|
| 生成速度 | 3.5秒の音声を約5秒（ほぼ実時間） |
| ピークメモリ | 4.7GB |
| 出力 | 48kHz WAV |

## つまずきどころ

- ⚠ **`python3 tools/tts.py` を直接叩かない。** システムの python では
  `AttributeError: module 'mlx.core' has no attribute 'float32'` で落ちる。
  `say-ja` は内部で専用の venv を使うので、必ず `say-ja` を呼ぶ
- ⚠ **oMLX（127.0.0.1:3005）の `/v1/audio/speech` は使えない。**
  モデル一覧に Irodori はあるが、読み込みに失敗する
  （`Received 516 parameters not in model: ...wk_caption...` ＝ 参照音声のキャプション層に未対応）
- ⚠ **NAS（SMB）上のパスに直接書き出せない。** `--check` は内部でローカルにコピーして回避している。
  生成先もローカルにして、あとから移すのが安全

## 動画に載せるとき

HyperFrames のパイプラインで使う場合は `~/dev/hyperframes-test/README.md` を読む。
音量バランス・ダッキング・フェードは `hyperframes-audio` の担当で、このスキルの範囲外。
