---
name: meta-rules
description: "SKILL.md・rules・agents・commands の作成・編集・リネーム・移行・削除・統廃合・棚卸し・整理を行うときに使う設計原則とチェックリスト。daikw/skills 等のスキルリポジトリ内でのファイル直接編集にも適用する。配置先の判断（公開/私的/repo-local/検証中）、frontmatter・description の書き方、機械検証（scripts/lint.sh）までを扱う。既存スキルを使ってタスクを実行するだけの場面や、settings.json 等の単発設定変更には使わない — 前者は個別スキルの description、後者は /update-config を参照。"
---

# Meta Rules - 設計原則と更新ガイドライン

Agent 設定（Rules/Skills/Agents/Commands）の作成・編集・リネーム・移行・削除・統廃合・棚卸し・整理を担うメタスキル。

## When to Use

- `rules/` `skills/` `agents/` `commands/` の追加・変更・削除・リネーム・移行・統廃合・棚卸し・整理を行うとき
- daikw/skills のようなスキルリポジトリ内で SKILL.md やスクリプトを直接編集するとき
- 新しいルールやスキルをどこに置くか（公開/私的/repo-local/検証中）迷ったとき

いつ使わないか:
- 既存スキルを呼び出してタスクをこなすだけの場面（各スキル自身の description に従う）
- settings.json のようなハーネス設定ファイルの単発変更（`/update-config` を使う）

## 使い分け

| 種類 | 性質 | 用途 |
|------|------|------|
| **Rules** | 非交渉的（常に従う） | プロジェクト/技術非依存の普遍的ガイドライン |
| **Skills** | 参照型（必要時に使う） | 特定技術・ワークフロー固有の知識 |
| **Agents** | 実行型（タスク委譲） | 自律的なタスク実行 |

## 共通原則

### 未来読者への自立性

設定や指示は、経緯を知らない未来の自分や AI が単独で読んでも判断に使える形にする。

- 過去の失敗、今回だけの対比、議論の経緯は、そのまま残さない
- 経緯を残すのは、将来の判断を変える一般原則・制約・例外条件に抽象化できる場合だけ
- 「何を避けるか」よりも「望ましい最終形は何か」を正方向に書く
- 文脈を知らない読者に行動変化を生まない情報は削る

### 置き場所の境界

Rules/Skills/Agents に書く前に、それが agent 設定として再利用される知識か確認する。

- プロジェクト固有の運用は、そのプロジェクトの README / docs に置く
- 一回限りの経緯や、将来の行動を変えないメモは削る
- 時系列の証跡は、設定ではなく commit 履歴、ログ、作業メモに任せる

## Rules

**普遍的・コンテキスト非依存のものに絞る。**

### 良い例
- セキュリティ原則（秘密情報の扱い、入力検証）
- テスト方針（TDD、カバレッジ基準）
- Git hygiene（コミットメッセージ形式など全タスク共通の約束）
- コード品質（レビュー基準）

### 悪い例
- 特定フレームワークの使い方
- ライブラリ固有の設定
- プロジェクト固有のディレクトリ構成

### 原則
- 常に適用されるため、最小限に保つ
- 例外なく従うべきものだけを記載
- 常時適用でも、特定技術・ワークフロー固有なら Skills へ
- 特定技術への依存は Skills へ
- 1ファイル = 1テーマ（単一責任）

## Skills

**特定のドメイン・技術・ワークフローに関する知識。**

see also: https://code.claude.com/docs/en/skills, [references/skill-authoring-best-practices.md](references/skill-authoring-best-practices.md)（公式原則の詳細）

### 良い例
- 特定言語/フレームワークのベストプラクティス
- ツール固有のワークフロー（GitHub PR 対応、jujutsu, Docker など）
- ドメイン知識（認証、決済など）

### frontmatter の規則

```yaml
---
name: <gerund-form-name>      # 例: processing-pdfs, researching-coding-agent-specs
description: "<third-person, 具体的なトリガー条件を含む>"
---
```

- **name**: gerund 形推奨（`processing-pdfs` 等）。lowercase + hyphen のみ、最大 64 文字。ディレクトリ名と厳密に一致させる（`anthropic` `claude` は予約語で使用不可）
- **description**: 必ず third-person（「I can…」NG）。「何をするか」と「いつ発火するか」の両方を含める。最大 1024 文字、XML タグ不可。キーワード列挙より自然な文章でトリガーを表現し、**「いつ使わないか」も 1 行入れる**（誤爆・不発の両方を抑える）

### 本文の書き方

- **500 行以内**を厳守。超える場合は `references/` に分割
- Claude が既に知っていることは書かない（一般的なスキル作成論等）。ユーザー・プロジェクト固有の判断基準だけを書く
- 詳細な参照情報は別ファイルへ移し、SKILL.md から直接リンクを張る（1 階層まで。SKILL.md → A.md → B.md の多段ネストは不可）
- 時間依存情報（「2025年8月以降は…」等）を書かない
- 発動条件（When to Use）は description に書く。本文はスキル発火後にしか読まれないため、本文に書いても discovery には効かない

**Freedom Level を明示する:**
- **低**: 手順通りに実行。逸脱しない（脆弱な処理・一貫性が必須な場合）
- **中**: 推奨パターンを使いつつ、文脈に応じて調整
- **高**: 複数のアプローチが有効。Claude が最善を判断

### ファイル構成

```
my-skill/
├── SKILL.md           # 必須。frontmatter + 本文（500行以内）
├── references/        # 必要時のみ読み込む参照ドキュメント
├── scripts/            # 実行可能スクリプト（決定論的処理向け）
└── assets/             # 出力に含めるファイル（テンプレート・画像等）
```

### Anti-patterns

- **選択肢を並べすぎる**: 「A か B か C か…」→ デフォルトを一つ示し、例外条件のみ添える
- **時間依存情報**: バージョン日付や「〜以降」→「現行バージョン」「旧パターン」で管理
- **深いネスト参照**: SKILL.md → A.md → B.md → 実情報 は NG
- **README の追加**: スキルに README.md, CHANGELOG.md 等は不要
- **When to Use を本文に書く**: トリガー条件は description に書く
- **フェーズ固有コマンドの汎用化**: 特定言語・特定リポジトリのコマンド（`go test`, `./internal/*.go` 等）を汎用スキルの手順に埋め込まない。その手順は repo-local（当該 repo の `.claude/skills/`）に置く
- **ライブ外部環境の並列テスト**: GUI アプリ・実機・SaaS ダッシュボードのような巻き戻せない環境を複数エージェントで同時に触らない（詳細は [references/agent-skill-testing-checklist.md](references/agent-skill-testing-checklist.md) の 8 節）

### 配置判断（公開/私的/repo-local/検証中の 4 系統、正本）

新規スキルの置き場所は、以下の 3 軸で判定する。

1. **公開性**: 誰が読むか（不特定多数 / 自分のみ / 特定 repo の関係者のみ）
2. **ハーネス中立性**: Claude Code / Codex CLI の両方で使うか、片方専用か
3. **機微性**: 個人情報・内部ホスト名・実機値・組織固有の GID/ID を含むか

| 系統 | 判定 | 置き場所 | 発動 |
|---|---|---|---|
| **Public** | 公開可・機微情報なし | `daikw/skills` の `plugins/daikw-skills/skills/<name>/`（このリポジトリ自身） | `daikw:<name>` |
| **Private** | 機微情報を含む・自分専用 | chezmoi 管理の `~/.claude/skills/<name>/`（Claude）+ `~/.agents/skills/<name>/`（Codex/共通） | prefix なし、user-level |
| **Repo-local** | 特定 repo の運用にしか意味がない | 当該 repo の `.claude/skills/<name>/` | prefix なし、project-level |
| **検証中の一次** | discovery から意図的に外したい | 検証中のプロジェクトの `tmp-skills/.claude/skills/<name>/` 等 | 発動なし（discovery 対象外） |

判断フロー: 機微情報を含む → Private。特定 repo でしか意味を持たない → Repo-local。開発検証中で discovery から外したい → 検証中の一次。それ以外で公開可能 → Public（このリポジトリ）。

**両ハーネス両置きルール**: Public / Private のスキルは、ユーザーから明示的に片方だけと指示されない限り、Codex/共通向け（`.agents/skills/<name>/` または `agents/openai.yaml`）と Claude 向け（`.claude/skills/<name>/` または `SKILL.md` + 同梱リソース）の両方を用意する。chezmoi 管理下（Private）では source 側（`dot_agents/skills/<skill>/`、`dot_claude/skills/<skill>/`）を更新し、`chezmoi apply` と各ハーネスでの動作検証まで行う。`agents/openai.yaml` は Codex/共通側だけに置き、Claude 側には原則として `SKILL.md` と必要な同梱リソースだけを置く。

新規作成時は、この3軸をユーザーに AskUserQuestion で確認してから配置する（配置後にリポジトリを跨いで移動するのはコストが高いため、着手前に決める）。

## Agents

**自律的なタスク実行を担当。**

### 良い例
- コードレビュー実行
- テスト実行・結果分析
- セキュリティスキャン
- ビルドエラー解決

### 原則
- 単一責任（1エージェント = 1目的）
- 実行が必要な作業に使用
- 知識参照だけなら Skills を使う
- 並列実行可能なら並列で起動

## 更新チェックリスト

### 追加前
- [ ] 既存との重複がないか確認（`grep -rl <キーワード> plugins/daikw-skills/skills/*/SKILL.md` 等）
- [ ] Rules/Skills/Agents のどれが適切か判断
- [ ] agent 設定ではなく README / docs / 削除が適切ではないか確認
- [ ] 編集対象が active source of truth か確認
- [ ] 発動条件は明確か（Skills の場合。「いつ使わないか」も含めて）
- [ ] 配置先の3軸判定（公開性/ハーネス中立性/機微性）を済ませたか

### 追加時
- [ ] 1ファイル = 1テーマを守る
- [ ] 具体例を含める
- [ ] 簡潔に保つ（長すぎる場合は分割を検討）
- [ ] 経緯を知らない未来の読者が単独で判断に使えるか確認
- [ ] `scripts/lint.sh <skill-name>` を実行し、機械検証可能な項目を通す

### 削除時
- [ ] 他から参照されていないか確認（他スキルの SKILL.md、rules/、CLAUDE.md、agents/ を横断 grep）
- [ ] 代替手段があるか確認

### リネーム・移行時（NEW）

- [ ] 旧名の利用実績を履歴・grep で確認する（起動ログ、他スキルからの参照、ユーザーの口頭呼称）
- [ ] 利用実績があるなら、呼称断絶を告知するか、旧名からのエイリアス・redirect を検討する
- [ ] 移行後、旧パスへの参照が repo 内・chezmoi source・CLAUDE.md に残っていないか grep で確認する

### 配布形態検証（NEW）

- [ ] plugin 配布（`daikw:<name>` 等）で、SKILL.md 記載のコマンド例・パスがインストール先で実際に成立するか確認する（配布経路がローカルコピー前提の固定パスになっていないか）
- [ ] スクリプトを含む場合、起動時に注入される `Base directory for this skill: <path>` を使う設計になっているか確認する（決め打ちパスにしない）

### 公開機微チェック（NEW）

- [ ] 公開リポ（daikw/skills 等）に置くスキルに、実機の値・内部ホスト名・個人情報・組織固有 ID が残っていないか確認する
- [ ] 該当する具体値は匿名化するか、Private 系統（chezmoi 管理）へ配置し直す

### source of truth 確認 (該当する場合)

設定・skill・agent の同名ファイルが複数見つかった場合は、名前の一致だけで同期先を決めない。

- plugin manifest、install path、remote URL、archive 状態、直近 commit から active source を確認する
- archived / deprecated repo は参照専用として扱い、同期先にしない
- cache / installed copy は即時反映用に編集してよいが、永続化は active source 側で commit する

### dotfile manager 同期 (該当する場合)

`~/.claude/` を chezmoi / stow / yadm 等の dotfile manager で管理している場合、
編集時は source 側も同期させる必要がある。詳細は
[`references/chezmoi-sync.md`](./references/chezmoi-sync.md) 参照。

## 動作検証

スキルは 2 つのレイヤーで検証する。自己再読は構造的にバイアスが入るので不可。

1. **指示文（SKILL.md / プロンプト）の明瞭性** → `/empirical-prompt-tuning`
   - バイアスを排した別 subagent に動かしてもらい、不明瞭点・裁量補完を炙り出す
   - 新規作成・大幅改訂直後は必須
2. **スクリプト・コードの正しさ**（`scripts/` を含むスキルのみ） → [references/agent-skill-testing-checklist.md](references/agent-skill-testing-checklist.md)
   - 副作用観測・ファジング・不変条件・OS 差分・無言の失敗を扱うチェックリスト
3. **機械検証可能な部分** → `scripts/lint.sh`（下記）。1・2 の代替ではなく、frontmatter や参照パスの実在性など機械的に検出できる範囲だけをカバーする

検証で詰まった場合の対処:
- Claude がスキルを選択しない → description を見直す（トリガー語彙・「いつ使わないか」）
- Claude が間違ったことをする → SKILL.md の当該セクションを強化
- Haiku でも動くか確認する（Opus 向けに最適化すると Haiku では過少情報になりうる）

## scripts/lint.sh

`plugins/daikw-skills/skills/*/` を対象に、機械検証可能な項目だけを静的にチェックする。bash + 標準コマンドのみで動く。

```sh
# 全スキルを検証
plugins/daikw-skills/skills/meta-rules/scripts/lint.sh

# 単一スキルのみ検証（パス指定 or ディレクトリ名指定）
plugins/daikw-skills/skills/meta-rules/scripts/lint.sh meta-rules
```

チェック項目:
- frontmatter の `name` とディレクトリ名の一致
- `allowed-tools` の各エントリが既知ツールリストに実在するか
- 本文中の `references/` `scripts/` `assets/` 相対パス参照が実在するか
- supply-chain rules との矛盾（`curl` を `sh`/`bash` に直接パイプする実行、`npx <pkg>@latest` 等の一回限り外部実行、Docker `:latest` タグ）
- description の長さ上限（目安 1024 字）と「いつ使わないか」系記述の有無（警告レベル）

エラー検出時は終了コード 1。追加・変更前後にこのスクリプトを通すことを追加前/追加時チェックリストの一部として扱う。

参照パスチェックは正規表現による近似のため、「ユーザー自身の別リポジトリに置くことを勧めるパス」を地の文で言及しているだけの箇所も誤検出しうる（例: 3d-printing の「repo 内に wrapper スクリプトを置く運用が現実的」という説明）。検出されたら実際にそのスキルが同梱を意図しているパスか確認し、意図した同梱物の欠落だけを直す。

## 関連スキル

- `/harness-audit`: 既存の rules/skills/agents/hooks/commands/plugins/personas/teams/memory を棚卸しし、陳腐化・重複・実効性ギャップを検出する
- `/empirical-prompt-tuning`: 指示文（SKILL.md 含む）の明瞭性をバイアスを排した subagent で検証する
- 新規追加や分類判断は `/meta-rules`、定期点検と証跡確認は `/harness-audit` を使う

## 判断フローチャート

```
新しい知識/ルールを追加したい
    │
    ├─ agent 設定として再利用する？ ─No→ README / docs / 削除
    │
    Yes
    ↓
    ├─ 常に従うべき？ ─Yes→ 技術非依存？ ─Yes→ Rules
    │                              │
    │                              No
    │                              ↓
    │                         Skills
    │
    No
    ↓
    ├─ 特定技術/ワークフロー固有？ ─Yes→ Skills（配置は3軸で判定）
    │
    No
    ↓
    └─ タスク実行が必要？ ─Yes→ Agents
                          │
                          No
                          ↓
                       Skills（知識として）
```
