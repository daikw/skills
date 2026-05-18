---
name: skill-creator
description: "Creates or improves Claude Code skills (SKILL.md and bundled resources). Use when the user wants to design a new skill, refactor an existing one, or apply best practices to skill authoring. Triggers on requests like 'create a skill for X', 'improve this skill', 'skill 設計して', 'スキルを作って'."
user-invocable: true
argument-hint: "<スキルの目的や改善したいスキル名（省略時はゼロから設計）>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - AskUserQuestion
---

# skill-creator

Claude Code スキルを設計・作成・改善する。

公式ベストプラクティスは [references/best-practices.md](references/best-practices.md) を参照。

## Anatomy of a Skill

```
skill-name/
├── SKILL.md           # 必須: frontmatter + 本文（500行以内）
├── references/        # 必要時のみ読み込む参照ドキュメント
├── scripts/           # 実行可能スクリプト（決定論的処理向け）
└── assets/            # 出力に含めるファイル（テンプレート・画像等）
```

ローカル（`~/.claude/skills/`）に置いたスキルはプラグイン版を上書きする。

## Creation Process

### Step 1: 用途の具体化

スキルの使用例を具体的なユーザー発話として 3 つ以上収集する。不明な場合は AskUserQuestion で聞く。

確認すること:
- どんな問いかけでこのスキルが発火してほしいか
- 何を入力し、何を出力するか
- スキルが持つべき再利用可能な資産（スクリプト・スキーマ・テンプレート等）があるか

### Step 2: 再利用資産の計画

各ユースケースを「ゼロから実行するとどうなるか」に分解し、繰り返し書くことになるものを特定する:

| 資産タイプ | 適したケース | 配置先 |
|---|---|---|
| スクリプト | 毎回同じコードを書く処理 | `scripts/` |
| スキーマ・API仕様 | 毎回調べ直す情報 | `references/` |
| ボイラープレート | 毎回同じ土台から始める | `assets/` |

### Step 3: スキルの初期化

新規作成の場合はディレクトリを作成し、SKILL.md のテンプレートを置く。既存スキルの改善なら Step 4 へ。

```bash
mkdir -p ~/.claude/skills/<skill-name>/references
```

### Step 4: SKILL.md の作成・編集

#### Frontmatter の書き方

```yaml
---
name: <gerund-form-name>      # 例: processing-pdfs, researching-coding-agent-specs
description: "<third-person, 具体的なトリガー条件を含む>"
---
```

**name の規則:**
- gerund形推奨: `processing-pdfs`, `analyzing-spreadsheets`
- lowercase + hyphens のみ。`anthropic` `claude` は予約語で使用不可
- 最大 64 文字

**description の規則（最重要）:**
- 必ず third-person で書く（「I can…」「You can…」は NG）
- 「何をするか」と「いつ発火するか（トリガー条件）」の両方を含める
- 最大 1024 文字。XML タグ不可
- キーワードの列挙よりも自然な文章で trigger を表現する

良い例:
```
"Processes Excel files and generates formatted reports.
 Use when working with .xlsx/.csv files or when the user mentions
 spreadsheets, pivot tables, or data analysis."
```

悪い例:
```
"Helps with documents"  # 曖昧
"I can help you process Excel files"  # first-person NG
```

#### 本文の書き方

- **500 行以内** を厳守。超える場合は `references/` に分割
- Claude が既に知っていることは書かない（「PDF とは何か」等）
- 詳細な参照情報は別ファイルへ移し、SKILL.md からリンクを張る（1 階層まで）
- 時間依存情報（「2025年8月以降は…」等）を書かない

**Freedom Level を明示する:**
- **低**: 手順通りに実行。逸脱しない（脆弱な処理・一貫性が必須な場合）
- **中**: 推奨パターンを使いつつ、文脈に応じて調整
- **高**: 複数のアプローチが有効。Claude が最善を判断

### Step 5: 動作検証

スキルは 2 つのレイヤーで検証する。自己再読は構造的にバイアスが入るので不可。

1. **指示文（SKILL.md / プロンプト）の明瞭性** → `/empirical-prompt-tuning`
   - バイアスを排した別 subagent に動かしてもらい、不明瞭点・裁量補完を炙り出す
   - 新規作成・大幅改訂直後は必須
2. **スクリプト・コードの正しさ**（`scripts/` を含むスキルのみ） → `/agent-skill-testing`
   - 副作用観測・ファジング・不変条件・OS 差分・無言の失敗を扱う

純粋に指示文だけなら 1 のみ、純粋にスクリプト集なら 2 のみ、両方含むなら順に両方。

検証で詰まった場合の対処:
- Claude がスキルを選択しない → description を見直す
- Claude が間違ったことをする → SKILL.md の当該セクションを強化
- Haiku でも動くか確認（Opus 向けに最適化すると Haiku では過少情報になる）

**Eval-first 原則:** 広範な手順を書く前に、まず 3 つの評価シナリオを作る。実際のギャップに対してのみ手順を追加する。

### Step 6: 改善サイクル

```
実タスクで使う → 詰まる箇所を観察 → SKILL.md を修正 → 再テスト
```

Claude が特定のファイルを読まない、または繰り返し同じファイルを読む場合は、参照の明示方法やファイル構成を見直す。

## Anti-patterns

- **選択肢を並べすぎる**: 「pypdf か pdfplumber か PyMuPDF か…」→ デフォルトを一つ示し、例外条件のみ添える
- **時間依存情報**: バージョン日付や「〜以降」→「現行バージョン」「旧パターン」セクションで管理
- **Windows パス**: バックスラッシュ不可。必ずスラッシュ (`scripts/helper.py`)
- **深いネスト参照**: SKILL.md → A.md → B.md → 実情報 は NG。SKILL.md から直接リンク
- **READMEの追加**: スキルに README.md, CHANGELOG.md 等は不要。余計なファイルを作らない
- **When to Use セクションを本文に書く**: 本文はスキル発火後に読まれる。トリガー条件は description に書く

## Checklist（公開前）

```
Frontmatter
- [ ] name が gerund 形（または noun 形）で lowercase/hyphens のみ
- [ ] description が third-person でトリガー条件を含む
- [ ] description が 1024 文字以内

本文
- [ ] 500 行以内
- [ ] 時間依存情報がない
- [ ] 参照が 1 階層まで
- [ ] Freedom Level が明示されているか、または自明

テスト
- [ ] 3 つ以上の実ユースケースで動作確認
- [ ] description を見てスキルが正しく選択される
```
