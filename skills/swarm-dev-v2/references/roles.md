# ロール定義

## Chrome テスター（Phase 4 専用・都度起動）

### 起動時に受け取る情報

- 実行コントラクト（`start_cmd`, `app_url`）
- 集約済み `[CHANGE_REPORT]`
- Issue 内容（あれば）
- `browser_validation_requested` の値

### テストシナリオ設計

1. Issue 由来のユーザーフロー 1-3 本
2. `[CHANGE_REPORT]` の変更対象から局所シナリオ
3. 共通回帰（ナビゲーション・レイアウト崩れ）1-2 本

「全主要フローを一通り」はやらない。

### テスト深さ（デフォルト: smoke）

**smoke**: ページ表示, 主要 CTA 動作, 期待する表示変化1回, console error なし

**detailed に上げる条件**: 新規画面・新規導線 / フォーム・認証・決済・検索 / バグ修正で再発防止が重要 / ユーザー影響が大きい UI 変更

detailed: 正常系 2-4, 主要異常系 1-2, 入力検証, ローディング, viewport 確認

### 必須出力: [CHROME_TEST_RESULT]

```
[CHROME_TEST_RESULT]
tested_commit: <sha>
chrome_tools_available: yes|no
dev_server_status: started|already_running|failed
test_target_url: <url>
test_depth: smoke|detailed
scenarios_run: <count>
chrome_test_status: passed|failed|blocked
evidence:
- <scenario: result, observation>
```

`dev_server_hint` は補助情報。起動は常に実行コントラクトの `start_cmd` を正とする。

### 失敗時: [DEFECT_REPORT]

```
[DEFECT_REPORT]
failure_signature: <失敗を一意に識別する短い文字列>
severity: blocker|major|minor
repro_steps: <手順>
expected: <期待動作>
actual: <実際の動作>
scope: <影響範囲>
evidence: <スクリーンショットパス等>
suggested_owner: frontend|backend|infra|unknown
```

### スクリーンショット

Playwright MCP（`mcp__playwright__browser_take_screenshot`）を使う。`filename` 指定でファイルに直接保存される。

```
mcp__playwright__browser_take_screenshot
  filename: "223_scan_error_banner.png"
  type: "png"          # or "jpeg"
  fullPage: true       # ページ全体
```

- 失敗時: 1-2 枚必須（`[DEFECT_REPORT]` の `evidence` にパスを記載）
- 成功時: 省略可
- 大きな UI 変更時: before/after が有効
- JPG 変換が必要な場合: `sips -s format jpeg <file>.png --out <file>.jpg`
- GitHub PR/Issue への添付: `/uploading-images-via-browser` スキルを使う

---

## 再帰的プランナー（常駐）

計画を常に最新に保つ。確認内容:
1. 当初計画の漏れ・新規問題はないか
2. 優先度変更が必要か
3. 依存関係が変わっていないか
4. Codex に相談すべき設計問題があるか

実施タイミング: 新問題発見時、フェーズ移行時。

---

## セキュリティ専門家

パターンマッチングではなく、コードを読み推論せよ。

検査フロー: コンテキスト把握 → 発見 → 多段階検証（誤検出除外）→ 重要度 + 信頼度付与

ゲートルール:
- CRITICAL/HIGH 1件以上 → フェーズ移行ブロック
- MEDIUM は記録のみ
- 人間の承認なしに修正を適用するな

---

## Codex レビュアー

各フェーズ完了時に実施。5項目中 0 fail = PASS。

```
[ ] セキュリティ: セキュリティ専門家のゲート PASS
[ ] 設計整合: 既存アーキテクチャ・型定義との一貫性
[ ] テスト妥当性: カバレッジ・品質・エッジケース
[ ] 実装アプローチ: より良い方法がないか
[ ] リグレッション: 既存機能を壊していないか
```

---

## Advisory Browser Tester（任意・best-effort）

Phase 3 中の早期フィードバック用。品質保証の根拠にはならない。

報告先:
| 状況 | 報告先 |
|------|--------|
| スコープ内の不具合 | リーダーへ直接報告 |
| スコープ外だが記録すべき | Issue 起票（`gh issue create` / `glab issue create`, ラベル `browser-test`）+ リンク報告 |
| 判断に迷う | リーダーへ報告し判断を委ねる |

起票前に `gh issue list --label browser-test` で重複確認。`gh`/`glab` 不可ならリーダーへ直接報告にフォールバック。

報告フォーマット:
```
ラウンド N 完了
【既知バグ（変化なし）】- #N: 内容
【新規発見】- #新: 内容 → Issue #XX として起票済み / リーダー判断待ち
【確認済み修正】- #N: 内容
```
