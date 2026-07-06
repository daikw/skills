---
name: x-search
description: "xAI x_search Agent Tool で X (Twitter) を検索する CLI。キーワード/ハッシュタグ/特定ユーザの最近の投稿を取得。grok-4.3 経由。キーワード: x, twitter, ツイート, 投稿検索, xAI, grok, X 検索, X で調べる"
---

# /x-search - X (Twitter) ローカル検索

`x-search` CLI で xAI Live Search を叩く。KB ingestion / 調査タスク補助用。
MCP は提供しない (tool list 肥大化を避ける progressive disclosure 設計)。

## 前提

このスキルの起動時、Claude Code はコンテキスト冒頭に `Base directory for this skill: <path>` という行を必ず注入する。以下の `$SKILL_DIR` はその行が示す実際のパスに読み替えること（インストール経路によって変わるため、固定パスを決め打ちしない）。

- CLI 本体: `$SKILL_DIR/scripts/x-search`（PEP 723 単一ファイル、`uv run --script` で実行）
- 初回セットアップ: `cp "$SKILL_DIR/scripts/x-search" ~/.local/bin/ && chmod +x ~/.local/bin/x-search`（`~/.local/bin` が PATH 上にあること）。導入済みならこのステップは不要、`x-search` コマンドをそのまま使う
- 任意: `XAI_MODEL` で利用モデルを上書き (default は `grok-4.3`)

CLI の実装と credential 解決方式は CLI 側に閉じる。詳細は `$SKILL_DIR/scripts/README.md`。このスキル本体は
「呼び方とコマンド体系」のみを扱う。

## よく使うコマンド

| 用途 | コマンド |
|---|---|
| キーワード検索 | `x-search search "<query>" -n 10` |
| 言語フィルタ | `x-search search "<query>" -n 10 --language ja` |
| 日付範囲指定 | `x-search search "<query>" --from-date 2026-05-01 --to-date 2026-05-18` |
| JSON 出力 | `x-search search "<query>" --format json` |
| 特定ユーザの最近投稿 | `x-search user @<username> -n 10` |
| ユーザ + 話題フィルタ | `x-search user @<username> --filter "AI"` |

`-n` (= `--limit`) は 1〜30 の範囲。default は 10。

## 課金注意 (2026-05 時点)

xAI の課金は **token + server-side tool** の独立 2 軸。1 search の概算:

- input/output token (grok-4.3): $1.25 / $2.50 per 1M
- x_search tool fee: **$5 / 1K calls = $0.005/call**
- 1 query で 1〜3 円程度、複雑クエリ (内部で複数 search call 発火) なら 3〜6 円

月 200 検索程度までなら現方式 (都度課金) が経済的。それ以上は Grok サブスク併設も検討。

## 既知の挙動

- `x_get_trending` は **未提供** (xAI x_search tool は Trending API を持たないため。`x-search search "<topic> trending"` で代替可)
- 検索結果は Grok が markdown 整形した自然文。raw post array が欲しい場合は `--format json`

## 参考

- xAI docs: https://docs.x.ai/developers/tools/x-search
