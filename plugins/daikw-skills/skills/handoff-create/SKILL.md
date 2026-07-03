---
name: handoff-create
description: "セッション引き継ぎ用の HANDOFF.md を生成する。コンテキストが大きくなったとき、作業を中断するとき、別のエージェントに引き継ぐときに使う。`$ARGUMENTS` に `quick` を渡すと Goal/Done/Next/State のみの最小版になる（省略時はフル項目）。既存の HANDOFF.md を読んで再開したいだけなら使わない（`handoff-resume` を使う）。キーワード: handoff, 引き継ぎ, セッション終了, コンテキスト引き継ぎ, quick handoff, 簡易引き継ぎ"
disable-model-invocation: false
user-invocable: true
argument-hint: "[quick でモード切替、出力先パス指定も可 (省略時: フル項目 / ./HANDOFF.md)]"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
---

# Handoff Create - 引き継ぎドキュメント生成

現在のセッションの作業状態を HANDOFF.md として書き出す。
次のセッションや別のエージェント（Claude Code / Codex / 人間）が「読むだけで再開できる」ことを目指す。

## モードと出力先

`$ARGUMENTS` を解釈する:

- 先頭トークンが `quick` → **quick モード**（下記の最小テンプレート）。残りは出力先パスとして扱う
- それ以外（省略含む） → **full モード**（デフォルト、下記のフルテンプレート）。`$ARGUMENTS` 全体を出力先パスとして扱う
- 出力先パス省略時は `./HANDOFF.md`

**モードの目安**: 変更ファイル数が数個・意思決定も単純なら quick で十分。複数の意思決定・Failed Approaches・他エージェントへの正式な引き継ぎが要るなら full を使う。

## 手順

### 1. コンテキスト収集

**quick モード**は最低限のみ:
- `git status --short` と `git branch --show-current`
- 現在のタスクリスト（あれば）

**full モード**は以下を自動的に調べる（すべて必須ではない。該当するものだけ集める）:

- **Git 状態**: `git status`, `git diff --stat`, `git log --oneline -10`, 現在のブランチ
- **変更ファイル一覧**: 未コミットの変更、新規ファイル
- **TodoWrite の状態**: 現在のタスクリスト（あれば）
- **エラー/失敗**: 直近で失敗したコマンドやテスト結果
- **環境**: 使用中のランタイム/フレームワークのバージョン

### 2. HANDOFF.md を生成

**quick モードのテンプレート**:

```markdown
# HANDOFF (Quick)

_Generated: {datetime}_

## Goal

一言で目的。

## Done

- 完了した作業（箇条書き）

## Next

- 次にやるべきこと（箇条書き、優先度順）

## State

- Branch: `{branch}`
- Uncommitted: yes/no
- Build: pass/fail
- Notes: 一言メモ
```

**full モードのテンプレート**: 以下のテンプレートに沿って書く。セクションが不要な場合は省略してよい。

```markdown
# HANDOFF

_Generated: {datetime}_
_Session: ${CLAUDE_SESSION_ID}_

## Goal

このセッションの目的を1-3行で。

## Completed

- [x] 完了した作業をリストアップ
- [x] 具体的に何をしたか（ファイル名・関数名を含む）

## Not Yet Done

- [ ] 未完了の作業
- [ ] 優先度順に並べる

## Failed Approaches

> 次のエージェントが同じ失敗を繰り返さないための記録。

- **やったこと**: 何を試したか
  - **結果**: なぜ失敗したか
  - **教訓**: 次に試すべきこと / 避けるべきこと

## Key Decisions

| 意思決定 | 選択肢 | 理由 |
|----------|--------|------|
| 例: ORM選定 | Drizzle | 型安全 + 軽量、Prisma は重すぎた |

## Current State

- **動作状況**: ビルドが通る / テストが通る / エラーがある
- **ブランチ**: `{branch_name}`
- **未コミット変更**: あり / なし
- **既知のエラー**:
  ```
  エラーメッセージがあればここに
  ```

## Code Context

次のエージェントがすぐ使えるよう、重要なシグネチャやパスを記載。

- **エントリポイント**: `src/index.ts`
- **主要な型/インターフェース**:
  ```typescript
  // 例: 重要な型定義をコピペ
  ```
- **API レスポンス例**:
  ```json
  // 例: 外部APIのレスポンス形式
  ```

## Resume Instructions

1. このファイルを読む
2. `{具体的な再開コマンド}`
3. 期待結果: `{何が起これば正常}`

## Setup Required

- [ ] 必要な環境変数: `FOO_API_KEY`
- [ ] 依存インストール: `npm install`
- [ ] その他の前提条件

## Warnings

- 注意すべき罠やハマりポイント
```

### 3. 出力後の確認

生成した HANDOFF.md の行数と主要セクションを報告する。

## auto-memory との違い

`~/.claude/projects/*/memory/` の auto-memory は Claude Code が暗黙に生成・参照する恒久知識で、他ハーネスや他人には渡せない。HANDOFF.md は明示的に生成し、git commit されてリポジトリと一緒に可搬な「特定タスクの状態スナップショット」である。恒常的な知見は auto-memory、今回の作業の引き継ぎは HANDOFF.md、という役割分担で使う。
