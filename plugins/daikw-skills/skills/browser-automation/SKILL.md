---
name: browser-automation
description: "Playwright MCP を使ったブラウザ自動化をガイドする。E2E テスト、スクリーンショット撮影、認証済みサービスへのアクセス、環境セットアップを支援する。「ブラウザ操作」「E2E テスト」「ブラウザテスト」「認証」などのリクエストで使用。"
---

# Browser Automation with Playwright MCP

Playwright MCP を使ったブラウザ自動化ガイド。ローカル Web アプリのテスト、外部サービスへの認証済みアクセス、スクリーンショット撮影などに対応する。

Freedom Level: **中** — 基本パターンに従いつつ、対象に応じて柔軟に調整する。

## Playwright MCP vs claude-in-chrome の使い分け

| 状況 | 使うもの |
|---|---|
| クリーン環境からの自動化・ヘッドレス実行・E2E テスト | **Playwright MCP**（このスキル） |
| ユーザーの実ブラウザセッション・既存ログインをそのまま使いたい | **claude-in-chrome** |

storage-state のエクスポート・IAP 認証等、このスキルの手順は「新規 BrowserContext + Cookie 注入」を前提にしている。既にログイン済みの実ブラウザで完結する軽微な操作（既存タブの内容確認、簡単なクリック等）は claude-in-chrome の方が手早い。逆に、SPA（Slack 等）の一部 UI は `isTrusted` イベント判定が厳しく、Playwright MCP の `ClipboardEvent` 系操作が無反応になることがある（実戦で確認済み）。その場合も claude-in-chrome へのフォールバックを検討する。

## Playwright MCP 環境セットアップ

### 推奨設定（`~/.claude.json`）

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "@playwright/mcp@0.0.77",
        "--isolated",
        "--headless",
        "--storage-state",
        "/Users/<username>/.claude/playwright-storage-state.json"
      ]
    }
  }
}
```

**フラグの意味:**
- `--isolated` — MCP セッションごとに新しい BrowserContext を作成。複数セッションから同時利用可能（推奨）。永続プロファイルは使わず、`--storage-state` から Cookie を注入する
- `--headless` — ブラウザウィンドウを表示しない。macOS ではデフォルト headed なので明示指定が必要
- `--storage-state` — 認証済み Cookie/localStorage を BrowserContext 作成時に注入。`--isolated` と併用することで、クリーンな環境 + 認証済み状態を実現する

### 設定の優先順位

`~/.claude.json` の `mcpServers` > プラグインの `.mcp.json`。
プラグイン側を編集しても `~/.claude.json` に同名キーがあるとそちらが優先される。

### storage-state のエクスポート

認証済みブラウザセッションがある状態で:

```
mcp__playwright__browser_run_code:
  code: |
    async (page) => {
      await page.context().storageState({
        path: '/Users/<username>/.claude/playwright-storage-state.json'
      });
    }
```

`storageState({ path })` で直接ファイルに書き出せる（`require('fs')` は使えない）。
Cookie の有効期限が切れたら同じ手順で再エクスポートする。

**重要:** storage-state は自動保存されない。ログイン後に明示的にエクスポートしないと保存されない。

### IAP（Identity-Aware Proxy）認証サイトへのアクセス

GCP IAP で保護されたサイト（例: `tools.gcp.<your-org>.dev`）にアクセスするには、
IAP のセッション Cookie（`GCP_IAP_UID`, `__Host-GCP_IAP_AUTH_TOKEN_*`）が storage-state に含まれている必要がある。

**初回セットアップ手順:**

1. `~/.claude.json` を一時的に変更し、headed + 非 isolated モードで起動:
   ```json
   "args": ["@playwright/mcp@0.0.77", "--storage-state", "<path>"]
   ```
2. Claude Code を再起動
3. `browser_navigate` で IAP サイトを開く → Google ログイン画面がブラウザに表示される
4. ブラウザ上で手動ログイン
5. **ログイン後、`browser_run_code` で storage-state をエクスポート**（上記の手順）
6. `~/.claude.json` を元の `--isolated --headless --storage-state` に戻す
7. Claude Code を再起動

**注意点:**
- `--isolated` は MCP セッションごとに新しい BrowserContext を作り、`--storage-state` の Cookie をロードする
- `--isolated` なし（永続プロファイルモード）では Cookie がディスク上のプロファイルに自動保存されるが、複数セッションで競合する
- IAP Cookie の有効期限は約1時間（リフレッシュあり）。期限切れ時は上記手順を再実行する
- 古い Playwright プロセスが残っていると新しいセッションが起動できないことがある: `pkill -f "playwright-mcp"` で掃除する

## Reconnaissance-Then-Action

**必ず「観察→操作→確認」の順で進める。** 盲目的にセレクタを推測しない。

```
1. navigate  — 対象ページを開く
2. snapshot  — アクセシビリティツリーを取得（DOM 構造の把握）
3. action    — click / fill_form / type 等（snapshot の ref を使う）
4. screenshot — 結果を視覚的に確認
```

## 基本ツールの使い分け

| ツール | 用途 |
|--------|------|
| `browser_navigate` | URL を開く |
| `browser_snapshot` | アクセシビリティツリー取得。操作対象の `ref` を特定 |
| `browser_click` | `ref` 指定でクリック |
| `browser_fill_form` | フォーム入力 |
| `browser_type` | キーボード入力 |
| `browser_take_screenshot` | スクリーンショット撮影（ヘッドレスでも動作） |
| `browser_evaluate` | 任意の JavaScript 実行 |
| `browser_run_code` | Playwright API を直接実行（高度な操作向け） |
| `browser_wait_for` | 要素出現やナビゲーション完了を待つ |

## リファレンス

- E2E テスト戦略・シナリオ設計: [references/e2e-testing.md](references/e2e-testing.md)
- 認証が必要なサービス: [references/authenticated-services.md](references/authenticated-services.md)
- 一般的なトラブルシューティング: [references/troubleshooting.md](references/troubleshooting.md)

## よくある問題

- **"Browser is already in use"** → `--isolated` が未設定、または別プロセスが同じプロファイルをロック中
- **認証が必要なサービスにアクセスできない** → storage-state の Cookie が期限切れ。再エクスポートする
- **要素が見つからない** → `browser_wait_for` で待機、または snapshot で実際の DOM を確認
- **ヘッドレスなのにウィンドウが出る** → `~/.claude.json` の設定が優先されているか確認。プラグイン `.mcp.json` の編集だけでは反映されない
