---
name: release
description: "GitHub リリースを作成する。過去リリースのスタイルを踏襲し、コミット履歴からリリースノートを自動生成する。キーワード: release, リリース, タグ"
user-invocable: true
argument-hint: "[バージョンタグ (省略時: 最新タグ+0.1)]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Release - GitHub リリース作成

GitHub リリースをコミット履歴ベースで作成する。

## バージョン決定

`$ARGUMENTS` が指定されていればそれをタグとして使う。
省略時は以下のロジックで自動決定:

```bash
# 最新タグを取得し、マイナーバージョンを +1
latest=$(gh release list --limit 1 --json tagName -q '.[0].tagName')
# 例: v0.4 → v0.5, v1.2 → v1.3
```

パースできない場合はユーザーに確認する。

## 手順

### 1. 情報収集（並列実行）

- `gh release list --limit 3` で過去リリースのスタイルを確認
- `gh release view <latest>` で直近リリースの本文フォーマットを確認
- `git fetch --tags` でタグを同期
- `git log <latest-tag>..HEAD --oneline` で含まれるコミットを収集

### 2. リリースノート作成

過去リリースのフォーマットに合わせてリリースノートを構成する。

- コミット内容を意味のある単位でグルーピング
- feat / fix / chore などの prefix から分類
- 末尾に `**Full Changelog**: https://github.com/{owner}/{repo}/compare/{prev}...{new}` を付ける

### 3. リリース対象ブランチの決定

- 現在のブランチをターゲットにする（`--target $(git branch --show-current)`）

### 4. リリース作成

```bash
gh release create <tag> \
  --target <branch> \
  --title "<tag>" \
  --notes "<release-notes>"
```

### 5. 完了報告

作成されたリリースの URL を報告する。
