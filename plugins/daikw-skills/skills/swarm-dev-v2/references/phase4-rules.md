# Phase 4 詳細ルール

## テスト深さの自動判定

| 条件 | 深さ |
|------|------|
| docs/style-only | smoke |
| route/page の変更 | smoke |
| フォーム, 認証, 決済, 検索 | detailed |
| 新規画面・新規導線 | detailed |
| バグ修正（再発防止重要） | detailed |
| high-risk ラベル付き Issue | detailed + mobile |

## frontend_changed 判定基準

**yes**: ルーティング, DOM構造, 表示文言, CSS/SCSS, 状態遷移, フォーム, レイアウト, クライアント用 API contract, ブラウザ API, feature flag の UI 面
**no**: バックエンド内部ロジック（UI contract 非影響）, CI/CD設定, テストコードのみ, ドキュメント・コメントのみ, 開発ツール設定
**迷ったら yes**

## 修正ループ制御

Phase 3 修正 → Phase 4 再検証 = 1 run。**最大 3 runs**。

### 早期停止条件

- 同一 `failure_signature` が 2 回連続再発
- 環境依存で切り分け不能
- バックエンド/API/外部依存の不備で frontend 単独では解消不能
- 要件の曖昧さで期待動作が確定しない

### 停止時の処理

1. `chrome_test_status: blocked`
2. `[DEFECT_REPORT]` にブロック理由を記録
3. エスカレーション報告を生成
4. PR 作成禁止。ユーザー承認後のみ PR 作成可

## browser_validation_requested の意味

| 値 | 意味 |
|----|------|
| required | ユーザーが明示的に要求。frontend_changed に関わらず実行 |
| skip | ユーザーが明示的に不要と指定。原則スキップ |
| auto | デフォルト。frontend_changed=yes なら実行、no ならスキップ |

### auto の実行条件

以下のいずれかで Phase 4 実行:
- いずれかのエージェントが `frontend_changed: yes`
- 変更ファイルに frontend パターンを含む（`.tsx`, `.jsx`, `.vue`, `.svelte`, `.css`, `.scss`, `.html` 等）

**`auto` を `skip` と解釈するな。** 迷ったら実行寄りに倒せ。
