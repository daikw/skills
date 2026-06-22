---
name: meta-rules
description: Rules/Skills/Agents の設計原則と更新ガイドライン。設定ファイルの追加・変更・削除時に参照。
---

# Meta Rules - 設計原則と更新ガイドライン

Agent 設定（Rules/Skills/Agents）を管理するためのメタルール。

## When to Use

- `rules/` `skills/` `agents/` の追加・変更・削除時
- 新しいルールやスキルをどこに置くか迷った時
- 設定の整理・リファクタリング時

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

see also: https://code.claude.com/docs/en/skills

### 良い例
- 特定言語/フレームワークのベストプラクティス
- ツール固有のワークフロー（GitHub PR 対応、jujutsu, Docker など）
- ドメイン知識（認証、決済など）

### 原則
- 発動条件（When to Use）を明確に定義
- 短い代表例・必須コマンド（必須オプションまで）は本文に含める
- `SKILL.md` には初回発動時に必須の発動条件、判断基準、最小手順、参照分岐、中止条件を書く
- 更新頻度が高い手順、任意オプション、条件付きでしか読まない詳細、長い例、例外処理、背景説明は `references/` に分ける
- 知識参照のみ、実行は Agents へ
- frontmatter に name と description を記載
- SKILL.md under 500 lines. Move detailed reference material to separate files.
- 動作確認: 指示文は `/empirical-prompt-tuning`、スクリプトは `/agent-skill-testing` を使う（自己再読はバイアスが入るので不可）

### ファイル構成
```
my-skill/
├── SKILL.md           # Main instructions (required)
├── template.md        # Template for Claude to fill in
├── examples/
│   └── sample.md      # Example output showing expected format
└── scripts/
    └── validate.sh    # Script Claude can execute
```

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
- [ ] 既存との重複がないか確認
- [ ] Rules/Skills/Agents のどれが適切か判断
- [ ] agent 設定ではなく README / docs / 削除が適切ではないか確認
- [ ] 編集対象が active source of truth か確認
- [ ] 発動条件は明確か（Skills の場合）

### 追加時
- [ ] 1ファイル = 1テーマを守る
- [ ] 具体例を含める
- [ ] 簡潔に保つ（長すぎる場合は分割を検討）
- [ ] 経緯を知らない未来の読者が単独で判断に使えるか確認

### 削除時
- [ ] 他から参照されていないか確認
- [ ] 代替手段があるか確認

### source of truth 確認 (該当する場合)

設定・skill・agent の同名ファイルが複数見つかった場合は、名前の一致だけで同期先を決めない。

- plugin manifest、install path、remote URL、archive 状態、直近 commit から active source を確認する
- archived / deprecated repo は参照専用として扱い、同期先にしない
- cache / installed copy は即時反映用に編集してよいが、永続化は active source 側で commit する

### dotfile manager 同期 (該当する場合)

`~/.claude/` を chezmoi / stow / yadm 等の dotfile manager で管理している場合、
編集時は source 側も同期させる必要がある。詳細は
[`references/chezmoi-sync.md`](./references/chezmoi-sync.md) 参照。

## 関連スキル

- `/harness-audit`: 既存の rules/skills/agents/hooks/commands/plugins/personas/teams/memory を棚卸しし、陳腐化・重複・実効性ギャップを検出する
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
    ├─ 特定技術/ワークフロー固有？ ─Yes→ Skills
    │
    No
    ↓
    └─ タスク実行が必要？ ─Yes→ Agents
                          │
                          No
                          ↓
                       Skills（知識として）
```
