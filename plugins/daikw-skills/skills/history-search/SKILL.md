---
name: history-search
description: "全プロジェクトの Claude Code 会話履歴を横断検索する。過去のトピックを調べたいとき、/resume したいがディレクトリを忘れたときに使う。キーワード: 履歴検索, history, resume, 過去の会話"
---

# history-search - Claude Code 履歴横断検索

全プロジェクトの Claude Code 会話履歴を横断して検索するスキル。

## When to Use

- どのプロジェクトで特定のトピックを調べたか思い出せないとき
- 過去の会話を横断的に検索したいとき
- `/resume` したいがディレクトリを忘れたとき

## 履歴の保存場所

```
~/.claude/projects/<プロジェクトパス>/   # ディレクトリ名は実パスの / を - に置換
    <session-uuid>.jsonl                 # 1ファイル = 1会話
~/.claude/history.jsonl                  # グローバル履歴
```

## 検索コマンド

### マッチしたプロジェクト名だけ表示（基本）

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u
```

### ファイルパスまで表示

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl"
```

### プロジェクト名を実パスに変換して表示

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u \
  | sed 's|^-||; s|-|/|g'
```

> ディレクトリ名の先頭の `-` を除去し、残りの `-` を `/` に戻す。

## /resume へのつなぎ方

検索で見つかったプロジェクトのディレクトリで Claude Code を起動し、`/resume` すれば続きから再開できる。

```bash
# 例: $HOME/<your-project> で再開
cd $HOME/<your-project> && claude
# → /resume
```
