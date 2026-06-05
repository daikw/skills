# ロール詳細ガイド

## Chrome テスター（Phase 4 専用）

Phase 4 でリーダーが Agent ツールで都度起動する。常駐ロールではない。

### 起動時に受け取る情報

リーダーから以下を渡される:
- 実行コントラクト（`start_cmd`, `app_url`）
- 集約済み `[CHANGE_REPORT]`（変更ファイル・UI サーフェス一覧）
- Issue の内容（あれば）
- `browser_validation_requested` の値

### テストシナリオ設計

1. Issue から期待されるユーザーフロー 1-3 本を抽出
2. `[CHANGE_REPORT]` の変更対象（route/component/state）から局所シナリオを追加
3. 共通回帰（ナビゲーション・レイアウト崩れ）を 1-2 本追加
4. 「全主要フローを一通り」は原則やらない

### テスト深さ

**デフォルト: smoke**

| 深さ     | 内容                                                                     |
| -------- | ------------------------------------------------------------------------ |
| smoke    | ページ表示、主要 CTA 動作、期待する表示変化1回、console error なし       |
| detailed | 正常系 2-4 パターン、主要異常系 1-2、入力検証、ローディング、viewport 確認 |

detailed に上げる条件:
- 新規画面・新規導線
- フォーム、認証、決済、検索、複雑な状態遷移
- バグ修正で再発防止が重要
- ユーザー影響が大きい UI 変更

### 必須出力

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

`dev_server_hint` は補助情報。起動コマンドは常に実行コントラクトの `start_cmd` を正とする。

失敗時は追加で `[DEFECT_REPORT]` を生成:

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

- 失敗時: 関連スクリーンショット 1-2 枚は必須
- 成功時: 添付なしでも可
- 大きな UI 変更時: before/after が有効

---

## 再帰的プランナー（常駐）

計画を常に最新の状態に保つ。Resident Boot Sequence で起動。

### 確認内容

1. 当初計画の漏れ・新規発見の問題はないか
2. 優先度の変更が必要か
3. タスクの依存関係が変わっていないか
4. Codex に相談すべき設計上の問題があるか

### 実施タイミング

- 実装中に新たな問題が発見された時
- フェーズ移行のタイミング

---

## セキュリティ専門家

ルールベースのパターンマッチングではなく、**人間のセキュリティ研究者のように**コードを読み推論する。

### 検査フロー

Phase A/C 完了時と Phase E で実施。

1. コンテキスト把握: コンポーネント間の相互作用・データフローを追跡
2. 発見 → 多段階検証: 各検出結果を自ら再検証し、誤検出を除外
3. 重要度 + 信頼度の付与

### ゲートルール

- CRITICAL / HIGH が 1 件以上 → **要対応**（フェーズ移行をブロック）
- MEDIUM は記録のみ
- 人間の最終承認なしに修正を適用しない

---

## Codex レビュアーのゲートチェック

各フェーズ完了時に実施。**5項目中 0 fail = PASS、1以上 = 要対応**。

```
[ ] セキュリティ: セキュリティ専門家のゲート判定が PASS
[ ] 設計整合: 既存アーキテクチャ・型定義との一貫性
[ ] テスト妥当性: カバレッジ・テスト品質・エッジケース
[ ] 実装アプローチ: より良い方法がないか
[ ] リグレッション: 既存機能を壊していないか

結果: PASS / 要対応（項目名: 内容）
```

---

## Advisory Browser Tester（任意・best-effort）

Phase 3 中に `/loop` で早期フィードバックを得るための任意ロール。品質保証の根拠にはならない。

### 報告先の使い分け

| 状況                                 | 報告先                   |
| ------------------------------------ | ------------------------ |
| 今回の修正スコープ内の不具合         | リーダーへ直接報告       |
| スコープ外だが記録すべき問題         | Issue 起票 + リンク報告  |
| 判断に迷う場合                       | リーダーへ報告し判断を委ねる |

Issue 起票時は `gh issue create` / `glab issue create` を使い、ラベル `browser-test` を付与する。起票前に既存 Issue を検索し、重複を避ける（`gh issue list --label browser-test`）。`gh` / `glab` が使えない環境ではリーダーへの直接報告にフォールバックする。

### 報告フォーマット

```
ラウンド N 完了

【既知バグ（変化なし）】
- #3: ログイン後リダイレクトが遅い（継続中）

【新規発見】
- #新: スキャン結果画面でスクロールするとヘッダーが崩れる
  再現手順: ...
  → Issue #XX として起票済み / リーダー判断待ち

【確認済み修正】
- #1: スキャン送信モーダルが正常に閉じることを確認
```
