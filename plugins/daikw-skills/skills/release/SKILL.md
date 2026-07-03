---
name: release
description: "GitHub リリースを作成する。過去リリースのスタイルを踏襲し、コミット履歴からリリースノートを自動生成する。バージョン番号はユーザーが指定する前提で、自動算出は行わない。単純に `gh release create` を素で叩くだけで足りるなら使わない。キーワード: release, リリース, タグ"
user-invocable: true
argument-hint: "[バージョンタグ (省略時: ユーザーに確認する)]"
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
---

# Release - GitHub リリース作成

GitHub リリースをコミット履歴ベースで作成する。

## バージョン決定

`$ARGUMENTS` が指定されていればそれをタグとして使う。実運用ではユーザーが常にバージョン番号（メジャー/マイナーの区別を含む）を明示指定しており、自動算出ロジックが使われた実績はない。

省略時は自動算出せず、`gh release list --limit 3` で直近のタグを提示したうえで、どのバージョンにするかユーザーに一言確認する。

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
