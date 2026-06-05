---
name: swarm-dev
description: チームを編成して開発する。プロジェクトを探索的に調査し、専門エージェントのチームで修正・テスト・レビューを実施する。
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

# swarm-dev - チーム編成・並列開発スキル

複雑な開発タスクを、専門エージェントのチームで並列実行する。

**Freedom Level**: Phase 0-3 は中（文脈に応じて調整可）、Phase 4-5 は**低**（手順厳守）。

---

## Non-Negotiable Rules

以下は例外なく守ること。

1. 全実装エージェントは作業完了時に `[CHANGE_REPORT]` を出力しなければならない。
2. いずれかのエージェントが `frontend_changed: yes` を報告した場合、リーダーは Phase 4 を実行しなければならない。
3. `frontend_changed: yes` かつ `chrome_test_status` が `passed` でない場合、**PR を作成してはならない**。
4. ブラウザツールが利用不可またはdev serverが起動できない場合、PR作成前に停止し、ブロック理由を明示報告する。
5. 成功の推測は禁止。記録されたテスト証跡のみが成功の根拠となる。
6. Phase 4 ではアプリケーションコードの修正を行ってはならない。修正が必要なら Phase 3 に差し戻す。
7. `browser_validation_requested=required` なら `frontend_changed` の値に関わらず Phase 4 を実行する。

---

## 基本概念

### 問題の優先度

| 優先度       | 定義                             |
| ------------ | -------------------------------- |
| **CRITICAL** | 動作不能・機能が完全に壊れている |
| **HIGH**     | 主要機能が動くが重大な欠陥がある |
| **MEDIUM**   | 軽微な問題・改善余地             |

### 完了の3段階

| ステージ        | 条件                                                    |
| --------------- | ------------------------------------------------------- |
| Implemented     | コードを書いた                                          |
| Verified(Local) | ローカルでテスト通過・動作確認済み                      |
| Integrated      | CI 通過 + Phase 4 ブラウザ検証 PASS（該当時）+ PR マージ済み |

Phase 3 → Phase 4 の移行は **Verified(Local)** で行う。Integrated は最終状態。

### リーダー責務原則

**リーダーはコーディネーションのみ。実作業は全てサブエージェントに委譲する。**

---

## 実行フロー

```
Phase 0:   要件確認
    ↓
Phase 0.5: 実行コントラクト確定（Command Detective）
    ↓
Phase 1:   発見・調査（Discovery + プロダクトアナリスト 並列）
    ↓
Phase 2:   チーム編成 → 即実行開始
    ↓
Phase 3:   CRITICAL修正 → テスト追加 → HIGH修正 → インフラ（自動移行）
    ↓
Phase 4:   ブラウザ検証ゲート（frontend_changed=yes 時必須）
    ↓
Phase 5:   統合・PR作成
```

---

## Phase 0: 要件確認

`$ARGUMENTS` を確認し、不明点は AskUserQuestion で聞く。

- タスクの目標・スコープ
- 以下のブラウザ検証フラグを受領・記録する（未指定なら `auto`）:
  - `browser_validation_requested`: required | skip | auto
  - `browser_validation_reason`: 理由（あれば）
  - `browser_validation_scope`: per_issue | batch（デフォルト: per_issue）

---

## Phase 0.5: 実行コントラクト確定

Command Detective をサブエージェントとして起動し、以下を調査・実行確認させる。

```yaml
start_cmd:      # ローカル起動コマンド
test_cmd:       # テスト実行コマンド
build_cmd:      # ビルドコマンド
lint_cmd:       # Lint コマンド
typecheck_cmd:  # 型チェックコマンド
app_url:        # フロントエンド URL（あれば）
env_vars:       # 必須環境変数
seed_steps:     # テストデータ投入手順
evidence:       # 根拠ファイル
verified:       # 各コマンドの実行確認結果
```

推測禁止。根拠ファイル + 実行確認をセットで報告する。

---

## Phase 1: 発見・調査

2エージェントを並列起動。リーダーは調査しない。

- **Discovery エージェント**: 技術的問題発見（テスト失敗・型エラー・ビルドエラー等）
- **プロダクトアナリスト**: 目的・意義ベースの課題発見

リーダーは両報告を統合し、優先度を判断する。

---

## Phase 2: チーム編成

ロール詳細は [ROLES.md](ROLES.md) を参照。

**固定ロール**: Command Detective, Discovery, プロダクトアナリスト, 統合テスト担当, セキュリティ専門家, Codex レビュアー, 再帰的プランナー

**条件付きロール**: フロントエンド開発者, バックエンド開発者, インフラ専門家

再帰的プランナーは常駐で起動する（`Skill("loop", "5m ...")`）。

---

## Phase 3: フェーズ別実行（自走）

```
Phase A: CRITICAL 修正（並列）
    ↓ [セキュリティゲート]
Phase B: テスト追加（並列）
    ↓
Phase C: HIGH 修正（並列）
    ↓ [セキュリティゲート]
Phase D: インフラ整備（任意）
    ↓
Phase E: セキュリティ・Codex レビュー・統合
```

### 実装エージェントの必須出力

**全実装エージェントは作業完了時に以下を TaskUpdate の description に記録する。省略禁止。**

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
- <browser test に関連する補足>
```

`frontend_changed` の判定基準:
- `yes`: ルーティング、DOM構造、表示文言、CSS/SCSS、状態遷移、フォーム、レイアウト、クライアント用 API contract、ブラウザ API、feature flag の UI 面に影響する変更
- `no`: バックエンド内部ロジック、CI設定、テストコードのみ、ドキュメントのみ
- **迷ったら `yes`**

### フェーズ移行条件

- 全実装タスクが **Verified(Local)** 状態
- CRITICAL が新規発生していない
- Phase A/C 完了時: セキュリティゲート PASS
- Phase E: Codex レビュアーゲート PASS

### リーダーの集約ルール

Phase 3 完了後、全 `[CHANGE_REPORT]` を集約する。

**Decision rule**: いずれかのエージェントが `frontend_changed: yes` を報告した場合、project-level `frontend_changed: yes` とする。

---

## Phase 4: ブラウザ検証ゲート

**実行優先順位**（上から順に評価）:
1. `browser_validation_requested == required` → 必ず実行
2. `browser_validation_requested == skip` でも `frontend_changed == yes` → 実行（安全優先）
3. `browser_validation_requested == auto` かつ `frontend_changed == yes` → 実行
4. `frontend_changed == no` かつ `browser_validation_requested != required` → スキップ

**`browser_validation_scope` の解釈**:
- `per_issue`: 当該 Issue の変更範囲だけを対象にシナリオ設計
- `batch`: バッチ内の全変更をまとめて対象にする

**Phase 4 ではアプリケーションコードの修正を行ってはならない。**

### 手順

1. リーダーが Chrome テスターエージェントを Agent ツールで起動
2. テスターは [CHROME_TEST_RESULT] を返却
3. `chrome_test_status: passed` → Phase 5 へ
4. `chrome_test_status: failed` → [DEFECT_REPORT] 生成 → Phase 3 に差し戻し

### 修正ループ

Phase 3 修正 → Phase 4 再検証の**ループ全体で最大 3 runs**。

停止条件（3 runs 未満でも停止）:
- 同一失敗が 2 回連続で再発
- 環境依存で切り分け不能
- バックエンド/外部依存の不備で frontend 単独では解消不能

停止時は `chrome_test_status: blocked` としてエスカレーション。

詳細な判定ルール・テストシナリオ設計は [references/phase4-rules.md](references/phase4-rules.md) を参照。

---

## Phase 5: 統合・PR 作成

### PR Gate Invariant

**PR 作成前に以下を生成し検証する。**

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

- `tested_commit` と `current_commit` が一致しない場合、`chrome_test_status` は `stale` 扱いとし Phase 4 を再実行する

**Decision rule**:
- `frontend_changed: no` かつ `browser_validation_requested != required` → `chrome_test_status: not_required` で通過可
- `frontend_changed: yes` または `browser_validation_requested == required` → `chrome_test_status: passed` のみ `pr_ready: yes`

**`pr_ready: no` の場合、PR を作成してはならない。** PR テキストの下書きも禁止。代わりにブロック理由を報告して停止する。

### PR 作成手順

1. テスト実行（全テスト）
2. コミット・プッシュ
3. `gh pr create` — PR body に Browser Test Summary を含める
4. `gh pr comment` — Phase 4 の詳細ログ・スクリーンショットを追記
5. **PR body の Browser Test Summary は最新の gate outcome と一致しなければならない**

アウトプットテンプレートは [TEMPLATES.md](TEMPLATES.md) を参照。

---

## Optional: Advisory Browser Check

**これは best-effort であり、品質保証の根拠にはならない。** Phase 4 の blocking gate が唯一の correctness 保証である。

`/loop` が安定動作する環境でのみ、Phase 3 中に早期フィードバック目的で起動してよい。

```
Skill("loop", "3m 全主要機能フローを探索し、発見した問題を報告する。既知バグは再報告しない。")
```

不安定な場合は無言でスキップする。Phase 4 の結果を代替しない。

**報告先の選択**: 発見した問題の性質に応じて、リーダーへの直接報告と GitHub/GitLab Issue 起票を使い分ける。

- 今回の修正スコープ内の不具合 → リーダーへ直接報告
- 今回のスコープ外だが記録すべき問題 → Issue として起票（`gh issue create` / `glab issue create`）し、リーダーにはリンクのみ報告
- 判断に迷う場合 → Issue として起票し、リーダーに判断を委ねる

---

## 並列編集プロトコル

責務境界での分割を優先する。jj の使い方は [references/parallel-editing.md](references/parallel-editing.md) を参照。

---

## 安全ルール

- リーダーは実作業しない
- main への直接 push 禁止（feature ブランチ + PR）
- 大規模削除・破壊的操作はユーザー確認必須
- 他エージェントの変更を承認なくロールバックしない
- Integrated 未達のままコミットしない
- CRITICAL は最優先で修正
- 実行コマンドはプロジェクトから読み取る（推測禁止）
