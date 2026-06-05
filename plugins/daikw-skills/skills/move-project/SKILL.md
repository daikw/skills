---
name: move-project
description: "プロジェクトディレクトリを移動・リネームしたとき、Claude Code と Codex CLI の会話履歴を新しいパスに追跡させる。キーワード: ディレクトリ移動, リネーム, 履歴追跡, プロジェクト移動, move, rename"
---

# move-project - 履歴のディレクトリ移動追跡（Claude Code & Codex）

プロジェクトディレクトリを移動・リネームした後、Claude Code と Codex CLI の会話履歴を新しいパスに紐付け直すスキル。

## When to Use

- `mv ~/old-name ~/new-name` などでプロジェクトディレクトリをリネームした
- プロジェクトを別の場所に移動した
- 移動後に `claude` や `codex resume` を起動したら履歴が見えなくなった

## スクリプト

```
~/.claude/skills/move-project/
├── migrate-claude.sh   ← Claude Code 履歴の移行
├── migrate-codex.sh    ← Codex CLI セッションの移行
└── SKILL.md
```

## 手順

### 0. まず移行が必要かチェック（--check）

```bash
# 何が変わるかを確認する（ファイルは変更しない）
bash ~/.claude/skills/move-project/migrate-claude.sh --check /old/path /new/path
bash ~/.claude/skills/move-project/migrate-codex.sh  --check /old/path /new/path
```

### 1. プロジェクトディレクトリを移動（未実施の場合）

```bash
mv /old/path/to/project /new/path/to/project
```

### 2. Claude Code 履歴を移行

```bash
bash ~/.claude/skills/move-project/migrate-claude.sh /old/path/to/project /new/path/to/project
```

### 3. Codex セッションを移行

```bash
bash ~/.claude/skills/move-project/migrate-codex.sh /old/path/to/project /new/path/to/project
```

### 4. 確認

```bash
# Claude Code
cd /new/path/to/project && claude
# → /resume で履歴が表示されるか確認

# Codex
cd /new/path/to/project && codex resume
# → 旧プロジェクトのセッションが表示されるか確認
```

---

## ツールの仕組みの違い

| | Claude Code | Codex CLI |
|---|---|---|
| **保存場所** | `~/.claude/projects/{key}/` | `~/.codex/sessions/YYYY/MM/DD/` |
| **ディレクトリ命名** | cwd の `/` と `.` を `-` に変換 | 日付ベース（プロジェクト無関係） |
| **セッション検索** | ディレクトリ名でフィルタ | `session_meta.payload.cwd` をスキャン |
| **移行で必要な作業** | ディレクトリ mv + 内部パス置換 | 内部 cwd 置換のみ（dir 移動不要） |

---

## 既知の制限事項

| 制限 | 詳細 |
|---|---|
| `\|` を含むパス非対応 | sed のデリミタ衝突。パス名に `\|` を含む場合は手動対応 |
| macOS 専用 | `sed -i ''` と `stat -f` が macOS 依存。Linux では要変更 |
| Codex の末尾アンカー | セッション内容の自由テキストに旧パスが残る場合がある（resume には影響なし） |
