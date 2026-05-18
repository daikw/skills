---
name: commit-push
description: "jj または git リポジトリでコミットとプッシュを行う。VCS を自動判定して適切なコマンドを実行する。キーワード: commit, push, コミット, プッシュ, jj, git"
user-invocable: true
disable-model-invocation: true
argument-hint: "[コミットメッセージ (省略時は diff を見て自動生成)]"
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Commit & Push Skill

jj または git リポジトリを自動判定してコミット・プッシュを行う。

## When to Use

- `/commit-push` で呼び出されたとき
- コミットとプッシュをまとめてやりたいとき

## 手順

### 1. VCS の判定

```bash
# jj リポジトリかどうか確認
jj root 2>/dev/null && echo "jj" || echo "git"
```

- `jj root` が成功 → **jj モード**
- 失敗 → **git モード**

### 2. 変更内容の確認

**jj の場合:**
```bash
jj status
jj diff
```

**git の場合:**
```bash
git status
git diff HEAD
```

変更がなければ「コミットする変更がないのだ」と報告して終了する。

### 3. コミットメッセージの決定

- `$ARGUMENTS` が指定されていればそれをメッセージとして使う
- 省略時は diff を読んで Conventional Commits 形式で自動生成する

**Conventional Commits 形式:**
```
<type>: <description>

<optional body>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

### 4. コミット実行

**jj の場合:**
```bash
# ワーキングコピーをコミット
jj commit -m "<message>"
```

**git の場合:**
```bash
# 全変更をステージして
git add -A
# コミット
git commit -m "<message>"
```

### 5. プッシュ先の確認

**git の場合のブランチチェック:**
```bash
git branch --show-current
```

- `main` または `master` ブランチにいる場合 → **ユーザーに確認を求める**（直接プッシュ禁止）
- feature ブランチの場合 → そのままプッシュ

### 6. プッシュ実行

**jj の場合:**
```bash
# 現在のブックマークをプッシュ（なければ作成を提案）
jj git push
```

jj でブックマークがない場合:
```bash
# ブランチ名を提案してブックマーク作成
jj bookmark create <suggested-name>
jj git push -b <suggested-name>
```

**git の場合:**
```bash
# 上流ブランチがあればそのまま、なければ -u で設定
git push
# 上流未設定の場合
git push -u origin <branch-name>
```

### 7. 完了報告

コミットハッシュ（または jj の change ID）とプッシュ先 URL を報告する。

## ルール

- main/master への直接プッシュはユーザー確認が必須
- コミットメッセージは必ず Conventional Commits 形式にする
- jj の場合、空のワーキングコピー（変更なし）はスキップする
