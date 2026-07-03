---
name: handoff-resume
description: "既存の HANDOFF.md を読み込んで作業を再開する。単に内容を思い出すだけなら Read で十分なので使わない — このスキルの価値は、HANDOFF.md 生成後にリポジトリが変わっていないかの drift 検知と、Not Yet Done/Next セクションの TodoWrite 一括変換にある。前セッションとの間に他の変更が入った可能性がある、または再開後すぐにタスクリストとして動き出したい場合に使う。キーワード: resume, 再開, 引き継ぎ読み込み, 続き"
disable-model-invocation: false
user-invocable: true
argument-hint: "[HANDOFF.md のパス (省略時: ./HANDOFF.md)]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Handoff Resume - 引き継ぎからの再開

既存の HANDOFF.md を読み込み、作業を再開するための準備を行う。

## 入力

`$ARGUMENTS` が指定されていれば、そのパスの HANDOFF.md を読む。
省略時は `./HANDOFF.md` を探す。見つからなければ `**/HANDOFF.md` で検索する。

## 手順

### 1. HANDOFF.md の読み込みと検証

- ファイルを読む
- 必須セクション（Goal, Next/Not Yet Done）が存在するか確認
- 生成日時（`_Generated: {datetime}_`）が **72 時間以上前**の場合は警告する（drift の可能性が高くなる目安。厳密な期限ではないので、対象リポジトリの更新頻度に応じて短く見積もってよい）

### 2. リポジトリの drift チェック

HANDOFF.md 作成後にリポジトリが変わっていないか確認する:

- `git log --oneline` で HANDOFF.md 生成後のコミットを確認
- `git diff --stat` で未コミット変更を確認
- HANDOFF.md に記載のブランチと現在のブランチが一致するか確認

**drift がある場合**: 差分を明示して、ユーザーに「そのまま続行 / HANDOFF.md を更新」を確認する。

### 3. 再開ブリーフィング

以下をまとめて報告する:

```
## 再開ブリーフィング

**目的**: {Goal から}
**完了済み**: {Done/Completed の要約}
**次のタスク**: {Next/Not Yet Done の一覧}
**注意点**: {Warnings, Failed Approaches の要約}
**drift**: {あれば差分の要約}
```

### 4. タスクリスト化

Not Yet Done / Next セクションの内容を TodoWrite でタスクリストに変換する。
その後、最初のタスクから作業を始められる状態にする。

## 注意

- HANDOFF.md の Failed Approaches は必ず確認し、同じ失敗を繰り返さない
- Setup Required がある場合は、再開前に環境を整える
- Resume Instructions がある場合は、その手順に従う

## auto-memory との違い

`~/.claude/projects/*/memory/` の auto-memory は Claude Code が暗黙に生成・参照する恒久知識で、他ハーネスや他人には渡せない。HANDOFF.md は明示的に生成し、git commit されてリポジトリと一緒に可搬な「特定タスクの状態スナップショット」である。両者は競合しない — 恒常的な知見は auto-memory、今回の作業の引き継ぎは HANDOFF.md、という役割分担で使う。
