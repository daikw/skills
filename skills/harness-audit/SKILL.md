---
name: auditing-harness
description: >-
  Audits the Claude Code harness configuration under ~/.claude/ — rules, agents, skills,
  hooks, commands, plugins, personas, teams, and memory. Detects stale files, broken
  cross-references, duplicate responsibilities, rule effectiveness gaps, and memory drift.
  Use when the user says 'harness-audit', '棚卸し', 'ハーネスの状態', 'ルールの整合性チェック',
  or 'メモリの整理'. Also triggered by Desktop Schedule for periodic automated runs.
---

# Harness Audit

Claude Code のハーネス構成（`~/.claude/` 配下）を棚卸しし、問題を検出して報告する。

**Read-only がデフォルト。** ファイルの修正はユーザーが明示的に依頼した場合のみ行う。

**Freedom Level: 中** — チェック項目は固定だが、検出した問題への提案は文脈に応じて判断する。

## 住み分け

| スキル | 責務 |
|---|---|
| `/meta-rules` | 設計原則・分類ルール。追加・変更・削除時の判断基準 |
| `/harness-audit` | 現物検査・診断。定期的な棚卸しと問題検出 |

## Audit Workflow

### Phase 1: インベントリ収集

以下のディレクトリを走査し、ファイル数と一覧を取得する。

| 対象 | パス | 確認内容 |
|---|---|---|
| Rules | `~/.claude/rules/*.md` | ファイル一覧 |
| Agents | `~/.claude/agents/*.md` | ファイル一覧 |
| Skills | `~/.claude/skills/*/SKILL.md` | ディレクトリ一覧、SKILL.md の有無 |
| Hooks | `~/.claude/settings.json` → `hooks` | 登録済みフック一覧 |
| Commands | `~/.claude/commands/*.md` | ファイル一覧 |
| Plugins | `~/.claude/plugins/installed_plugins.json` + `settings.json` → `enabledPlugins` | インストール済み vs 有効 |
| Personas | `~/.claude/personas/*.md` | ファイル一覧 |
| Teams | `~/.claude/teams/` | ディレクトリ一覧 |
| Memory | `~/.claude/projects/*/memory/` | プロジェクトごとの MEMORY.md とエントリ数 |

### Phase 2: 整合性チェック

rules/agents/skills/commands 間の相互参照が実在するか検証する。

チェック項目:
- `rules/agents.md` のテーブルに列挙されたエージェント名が `agents/*.md` に存在するか
- `rules/testing.md` 等で参照されているエージェント・スキルが実在するか
- `settings.json` の hooks で参照しているコマンド・スクリプトが PATH 上に存在するか
- `settings.json` の `enabledPlugins` にあるプラグインが `installed_plugins.json` に存在するか
- `CLAUDE.md` から参照されているルール・スキルが実在するか

### Phase 3: 陳腐化検知

- **mtime が 180 日以上のファイル**: rules, agents, skills の中で長期間未更新のものをリスト
- **settings.json と hooks/ ディレクトリの乖離**: hooks/ に実装があるのに settings.json で未参照、またはその逆
- **無効化されたプラグイン**: `enabledPlugins: false` のまま放置されているもの
- **plugins/cache 内の古いバージョン**: `lastUpdated` が 180 日以上前のもの

### Phase 4: 重複・責務の重なり検出

- rules と skills で同じトピックを扱っているもの（例: セキュリティが rules にも skills にもある）
- 複数の skills が同じトリガー条件で発火しうるもの（description の類似度）
- agents と skills で責務が曖昧なもの

### Phase 5: ルール実効性マトリクス

各 rule について、どのレベルで実効性があるか評価する。

| Level | 意味 | 例 |
|---|---|---|
| 0 | 文書のみ。skill/agent/hook のどれにも接続されていない | — |
| 1 | skill か agent の手順に組み込まれている | git-workflow → /pr skill |
| 2 | hook で検出可能 | supply-chain-security → supply_chain_guard.py（ただし現在未接続） |
| 3 | hook で強制ブロック + 直近の利用実績あり | security → aws-sso-login guard |

Level 0-1 の rule は「書いてあるが守られるかは LLM 任せ」なので、hook 化の検討を提案する。

### Phase 6: メモリドリフト検知

`~/.claude/projects/*/memory/` を横断して以下をチェック:
- **MEMORY.md のエントリ数**: 200 行上限に近づいていないか
- **古いメモリ**: type: project のメモリで、記載日から 90 日以上経過しているもの
- **現状との矛盾**: type: feedback のメモリが現在の rules と矛盾していないか（可能な範囲で）
- **孤立ファイル**: MEMORY.md から参照されていないメモリファイル
- **空プロジェクト**: memory ディレクトリはあるが中身が空、または MEMORY.md しかないもの

## 出力フォーマット

```markdown
# Harness Audit Report — YYYY-MM-DD

## Summary
- 総ファイル数: N
- 問題: Critical N / Warning N / Info N

## Inventory
| カテゴリ | 件数 | 前回比 |
|---|---|---|
| Rules | N | — |
| ... | | |

## Findings
| Severity | カテゴリ | 問題 | 対象ファイル | 推奨アクション |
|---|---|---|---|---|
| Critical | 整合性 | agents.md に記載のエージェントが存在しない | rules/agents.md | テーブルから除去 or エージェント作成 |
| Warning | 陳腐化 | 180日以上未更新 | skills/foo/SKILL.md | 内容を確認して更新 or 削除 |
| ... | | | | |

## Rule Effectiveness Matrix
| Rule | Level | 接続先 | Gap |
|---|---|---|---|
| security | 3 | aws-sso-login hook | — |
| testing | 1 | tdd-guide agent のみ | hook 未接続 |
| ... | | | |

## Memory Status
| プロジェクト | エントリ数 | 古いメモリ | 孤立ファイル |
|---|---|---|---|
| tools | 3 | 0 | 0 |
| ... | | | |

## Proposed Actions
1. ...
2. ...
```

## 自動実行での利用

Desktop Schedule で週次実行する場合:

```
claude -p "/harness-audit" --allowedTools "Read,Glob,Grep,Bash"
```

問題が見つかった場合は macOS 通知で知らせる。Notification hook の設定例:

```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "osascript -e 'display notification \"$CLAUDE_NOTIFICATION\" with title \"Harness Audit\"'"
      }]
    }]
  }
}
```
