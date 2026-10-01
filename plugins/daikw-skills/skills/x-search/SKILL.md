---
name: x-search
description: "X (Twitter) の投稿を、キーワード・期間・投稿者から x-search CLI で検索する。X の投稿調査に使う。一般的なWeb検索やxAIモデルの設定・導入には使わない。"
---

# /x-search - X (Twitter) ローカル検索

`x-search` CLI で xAI Live Search を呼び出す。KB への情報収集や調査を補助する。
MCP は提供しない (tool list 肥大化を避ける progressive disclosure 設計)。

## 利用する CLI

現在インストール済みの `x-search` を使う。実装と認証情報の取得は CLI に任せ、秘密値を表示しない。
モデルが指定されている場合は、その設定と結果の確認可能なモデル情報を照合する。別モデルへの変更を推定しない。

CLI が見つからない場合は導入不足として報告する。同梱の PEP 723 script は依存の範囲指定を含むため、単にコピーして実行しない。
新規導入では依存を固定・検証する既存の環境を確認し、供給元と実行する内容をレビューする必要がある。
技能の利用依頼だけからインストール方式・課金サービス・認証の変更を追加しない。

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

## 検索範囲と費用

依頼から検索語・期間・投稿者・必要件数を決める。最新の料金や利用上限が判断に必要なら公式情報を確認する。
過去の料金から現在の費用やサブスクリプションの優劣を断定しない。無条件に検索を再送しない。

## 既知の挙動

- `x_get_trending` は **未提供** (xAI x_search tool は Trending API を持たないため。`x-search search "<topic> trending"` で代替可)
- 検索結果はモデルが生成・整形した内容。`--format json` もモデルへJSON形式を要求するもので、構造を保証するraw post APIではない。JSONはparseし、引用元・投稿URL・日付を照合して使う

## 参考

- xAI docs: https://docs.x.ai/developers/tools/x-search
