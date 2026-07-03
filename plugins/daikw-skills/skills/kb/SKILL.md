---
name: kb
description: "Knowledgebase (daikw/knowledgebase) の inbox に各種ソースから投入するスキル。Web URL / GitHub issue-PR / 手書きメモに対応。キーワード: kb, knowledgebase, ナレッジベース, inbox, ingest, clip, クリップ"
---

# /kb - Knowledgebase Ingestion

`~/ghq/github.com/daikw/knowledgebase/` の `inbox/` に素材を投入するスキル。

Karpathy LLM Wiki パターンの ingest（投入）操作のみを担う。triage / query / lint / compact は実装しておらず、投入後の inbox 整理は手動で行う。

## KB パスの解決

```bash
KB_PATH="${KB_PATH:-$HOME/ghq/github.com/daikw/knowledgebase}"
```

KB が存在しない場合は即エラー終了し、ユーザーに `git clone` を促す。

## サブコマンド一覧

| コマンド | 動作 | 落とし先 |
|---|---|---|
| `/kb` (引数なし) | このヘルプを表示 | — |
| `/kb url <url>` | Web ページを markdown 化して保存 | `inbox/clippings/` |
| `/kb gh <url\|ref>` | GitHub issue/PR/discussion を取得 | `inbox/clippings/` |
| `/kb note <text...>` | ワンライナーのメモを保存 | `inbox/manual/` |

## 共通ルール

### ファイル命名

```
<inbox subdir>/YYYY-MM-DD-<slug>.md
```

- `YYYY-MM-DD`: 今日の日付（`date +%Y-%m-%d`）
- `slug`: タイトルから生成。kebab-case、ASCII、最大 60 文字
- 既存ファイルと衝突したら末尾に `-2`, `-3` ...

### frontmatter

各投入ファイルの先頭に必ず以下を付ける:

```yaml
---
source: <URL or "manual">
source_type: web | github | slack | manual
captured_at: YYYY-MM-DD
title: <元のタイトル>
---
```

### 投入後の処理

1. ファイルを書き込む
2. KB リポジトリで `git add <file> && git commit -m "ingest: <short title>"` を実行
3. push はしない（ユーザーが後でまとめて push）
4. ユーザーに投入先パスを伝える。triage サブコマンドは無いため、inbox の整理は手動で行うよう案内する

---

## `/kb url <url>` — Web ページ投入

### 手順

1. WebFetch で URL を取得し、以下のプロンプトで整形:
   > このページの本文を忠実に markdown に変換してください。広告・ナビゲーション・フッター等の周辺要素は除外。見出し階層・コードブロック・リンクは保持。冒頭に1行要約を `## Summary` セクションで付けてください。
2. ページタイトルから slug を生成
3. frontmatter を付けて `inbox/clippings/YYYY-MM-DD-<slug>.md` に保存
4. git commit

### 出力例

```
✓ saved: inbox/clippings/<date>-<slug>.md (3.2KB)
  source: https://gist.github.com/karpathy/...
  next: triage サブコマンドは無いので、inbox/ の内容は手動で確認・分類すること
```

---

## `/kb gh <url|ref>` — GitHub issue/PR/discussion 投入

### 引数パターン

- URL: `https://github.com/owner/repo/issues/123`
- shorthand: `owner/repo#123`

### 手順

1. URL/ref をパースして `owner/repo` と `type` (issues/pull/discussions) と `number` を抽出
2. `gh` CLI で取得:
   ```bash
   gh issue view <number> --repo <owner/repo> --json title,body,author,state,createdAt,url,labels,comments
   # or: gh pr view, gh api for discussions
   ```
3. タイトル + 本文 + 主要コメント（先頭 5 件）を markdown 化
4. frontmatter に `source: <URL>`, `source_type: github` を付けて `inbox/clippings/` に保存
5. git commit

### discussion は `gh api` 経由

`gh discussion view` は未対応なので `gh api graphql` でフェッチする:

```bash
gh api graphql -f query='query($owner:String!,$repo:String!,$num:Int!){repository(owner:$owner,name:$repo){discussion(number:$num){title body author{login} comments(first:5){nodes{body author{login}}}}}}' \
  -F owner=<owner> -F repo=<repo> -F num=<num>
```

---

## `/kb note <text...>` — 手書きメモ投入

### 手順

1. 引数テキストから slug を生成（最初の単語を数語取る、kebab-case 化）
   - テキストが短い場合は全文を slug に
   - 長い場合は先頭 6 単語まで
2. 本文は渡されたテキストそのまま（Markdown として解釈）
3. frontmatter に `source: "manual"`, `source_type: manual`
4. `inbox/manual/YYYY-MM-DD-<slug>.md` に保存
5. git commit

### 引数が空の場合

ユーザーに「何を記録する？」と 1 行で尋ねる。返答を本文として保存。

---

## エラーハンドリング

| ケース | 対応 |
|---|---|
| KB ディレクトリが存在しない | 終了。`git clone git@github.com:daikw/knowledgebase.git $KB_PATH` を提案 |
| URL が取得できない | エラーを表示し、手動で要点を `/kb note` するよう提案 |
| gh CLI 未認証 | `gh auth login` を提案して終了 |
| 既存ファイルと slug 衝突 | 末尾に `-2`, `-3` ... を付けて保存 |
| 機密パターン検出 (sk-, ghp_, 社内 URL 等) | 保存前に警告、ユーザー確認を取る |

## 機密情報の扱い

保存前に以下の正規表現でマスクを検討（検出したら本文から削除 + 警告）:
- `sk-[A-Za-z0-9]{20,}` (API キー)
- `ghp_[A-Za-z0-9]{30,}`, `glpat-[A-Za-z0-9_-]{20,}` (GitHub/GitLab PAT)
- 社内限定ドメイン（ユーザーに都度確認）

## 検討中の拡張案（未着手・実装時期未定）

- `/kb ingest session [path]` — Claude Code 会話履歴から抽出
- `/kb ingest slack <url>` — Slack メッセージ/スレッド
- `/kb ingest tweet` — X ブックマーク（API 調達後）
- `/kb triage` — inbox 対話的 3 択 triage
- `/kb query <question>` — wiki 検索 + LLM 合成
- `/kb lint` — duplicate / orphan / stale / unsupported claim 検出
- `/kb compact <page>` — ページ rewrite draft 作成

## 関連

- KB リポジトリ: https://github.com/daikw/knowledgebase (private)
- 設計判断: `decisions/local-wiki-is-source-of-truth.md`
- 昇格ルール: `patterns/promote-on-second-use.md`
- スキーマ: `CLAUDE.md`
