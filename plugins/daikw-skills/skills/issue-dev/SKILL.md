---
name: issue-dev
description: "Fetches GitHub or GitLab issues and drives full implementation using swarm-dev. Use when the user says things like 'チケット取得して開発して', 'Issue #XX を対応して', '#XX 実装して', 'このチケット対応して', or 'オープンなIssueを順に処理して'. Also triggers when a GitHub/GitLab issue URL is pasted alongside a development request."
---

# issue-dev

GitHub / GitLab の Issue を取得し、`/swarm-dev` チームで実装して PR を作成するまでを一貫して行う。
可能な限り自律して取り組み、ユーザーの介入を最小限に抑える。

**Freedom Level: 中** — フロー順序は守りつつ、Issue の内容・プロジェクト構成に応じてチーム編成を調整する。

---

## フロー

### Step 1: Issue を取得する

**番号・URLが渡された場合:**
```bash
# GitHub
gh issue view <N> --json title,body,labels,assignees,comments

# GitLab
glab issue view <N>
```

**何も渡されなかった場合:**
```bash
# GitHub: オープンIssueを優先度ラベル付きで取得
gh issue list --state open --json number,title,labels,assignees | head -20

# GitLab
glab issue list --state opened
```
→ ラベル・タイトルから CRITICAL / HIGH / MEDIUM で優先度を判断し、処理順を決める。

---

### Step 2: 解釈を確認する（重要）

Issue の内容を読んだあと、もし曖昧な点があれば、以下を確認する。

```
Issue #XX「<タイトル>」の解釈を確認します。

【理解した内容】
- <実装すること>
- <変更対象のファイル・モジュール>
- <完了条件>

【不明点・前提確認】
- <あれば記載>

この解釈で進めてよいですか？
```

解釈のズレがあれば修正して再確認し、曖昧さが十分解消されたと感じたら Step 3 へ進む。

---

### Step 3: /swarm-dev で実装

確認が取れたら `/swarm-dev` を呼び出し、チームを編成して並列実装する。

`/swarm-dev` に渡すコンテキスト:
- Issue番号・タイトル・本文
- 確認済みの解釈・完了条件
- 追加要件（ユーザーが補足した場合）
- **ブラウザ検証フラグ**:

```yaml
browser_validation_requested: required | skip | auto
browser_validation_reason: <理由>
browser_validation_scope: per_issue | batch
```

#### ブラウザ検証フラグの決定ルール

| ユーザーの発言                                     | 値       |
| -------------------------------------------------- | -------- |
| 「ブラウザ確認して」「Chromeで見て」「UI確認必須」 | required |
| 「バックエンドだけ」「ブラウザ確認不要」           | skip     |
| それ以外（デフォルト）                             | auto     |

- Issue 文面からの推定で `required` に寄せない（誤爆防止）
- Issue に UI/UX 関連のヒントがあれば `reason` に記載するのみ
- `scope` のデフォルトは `per_issue`

---

### Step 4: PR 作成・報告

実装完了後（swarm-dev の Phase 5 で PR が作成される）:

- PR URL をユーザーに報告
- PR body には Browser Test Summary が含まれていることを確認
- `pr_ready: no` で swarm-dev が停止した場合、ブロック理由をユーザーに報告し判断を仰ぐ

---

## 複数 Issue の処理

「順に処理して」と言われた場合は、優先度判断後に **1件ずつ** Step 2〜4 を繰り返す。
並列実装は swarm-dev 内部で行う。Issue間の依存関係がある場合は直列処理する。

ブラウザ検証は原則 **Issue ごと**（`per_issue`）。同一ブランチで密結合な複数 Issue をまとめる場合のみ `batch` を指定。

---

## プラットフォーム判定

| 条件                         | コマンド          |
| ---------------------------- | ----------------- |
| `gh` が使える / GitHub URL   | `gh issue view`   |
| `glab` が使える / GitLab URL | `glab issue view` |
| `GITLAB_URL` 環境変数あり    | GitLab として扱う |
| 判別できない                 | ユーザーに確認    |

---

## よくある補足パターン

ユーザーが Issue 番号と一緒に追加要件を渡すケースがある:

```
#68 を対応して。ただし GCP 前提で実装すること
```

この場合、追加要件は解釈確認（Step 2）に含めて提示し、swarm-dev に確実に引き継ぐ。
ブラウザ検証に関する指示があれば `browser_validation_requested` に反映する。
