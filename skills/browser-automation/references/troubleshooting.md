# Playwright MCP トラブルシューティング

## ブラウザ起動の問題

### "Browser is already in use" エラー

**原因:** 同じ `--user-data-dir` を使うプロセスが既に起動している。

**解決策:**
1. `--isolated` を使う（推奨）
2. または既存プロセスを停止: `pkill -f "playwright-mcp"`

**注意:** `pkill` は自分のセッションの Playwright MCP も停止する。
停止後は `/mcp` で再接続が必要。

### ヘッドレスモードが効かない

**原因:** `~/.claude.json` の `mcpServers` 設定がプラグインの `.mcp.json` より優先される。

**確認手順:**
```bash
# 実際のプロセス引数を確認
ps aux | grep "playwright-mcp" | grep -v grep
```

`--headless` が引数に含まれていなければ、`~/.claude.json` の設定を確認する。

### ゾンビプロセスの蓄積

各 Claude Code セッションが playwright-mcp プロセスを起動するが、
セッション終了後も残ることがある。

```bash
# 全 playwright-mcp プロセスを確認
ps aux | grep "playwright-mcp" | grep -v grep

# 不要なプロセスを停止
pkill -f "playwright-mcp"
```

## 認証の問題

### storage-state で GitHub にログインできない

**原因:** Cookie の有効期限切れ。`user_session` Cookie の `expires` を確認する。

**再エクスポート手順:**
1. `~/.claude.json` から `--isolated` と `--storage-state` を一時的に外す
2. `--user-data-dir` で既存プロファイルを使って起動
3. GitHub にログイン
4. `page.context().storageState()` でエクスポート
5. `~/.claude/playwright-storage-state.json` を上書き
6. `~/.claude.json` を元に戻す

### storage-state に含めるべき Cookie

GitHub 認証に必要な永続 Cookie:
- `user_session`
- `__Host-user_session_same_site`
- `saved_user_sessions`
- `logged_in`
- `dotcom_user`
- `_device_id`

除外してよいもの:
- `_gh_sess`（セッション Cookie、毎回変わる）
- `_ga*`（Analytics）
- `COPILOT_*`（Copilot 関連、localStorage）

## 要素操作の問題

### 要素が見つからない

1. **ページロード待ち**: `browser_wait_for` で要素の出現を待つ
2. **snapshot で確認**: `browser_snapshot` で実際の DOM ツリーを見る
3. **iframe 内の要素**: Playwright MCP は iframe 内の要素も snapshot に含む

### クリックしても反応しない

1. **要素が画面外**: スクロールが必要。`browser_evaluate` で `element.scrollIntoView()` してから操作
2. **オーバーレイ**: モーダルやトーストが被っている。先に閉じる
3. **非同期更新**: クリック後に `browser_wait_for` で状態変化を待つ

## スクリーンショットの問題

### ヘッドレスでもスクリーンショットは撮れる

ヘッドレスモードでもブラウザはバックグラウンドでレンダリングしている。
`browser_take_screenshot` は正常に動作する。

### 特定要素だけ撮影したい

`browser_snapshot` で `ref` を取得し、`browser_take_screenshot` に
`ref` と `element` を渡す。

### フルページスクリーンショット

`fullPage: true` を指定する。ビューポート外のコンテンツも含まれる。
