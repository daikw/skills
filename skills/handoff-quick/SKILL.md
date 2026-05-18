---
name: handoff-quick
description: "最小限の引き継ぎメモを HANDOFF.md として生成する。サクッと中断して後で戻りたいときに使う。キーワード: quick handoff, 簡易引き継ぎ, メモ"
disable-model-invocation: true
user-invocable: true
argument-hint: "[出力先パス (省略時: ./HANDOFF.md)]"
allowed-tools:
  - Read
  - Write
  - Bash
---

# Handoff Quick - 最小版引き継ぎメモ

`handoff-create` の簡易版。最低限の情報だけ素早く書き出す。

## 出力先

`$ARGUMENTS` が指定されていれば、そのパスに出力する。
省略時は `./HANDOFF.md` に出力する。

## 手順

### 1. 最低限の情報収集

- `git status --short` と `git branch --show-current`
- 現在のタスクリスト（あれば）

### 2. HANDOFF.md を生成

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

### 3. 完了報告

ファイルパスだけ報告する。
