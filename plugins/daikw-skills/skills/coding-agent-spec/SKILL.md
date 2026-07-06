---
name: coding-agent-spec
description: "Researches coding-agent specifications (Claude Code, Codex, Cursor, etc.), verifies facts from official docs/repos, and produces a structured comparison report. Triggers when users ask to investigate, compare, or update agent specs, hooks, config schemas, MCP integration, or CLI behavior. キーワード: コーディングエージェント仕様, hook仕様, Claude Code仕様, Codex仕様, Cursor仕様, agent spec. 特定エージェントの使い方を実行するだけの場面（既存スキルの呼び出しで足りるとき）では使わない。"
user-invocable: true
argument-hint: "<対象エージェント名・調査トピック・比較範囲（省略時は横断調査）>"
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
  - WebSearch
  - WebFetch
  - Task
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskList
---

# coding-agent-spec

コーディングエージェント仕様を調査し、根拠付きの比較レポートを作成する。

## Trigger

- エージェント仕様の調査（hooks / config / MCP / CLI / session）
- 複数エージェントの仕様比較
- 既存理解の更新（最新仕様との差分確認）
- 実装前の互換性確認

## Input / Output

- Input: `$ARGUMENTS`（エージェント名、トピック、比較条件）
- Output: Markdown レポート（要点、比較表、未確認事項、参照 URL）

## Scope

主な調査トピック:

1. フックシステム（イベント、入出力、終了コード、制御）
2. 設定ファイル（場所、形式、優先順位、スキーマ）
3. CLI（コマンド、フラグ、環境変数）
4. MCP 統合（設定方法、対応範囲、制約）
5. スキル/エージェント拡張機構
6. セッション管理（保存形式、復元、ログ）

主な調査対象エージェントとリソースは [references.md](references.md) を参照。

## Freedom Level

- **低**: ユーザー指定範囲のみ調査。追加探索しない。
- **中**: 指定範囲を中心に、関連する公式ページまで拡張。（`$ARGUMENTS` が曖昧なときのデフォルト）
- **高**: 横断比較と差分分析まで実施し、必要なら追加トピックも提案。

## Workflow

### Phase 0: 依頼の正規化

`$ARGUMENTS` を以下に正規化する:

- targets: 対象エージェント（例: Claude Code, Codex, Cursor）
- topics: 調査トピック
- depth: 深さ（低/中/高）
- deliverable: 出力形式（比較重視/単体調査）

チェックリスト:
```
- [ ] 対象エージェントが確定した
- [ ] 調査トピックが確定した
- [ ] 深さ（低/中/高）を確定した
```

### Phase 1: ローカル情報の収集（プロジェクト非依存）

ローカルで参照可能な設定・実装の痕跡を確認する。

```bash
# エージェント関連ファイルの候補を列挙
find "$PWD" -type f \( -path "*/.claude/*" -o -path "*/.codex/*" -o -path "*/.cursor/*" \) 2>/dev/null

# 仕様に関連するキーワードを横断検索（言語非依存）
rg -n --hidden -l "(hook|hooks|mcp|session|transcript|config\.toml|settings\.json)" "$PWD" 2>/dev/null
```

チェックリスト:
```
- [ ] ローカル由来の Fact を抽出した
- [ ] 推測と事実を分離した
```

### Phase 2: 公式ソース調査

プログレッシブに調査する（必要箇所のみ深掘り）:

1. 公式ドキュメントのトップ/目次を確認
2. 該当トピックの一次情報ページを確認
3. 不足時のみリポジトリ内の関連ファイルを確認（README/docs/schema/changelog）

並列調査が有効な場合は Task を分割する（エージェント別またはトピック別）。

Task 指示テンプレート:
```text
対象: <agent>
トピック: <topic>
必須:
1) 公式ドキュメント URL と該当セクションを特定
2) 公式リポジトリの一次情報を確認（最新安定版時点）
3) 確定仕様（Fact）と未確認事項（Unknown）を分離して要約
出力: 参照 URL / Fact / Unknown
```

チェックリスト:
```
- [ ] 参照元が一次情報中心になっている
- [ ] 最新安定版の情報として確認した
- [ ] Unknown を明示した
```

### Phase 3: 統合と比較表作成

収集結果を統合し、比較可能な形式に揃える。

必須構成: サマリー（3-5点）/ エージェント別仕様 / 比較表 / 未確認事項 / 参照 URL 一覧

レポートテンプレートは [report-template.md](report-template.md) を参照。

チェックリスト:
```
- [ ] 比較軸が揃っている
- [ ] Fact / Assumption / Unknown が分離されている
- [ ] 参照 URL が全主張に対応している
```

### Phase 4: 出力整形と保存（任意）

ユーザーが保存を希望する場合のみファイル出力する。

チェックリスト:
```
- [ ] ユーザー指定形式に整形した
- [ ] 保存要否を確認した
```

## Quality Rules

- 一次情報（公式 docs / 公式 repo）を優先する
- 断定には根拠 URL を付ける
- 推測は `Assumption:` として明示する
- JSON スキーマがあれば全文引用する
