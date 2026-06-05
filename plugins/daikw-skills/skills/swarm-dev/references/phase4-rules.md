# Phase 4: ブラウザ検証ゲート 詳細ルール

## テストシナリオ設計

### シナリオ生成の優先順位

1. **Issue 由来のフロー**: Issue の内容から期待されるユーザーフロー 1-3 本
2. **変更面フォーカス**: `[CHANGE_REPORT]` の route/component/state から局所シナリオ
3. **最小共通回帰**: ナビゲーション・レイアウト崩れ確認 1-2 本

「全主要フローを一通り」は原則やらない。高コストで不安定になる。

### テスト深さの自動判定

| 条件                                        | 深さ     |
| ------------------------------------------- | -------- |
| docs/style-only の変更                       | smoke    |
| route/page の変更                            | smoke    |
| フォーム、認証、決済、検索                   | detailed |
| 新規画面・新規導線                           | detailed |
| バグ修正（再発防止が重要）                   | detailed |
| high-risk ラベル付き Issue                   | detailed + mobile |

### smoke テストの範囲

- ページ表示
- 主要 CTA が押せる
- 期待する表示変化が 1 回起こる
- console error / uncaught error なし
- レイアウト崩れが致命的でない

### detailed テストの範囲

- 正常系 2-4 パターン
- 主要な異常系 1-2 パターン
- 入力検証、ローディング、成功/失敗表示
- 画面遷移前後の状態保持
- viewport を desktop / mobile で確認（該当時）

---

## frontend_changed の判定基準

### yes と判定する変更

- ルーティング（URL パス・パラメータ・リダイレクト）
- DOM 構造（HTML 要素の追加・削除・変更）
- 表示文言（ラベル・メッセージ・ツールチップ）
- CSS / SCSS / Tailwind クラス
- 状態遷移（React state、Vue reactive、Svelte store 等）
- フォーム（入力項目・バリデーション・送信処理）
- レイアウト（グリッド・フレックス・レスポンシブ）
- クライアント用 API contract（レスポンス形式・フィールド名の変更）
- ブラウザ API（localStorage、sessionStorage、cookie、URL API）
- Feature flag の UI 面への影響

### no と判定する変更

- バックエンド内部ロジック（UI contract に影響しない）
- CI/CD 設定
- テストコードのみ
- ドキュメント・コメントのみ
- 開発ツール設定（ESLint, Prettier 等）

### 迷ったら yes

---

## 修正ループの制御

### ループ定義

Phase 3 修正 → Phase 4 再検証を 1 run とカウント。**最大 3 runs**。

### 早期停止条件

以下のいずれかに該当したら、3 runs 未満でも停止:

- 同一 `failure_signature` が 2 回連続で再発
- 原因が環境依存で切り分け不能
- バックエンド / API / 外部依存の不備で frontend agent 単独では解消不能
- 要件の曖昧さで期待動作が確定しない

### 停止時の処理

1. `chrome_test_status: blocked` とする
2. `[DEFECT_REPORT]` にブロック理由を記録
3. エスカレーション報告を生成（TEMPLATES.md 参照）
4. **PR は作成してはならない。** エスカレーション報告のみ生成する
5. ユーザーに判断を委ねる（ユーザー承認後のみ PR 作成可）

---

## browser_validation_requested の意味定義

| 値       | 意味                                                                 |
| -------- | -------------------------------------------------------------------- |
| required | ユーザーが明示的にブラウザ検証を要求。frontend_changed に関わらず実行 |
| skip     | ユーザーが明示的に不要と指定。原則スキップ                           |
| auto     | デフォルト。frontend_changed=yes なら実行、no ならスキップ           |

### auto の厳密な実行条件

`auto` の場合、以下のいずれかに該当すれば Phase 4 を実行する:

- いずれかのエージェントが `frontend_changed: yes` を報告
- 変更ファイルに frontend-facing パターンが含まれる（`.tsx`, `.jsx`, `.vue`, `.svelte`, `.css`, `.scss`, `.html` 等）

**`auto` を `skip` と解釈してはならない。** 判断に迷ったら実行寄りに倒す。

---

## スクリーンショット

Playwright MCP（`mcp__playwright__browser_take_screenshot`）を使う。`filename` 指定でファイルに直接保存される。

```
mcp__playwright__browser_take_screenshot
  filename: "screenshot.png"
  type: "png"          # or "jpeg"
  fullPage: true       # ページ全体
```

- 失敗時: 1-2 枚必須（`[DEFECT_REPORT]` の `evidence` にパスを記載）
- 成功時: 省略可
- 大きな UI 変更時: before/after が有効
- JPG 変換が必要な場合: `sips -s format jpeg <file>.png --out <file>.jpg`
- GitHub PR/Issue への添付: `/uploading-images-via-browser` スキルを使う
