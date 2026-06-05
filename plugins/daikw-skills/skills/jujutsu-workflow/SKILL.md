---
name: jujutsu-workflow
description: Git互換VCS「jujutsu (jj)」のワークフロー支援。jjでのバージョン管理、コミット操作、Git連携、コンフリクト解決をサポート。
---

# Jujutsu (jj) VCS Workflow Skill

Git互換のバージョン管理システム「jujutsu」を使用したワークフロー支援。

## When to Use
- jujutsuでのバージョン管理作業
- Gitリポジトリでjjを使い始めるとき
- コミット履歴の編集・整理
- コンフリクト解決

## 基本概念

### Working Copy = コミット
jjではWorking copyが自動的にコミットとして扱われる。staging area不要。

### Change ID vs Commit ID
- **Change ID**: 論理的な変更単位（安定、変わらない）
- **Commit ID**: Changeの内部表現（編集で変わる）

### リビジョン記法
- `@` - 現在のワーキングコピー
- `@-` - 親コミット
- `@--` - 2つ前
- `root()` - ルートコミット

## ワークフロー

### 既存Gitリポジトリでjjを開始
```bash
cd your-git-repo
jj git init --colocate
```

### Squash Workflow（推奨）
```bash
# 1. 作業内容を説明
jj describe -m "機能追加: ユーザー認証"

# 2. 新しい空の変更を作成（ここで編集開始）
jj new

# 3. ファイルを編集...

# 4. 変更を親にsquash
jj squash
```

### 複数の変更を並行作業
```bash
# 機能Aの作業
jj describe -m "機能A"
jj new

# 機能Bに切り替え（機能Aの親から分岐）
jj new @-
jj describe -m "機能B"
```

## コマンドリファレンス

### 状態確認
```bash
jj status              # リポジトリ状態
jj log                 # 履歴グラフ
jj log -r @            # 現在のコミットのみ
jj diff                # 変更内容
```

### コミット操作
```bash
jj describe -m "msg"   # メッセージ設定
jj new                 # 新しい変更作成
jj commit -m "msg"     # describe + new
jj squash              # 親にマージ
jj edit <rev>          # 過去のコミットを編集
jj split               # コミット分割
jj abandon <rev>       # コミット廃棄
```

### リベース
```bash
jj rebase -b @ -d main          # 現在のブランチをmainにリベース
jj rebase -s <rev> -d <dest>    # 特定のコミットから移動
```

### コンフリクト解決
```bash
jj status                       # コンフリクト確認
jj resolve                      # 対話的に解決
jj resolve --list               # コンフリクトファイル一覧
```

### Git連携
```bash
jj git fetch                    # リモートからフェッチ
jj git push                     # リモートにプッシュ
jj git push -b <bookmark>       # 特定ブックマークをプッシュ
```

### ブックマーク（≒ Gitブランチ）
```bash
jj bookmark create <name>       # 作成
jj bookmark list                # 一覧
jj bookmark move <name>         # 現在位置に移動
jj bookmark track <name>@origin # リモート追跡
```

### 操作ログ・取り消し
```bash
jj op log                       # 操作履歴
jj undo                         # 最後の操作を取り消し
jj op restore <op-id>           # 特定時点に復元
```

## Tips

### jj log のカスタマイズ
```bash
# シンプル表示
jj log --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'
```

### Git pushの前に
```bash
# ブックマークを作成してからpush
jj bookmark create feature-x
jj git push -b feature-x
```

### コンフリクトをコミットしてから解決
jjはコンフリクト状態でもコミット可能。後で解決できる。

```bash
jj new           # コンフリクト状態でも新しい変更を作成可能
# 後で解決
jj resolve
```

## Gitとの対応表

| Git | jj |
|-----|-----|
| `git status` | `jj status` |
| `git log` | `jj log` |
| `git add + commit` | `jj describe` / `jj commit` |
| `git checkout -b` | `jj new` + `jj bookmark create` |
| `git stash` | 不要（自動コミット） |
| `git rebase -i` | `jj squash` / `jj edit` |
| `git reflog` | `jj op log` |
| `git reset --hard` | `jj undo` |

## References
- 公式ドキュメント: https://docs.jj-vcs.dev/latest/
- チュートリアル: https://jj-vcs.github.io/jj/latest/tutorial/
- Steve's Tutorial: https://steveklabnik.github.io/jujutsu-tutorial/
