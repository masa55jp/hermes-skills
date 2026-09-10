# hermes-skills

[Hermes Agent](https://github.com/) / Claude Code 向けに書いた自作スキル。
どちらも「AIにいきなり作らせない」ための道具で、手を動かす前に通す工程を1つ足す。

| スキル | 何をするか |
|---|---|
| [`game-design/game-design-doc`](game-design/game-design-doc/SKILL.md) | ゲームを作る依頼を受けたら、コードを1行も書く前に企画書を通す。面白さの核を一文で言い切らせ、各段階に通過条件を置いて、満たすまで先へ進ませない |
| [`creative/svg-character-design`](creative/svg-character-design/SKILL.md) | ゲーム用キャラクターを手書きSVGで描く。シルエット → レイヤー構成 → 描画 → ラスタライズして自己批評 → 修正（最大3周） |

## 入れ方

```bash
git clone https://github.com/<user>/hermes-skills.git
cd hermes-skills && ./install.sh
```

`~/.hermes/skills/` の該当フォルダだけを同期する。`creative/` には他人が作ったスキルも
同居するので、カテゴリごと上書きはしない。別の場所に入れるなら `HERMES_SKILLS_DIR` を指定する。

## svg-character-design が必要とするもの

ラスタライザが1つ要る。macOS なら:

```bash
brew install resvg librsvg
```

`resvg` が主力で、`librsvg` は2本目。`--compare` を付けると両方で描いて並べ、
食い違ったピクセルの割合を出す。ゲームに載せるSVGは自分の手元にないレンダラで描かれるので、
1つのエンジンで見て満足すると刺さる。

どちらも無い環境では macOS 標準の `qlmanage` と headless Chrome に落ちる。ただしこの2つは
**不透明な白背景に焼き込む**ため、シルエット確認と透明PNGの書き出しが壊れる。非常用と考える。

## なぜこの2つなのか

どちらも同じ失敗に対する手当て。LLMにゲームやキャラクターを作らせると、
**計画を飛ばしていきなり出力する**。結果、機能の寄せ集めになったり、
浮いた手足と濁った色のSVGになったりする。

そこで両方のスキルとも、工程を分けて各段階に**通過条件**を置いた。
条件を満たさないものを「完成」と呼ばせない。判断は人間に残す。

## 出典（game-design-doc）

カプコンが学生向けコンペ「CAPCOM GAMES COMPETITION 2027」の応募者に向けて公開した
[「ゲーム企画書の作り方」](https://www.capcom-games.com/cgc2027/ja-jp/game-design-document/)
の4ステップ構成を下敷きにしている。原文はスライド画像内のテキストで ©CAPCOM。
このスキルは要点と判定基準を自分の言葉で書き直したもの。

## ライセンス

MIT（[LICENSE](LICENSE)）
