---
name: codex
description: "Codex CLI を任意プロンプトで直接呼び出すセカンドオピニオン用 Skill。進捗を stdout でリアルタイム観察。定型レビューは codex-plugin-cc の /codex:review, /codex:adversarial-review, /codex:rescue を使う。キーワード: codex, openai, セカンドオピニオン, コードレビュー, マルチモデル"
---

# Codex Skill

`codex exec` コマンドを直接実行し、進捗をリアルタイムで観察しながら Codex CLI に作業を依頼する。

## When to Use

- Claude Code とは異なるモデルの視点でコードを分析したいとき（セカンドオピニオン）
- **任意プロンプト**で Codex を叩きたいとき（観点指定・設計仮説の検証など）
- read-only で安全に調査したいとき
- 進捗を Claude がリアルタイムで stdout から観察したいとき

## When NOT to Use（codex-plugin-cc を使う）

`openai/codex-plugin-cc` plugin と併用しているので、用途で使い分ける:

| やりたいこと | 使うもの |
|---|---|
| 任意プロンプトでセカンドオピニオン | **この Skill (`/codex`)** |
| 標準的な差分レビュー (git diff ベース) | `/codex:review` |
| 設計判断の pressure-test (adversarial) | `/codex:adversarial-review` |
| 長めの調査・修正委譲、resume/background 管理 | `/codex:rescue` |
| ジョブ状態確認 | `/codex:status` / `/codex:result` / `/codex:cancel` |

> **注意:** `/codex:rescue` は write-capable がデフォルト。read-only セカンドオピニオン目的なら、この Skill を使う方が安全。

## 前提条件

`codex` コマンドが PATH にあり、認証済みであること。

## 実行手順

### 1. プロジェクトディレクトリの特定

`--cd` に渡すディレクトリを決める（不明な場合は `git rev-parse --show-toplevel`）。

### 2. コマンド実行

プロンプト末尾には必ず以下を付ける:
> 確認や質問は不要です。具体的な提案・修正案・コード例まで自主的に出力してください。

```bash
# 読み取り専用（デフォルト）
codex exec --full-auto --sandbox read-only --cd "<project_directory>" \
  "<タスク>。確認や質問は不要です。具体的な提案・修正案・コード例まで自主的に出力してください。"

# ファイル変更を伴う場合
codex exec --full-auto --sandbox workspace-write --cd "<project_directory>" \
  "<タスク>。確認や質問は不要です。具体的な修正を実施してください。"
```

> **Note:** git リポジトリ外のディレクトリで実行する場合は `--skip-git-repo-check` を追加する。
