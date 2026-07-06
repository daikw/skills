# 認証が必要なサービスへのアクセス

## 仕組み

`--storage-state` で Cookie と localStorage を注入する。
サービスごとに認証方式が異なるため、必要な Cookie も異なる。

## 認証の難易度（目安）

| タイプ | 例 | storage-state との相性 |
|--------|-----|----------------------|
| セッション Cookie 方式 | GitHub, GitLab | 良好。Cookie エクスポートで安定動作 |
| 複数トークン + リフレッシュ | Google, Microsoft | 不安定。トークンが頻繁に失効する |
| IP / デバイス紐付き | 一部の社内ツール | 環境依存。ヘッドレスだと「新しいデバイス」扱いになりうる |

storage-state で安定しないサービスは `--user-data-dir` で永続プロファイルを使う方が確実。
ただし同時起動できないトレードオフがある。

## 初回認証セットアップ

ヘッドレスモードではログインフォームの操作やOAuth リダイレクト、2FA の入力ができない。
**初回認証は必ずヘッドモード（ブラウザ表示あり）で行う。**

### 手順

1. **`~/.claude.json` から `--headless` を一時的に外す**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "playwright-mcp",
      "args": [
        "--isolated",
        "--storage-state",
        "/Users/<username>/.claude/playwright-storage-state.json"
      ]
    }
  }
}
```

（`playwright-mcp` は `pnpm add -g @playwright/mcp@0.0.77` 等で事前インストール済みのバイナリ。`npx` は使わない — セットアップ手順は SKILL.md の「Playwright MCP 環境セットアップ」参照）

2. **Claude Code を再起動**（設定反映のため）

3. **`browser_navigate` でログインページを開く**
   - ブラウザウィンドウが表示される
   - ユーザーが手動でログイン操作（ID/パスワード入力、OAuth、2FA 等）を実施

4. **ログイン完了後、storage-state をエクスポート**

```
mcp__playwright__browser_run_code:
  code: |
    async (page) => {
      const state = await page.context().storageState();
      return JSON.stringify(state);
    }
```

5. **結果の JSON を `~/.claude/playwright-storage-state.json` に保存**
   - 不要な Cookie（Analytics、一時セッション等）は除外してよい
   - 認証に必要な永続 Cookie だけ残す

6. **`--headless` を戻して Claude Code を再起動**

### 既存プロファイルがある場合

過去に `--user-data-dir` で認証済みプロファイルがあるなら:

1. `~/.claude.json` を一時的に `--user-data-dir <path>` 方式に戻す
2. Claude Code を再起動
3. `browser_navigate` でサービスにアクセスしてログイン済みか確認
4. `page.context().storageState()` でエクスポート
5. `~/.claude.json` を `--isolated --headless --storage-state` に戻す

## 複数サービスの認証を管理する

storage-state は 1 ファイルに複数サービスの Cookie を含められる。
エクスポート時に全サービスの Cookie がまとめて出力される。

**マージ手順:**
サービス A でエクスポートした JSON と、サービス B の JSON の
`cookies` 配列を手動でマージする。`origins`（localStorage）も同様。

```json
{
  "cookies": [
    { "name": "user_session", "domain": "github.com", "..." : "..." },
    { "name": "session_token", "domain": "example.com", "..." : "..." }
  ],
  "origins": []
}
```

## トラブルシューティング

### ログイン状態が維持されない

1. Cookie の `expires` を確認 — 期限切れなら再エクスポート
2. `--isolated` なしで同じ URL にアクセスしてログインできるか確認
3. サービスがブラウザフィンガープリントを見ている場合、
   `--isolated` のクリーンプロファイルが「新しいデバイス」と判定される可能性あり
   → `--user-agent` で固定のユーザーエージェントを設定する

### 2FA / MFA を求められる

1. `--headless` を外して Claude Code を再起動
2. `browser_navigate` でサービスを開き、手動で 2FA を通す
3. 「このデバイスを信頼する」にチェックして Cookie に記録させる
4. `page.context().storageState()` で再エクスポート
5. `--headless` を戻す

### CAPTCHA が表示される

- ヘッドレスブラウザは bot 検出されやすい
- `--no-sandbox` は逆効果（フィンガープリントが異常になる）
- 対策: `--user-agent` で通常のブラウザと同じ UA を設定する
- それでもダメな場合は `--headless` を外して手動で通す
