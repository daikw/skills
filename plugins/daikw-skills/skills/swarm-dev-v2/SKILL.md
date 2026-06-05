---
name: swarm-dev-v2
description: チームを編成して開発する（軽量版）。プロジェクトを探索的に調査し、専門エージェントのチームで修正・テスト・レビューを実施する。swarm-dev の情報量削減版。
user-invocable: true
argument-hint: "<タスクの概要 or 修正方針>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - Skill
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - TeamCreate
  - TeamDelete
  - SendMessage
---

# swarm-dev-v2 - チーム編成・並列開発スキル（軽量版）

## Non-Negotiable Rules（例外なく守ること）

1. 全実装エージェントは完了時に `[CHANGE_REPORT]` を出力せよ
2. いずれかが `frontend_changed: yes` → Phase 4 を実行せよ
3. `frontend_changed: yes` かつ `chrome_test_status != passed` → PR 作成禁止
4. ブラウザツール利用不可 or dev server 起動不可 → PR 作成前に停止し理由を報告せよ
5. 成功の推測禁止。記録されたテスト証跡のみが根拠
6. Phase 4 ではコード修正禁止。修正が必要なら Phase 3 に差し戻せ
7. `browser_validation_requested=required` → `frontend_changed` に関わらず Phase 4 実行

## 安全ルール

- リーダーは実作業しない（コーディネーションのみ）
- main 直接 push 禁止（feature branch + PR）
- 大規模削除・破壊的操作はユーザー確認必須
- CRITICAL 最優先。実行コマンドは推測禁止（プロジェクトから読み取れ）

---

## 実行フロー

```
Phase 0 → 0.5 → 1 → 2 → 3 → 4(条件付き) → 5
```

### Phase 0: 要件確認

`$ARGUMENTS` 確認、不明点は AskUserQuestion。以下を記録:
- `browser_validation_requested`: required | skip | auto（デフォルト: `auto`）
- `browser_validation_scope`: per_issue | batch（デフォルト: per_issue）

### Phase 0.5: 実行コントラクト確定

Command Detective で `start_cmd / test_cmd / build_cmd / lint_cmd / typecheck_cmd / app_url / env_vars / seed_steps` を調査・実行確認。推測禁止。

### Phase 1: 発見・調査

2エージェント並列（リーダーは調査しない）:
- **Discovery**: 技術的問題（テスト失敗・型エラー・ビルドエラー等）
- **プロダクトアナリスト**: 目的・意義ベースの課題

リーダーは統合し優先度判断（CRITICAL > HIGH > MEDIUM）。

### Phase 2: チーム編成

ロール詳細: [references/roles.md](references/roles.md)
**固定**: Command Detective, Discovery, プロダクトアナリスト, 統合テスト, セキュリティ専門家, Codex レビュアー, 再帰的プランナー（`Skill("loop", "5m ...")`）
**条件付き**: フロントエンド, バックエンド, インフラ

### Phase 3: フェーズ別実行

A: CRITICAL修正(並列)→セキュリティゲート → B: テスト追加 → C: HIGH修正(並列)→セキュリティゲート → D: インフラ(任意) → E: レビュー・統合

Apply Non-Negotiable Rules. 特に `[CHANGE_REPORT]` 出力と `frontend_changed` 判定。

**[CHANGE_REPORT]（全実装エージェント必須・省略禁止）**:
```
[CHANGE_REPORT]
frontend_changed: yes|no
touched_files:
- <path>
ui_surfaces_changed:
- <route/component or none>
dev_server_hint:
- <command or unknown>
notes:
- <browser test 補足>
```

**frontend_changed 判定**:
- **yes**: ルーティング, DOM, 表示文言, CSS/SCSS, 状態遷移, フォーム, レイアウト, クライアント用 API contract, ブラウザ API, feature flag UI面
- **no**: バックエンド内部, CI設定, テストのみ, ドキュメントのみ
- **迷ったら yes**

**移行条件**: 全タスク Verified(Local) + CRITICAL 新規なし + セキュリティゲート PASS(A/C) + Codex ゲート PASS(E)

Phase 3 完了後、全 `[CHANGE_REPORT]` 集約。いずれか `frontend_changed: yes` → project-level yes。

### Phase 4: ブラウザ検証ゲート

**実行判定**（上から順）:
1. `required` → 実行
2. `skip` でも `frontend_changed == yes` → 実行（安全優先）
3. `auto` + `frontend_changed == yes` → 実行
4. `frontend_changed == no` + `!= required` → スキップ

コード修正禁止。詳細: [references/phase4-rules.md](references/phase4-rules.md)

**手順**: リーダーが Chrome テスターを Agent 起動 → `[CHROME_TEST_RESULT]` 返却 → `passed` で Phase 5 / `failed` で `[DEFECT_REPORT]` → Phase 3 差し戻し

**修正ループ最大 3 runs**。早期停止: 同一 failure_signature 2回連続 / 環境依存 / 外部依存で解消不能。停止時 `blocked` → エスカレーション → PR 禁止。

### Phase 5: 統合・PR 作成

**PR Gate Invariant（PR 作成前に必ず生成・検証）**:
```
[PR_READINESS_CHECK]
frontend_changed: yes|no
browser_validation_requested: required|skip|auto
chrome_test_status: passed|not_required|failed|blocked|not_run
tested_commit: <sha or n/a>
current_commit: <sha>
pr_ready: yes|no
blocking_reason: <none or reason>
```

- `tested_commit != current_commit` → stale → Phase 4 再実行
- `frontend_changed: no` + `!= required` → `not_required` で通過可
- `frontend_changed: yes` or `required` → `passed` のみ `pr_ready: yes`
- **`pr_ready: no` なら PR 作成禁止。** ブロック理由報告して停止

**PR 手順**: 全テスト → コミット・プッシュ → `gh pr create`（Browser Test Summary 含む）→ `gh pr comment`（Phase 4 詳細ログ）。テンプレート: [references/templates.md](references/templates.md)

---

## Advisory Browser Check（任意・best-effort）

Phase 4 の blocking gate が唯一の正当性保証。Advisory は根拠にならない。
`/loop` 安定環境でのみ Phase 3 中に起動可。報告先: スコープ内→リーダー直接 / スコープ外→Issue 起票+リンク / 迷う→Issue 起票しリーダー判断。

## 並列編集

責務境界での分割を優先。jj: [references/parallel-editing.md](references/parallel-editing.md)
