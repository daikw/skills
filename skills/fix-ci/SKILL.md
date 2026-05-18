---
name: fix-ci
description: GitHub Actions / GitLab CI の失敗を修正するスキル。ログ取得→根本原因分析→修正提案→確認→実施 の多フェーズで安全に対応する。
---

# fix-ci

GitHub Actions / GitLab CI の失敗を修正するスキル。

## When to Use

- `fix-ci`, `CI 直して`, `CI 失敗`, `Actions 失敗`
- `pipeline 失敗`, `GitLab CI 落ちた`, `CI エラー`
- PR URL や Run URL を貼って「直して」と言われた場合

---

## FLOW（実行フロー）

### Phase 1: コンテキスト収集

不明な場合はユーザーに確認する:
- PR番号 または CI Run URL
- リポジトリ（カレントか否か）
- GitHub / GitLab どちらか

```bash
# GitHub の場合
gh run list --limit 5                   # 最近の Run 一覧
gh run view <run-id> --log-failed       # 失敗ログのみ取得
gh pr checks <pr-number>               # PR の checks 状況

# GitLab の場合
glab ci view                            # 最新パイプライン
glab ci trace <job-id>                 # ジョブログ取得
```

### Phase 2: エラー分析

ログから以下を特定する:
1. **失敗 Job / Step 名**
2. **エラーメッセージ**（exit code, 例外, タイムアウト等）
3. **根本原因カテゴリ**（下表）

| カテゴリ | 例 |
|---|---|
| 依存関係 | `npm install` 失敗, パッケージ競合 |
| テスト失敗 | assertion error, snapshot mismatch, timeout |
| Lint / 型エラー | tsc error, eslint violation |
| 権限・シークレット | token expired, env var missing |
| インフラ | runner OOM, disk full, network timeout |
| 設定ミス | YAML 構文エラー, action バージョン不整合 |

### Phase 3: 修正提案（ユーザー確認必須）

修正内容を **diff 形式** で提示してから確認を取る:

```
以下の変更を行います。よいですか？

File: .github/workflows/ci.yml
- node-version: '16'
+ node-version: '20'
```

⚠️ ファイル書き換えはユーザーの明示的な `yes` 後にのみ実行する。

### Phase 4: 修正実施

確認後にファイルを編集する。複数ファイルにまたがる場合は変更順序を明示する。

### Phase 5: 検証（任意）

```bash
# ローカル検証できる場合
act -j <job-name>     # GitHub Actions ローカル実行 (nektos/act)
npx tsc --noEmit      # 型エラーの確認
npm test              # テスト再実行

# Push して再確認
gh run watch          # CI 完了まで監視
glab ci view          # GitLab の場合
```

---

## 出力フォーマット

```
## CI 失敗レポート

**失敗 Job**: build / test
**原因カテゴリ**: テスト失敗
**根本原因**: `test/auth.spec.ts:42` の assertion が失敗

## 修正案

[diff を表示]

修正してよいですか？ (yes/no)
```

---

## 安全ルール

- CI ログに含まれるシークレット・トークン・パスワードは **出力しない**
- `.env` や secrets の内容を読み取らない
- `force push` は提案しない（ユーザーが明示した場合のみ）
- main/master への直接 push は提案せず、PR 経由を推奨する
