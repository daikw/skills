---
name: uploading-images-via-browser
description: "Uploads images and screenshots to web forms (GitHub Issues/PRs, GitLab MRs, Notion, Slack, etc.) via Playwright MCP using ClipboardEvent paste injection. Use when the user asks to attach screenshots to issues, paste images into PR comments, or upload images to any web textarea that supports paste-to-upload."
---

# uploading-images-via-browser

Playwright MCP で Web フォームの textarea/contenteditable に画像を paste event で注入するスキル。GitHub/GitLab/Notion 等の paste-to-upload 対応サイトで動作する。

Freedom Level: **中** — 推奨パターンに従いつつ、サイトごとのセレクタは文脈に応じて調整する。

## 前提

- **Playwright MCP の基本操作は [browser-automation](../browser-automation/SKILL.md) スキルを参照**
  - 環境セットアップ、storage-state、認証、基本ツールの使い方
- 対象サイトにログイン済みの storage-state が設定されていること
- アップロードする画像ファイルが `$HOME/tmp/uploads` 配下または `.playwright-mcp/` 配下にあること（Playwright MCP のファイルアクセス制限）

## なぜ paste event か

GitHub をはじめ多くのモダン Web アプリは `<input type="file">` を持たず、paste/drop イベントで画像をアップロードする UI になっている。そのため通常のファイル選択ダイアログ経由（`browser_file_upload`）では動かない。

代わりに `ClipboardEvent('paste')` に File を入れて dispatch することで、アプリの paste ハンドラを直接発火させる。サイト側がアップロード処理を行い、マークダウンリンクや `<img>` タグを自動挿入する。

## 手順

### Step 1: 対象ページへナビゲート

```
mcp__playwright__browser_navigate → url: "https://github.com/{owner}/{repo}/issues/new"
```

### Step 2: textarea セレクタを確認

サービス別のセレクタは [references/paste-targets.md](references/paste-targets.md) を参照。

新しいサイトの場合は `browser_snapshot` で DOM を確認してセレクタを特定する。

### Step 3: 画像を base64 化してスクリプトを生成

`browser_run_code` 内では Node.js の `require`/`import` が使えないため、Bash 側で base64 を埋め込んだ JS ファイルを生成する。

```bash
B64=$(base64 -i /path/to/image.png | tr -d '\n')  # macOS
# B64=$(base64 -w0 /path/to/image.png)  # Linux

cat > $HOME/tmp/uploads/upload-script.js << JSEOF
async (page) => {
  const b64 = '${B64}';
  const result = await page.evaluate(async (b64) => {
    // base64 → File
    const binaryStr = atob(b64);
    const bytes = new Uint8Array(binaryStr.length);
    for (let i = 0; i < binaryStr.length; i++) bytes[i] = binaryStr.charCodeAt(i);
    const blob = new Blob([bytes], { type: 'image/png' });
    const file = new File([blob], 'screenshot.png', { type: 'image/png' });

    // サイト別セレクタ（フォールバック付き）
    const selectors = [
      'textarea[placeholder*="Type your description"]',   // GitHub New Issue
      'textarea[placeholder*="Leave a comment"]',          // GitHub Comment
      '.js-comment-field',                                 // GitHub Review
      'textarea#note-body',                                // GitLab
      'textarea.js-gfm-input',                             // GitLab
      '.ProseMirror[contenteditable="true"]',              // Notion/TipTap
      'div.ql-editor[contenteditable="true"]',             // Quill (Slack)
    ];
    let el = null;
    let matchedSelector = '';
    for (const s of selectors) {
      el = document.querySelector(s);
      if (el) { matchedSelector = s; break; }
    }
    if (!el) return { error: 'No editable element found' };

    // フォーカス設定（contenteditable は selection も必要）
    el.focus();
    if (el.getAttribute('contenteditable') === 'true') {
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(false);
      sel.removeAllRanges();
      sel.addRange(range);
    }

    // paste event dispatch
    const dt = new DataTransfer();
    dt.items.add(file);
    const evt = new ClipboardEvent('paste', {
      bubbles: true,
      cancelable: true,
      clipboardData: dt
    });
    const dispatched = el.dispatchEvent(evt);

    // サイトのアップロード処理待ち
    await new Promise(r => setTimeout(r, 3000));

    return {
      success: true,
      dispatched,
      matchedSelector,
      fileSize: file.size,
      resultPreview: (el.value || el.innerHTML || '').substring(0, 300)
    };
  }, b64);
  return JSON.stringify(result, null, 2);
}
JSEOF
```

### Step 4: スクリプトを実行

```
mcp__playwright__browser_run_code → filename: "$HOME/tmp/uploads/upload-script.js"
```

**成功判定:**
- `success: true` かつ `matchedSelector` が埋まっている
- `dispatched: false` は正常（サイト側が `preventDefault` で処理済み）
- `resultPreview` に `<img ... src="https://...">` や `![image](...)` 形式のマークダウンが含まれていれば、サーバーアップロード成功

### Step 5: 結果を視覚確認

```
mcp__playwright__browser_take_screenshot → filename: "upload-result.png", type: "png"
```

## 動作確認済みサービス

| サービス | 状態 | 備考 |
|---------|------|------|
| **GitHub** | ✅ 完全動作 | `user-attachments/assets/<uuid>` にアップロードされる |
| **Quill** (Slack エディタ同系) | ✅ 完全動作 | `data:image/png;base64,...` として挿入 |
| **ProseMirror** | ✅ イベント到達 | 画像対応プラグインがあれば動作 |
| **GitLab** | 未テスト | セレクタは準備済み |
| **Notion** | 未テスト | セレクタは準備済み（contenteditable） |
| **Google Docs** | ⚠️ 難しい | iframe 内の body が対象でクロスオリジン制約 |

詳細は [references/paste-targets.md](references/paste-targets.md)。

## トラブルシューティング

### "No editable element found"

- ページロード完了前に実行された可能性 → `browser_wait_for` で textarea 出現を待つ
- SPA で非同期にエディタが生成されるサイト → `page.waitForTimeout(3000)` を追加
- セレクタが変わった → `browser_snapshot` で実際の DOM を確認

### paste event は通るが画像 URL に差し替わらない

- サイトの JS が paste event を拾えていない → `focus()` 後に `dispatchEvent` しているか確認
- 待機時間が短い → `setTimeout(r, 3000)` を 5000-10000 に延長
- サイトが画像アップロードを非対応 → 画像ハンドラのないエディタ（例: ProseMirror 基本デモ）では動かない

### ファイルアクセス拒否

- `browser_run_code` 経由の `page.evaluate` は OS ファイルにアクセスしない（base64 は Bash 側で埋め込む）
- 画像ファイル自体は Playwright MCP の許可ディレクトリ（`$HOME/tmp/uploads` 配下等）に置く

## 既知の制限

- **`browser_file_upload` は使えない**: GitHub などの新 UI には `<input type="file">` が存在しないため
- **`claude-in-chrome` の `upload_image` は壊れている**: MCP コードパスに `messages` プロパティが渡されないバグあり。詳細は `~/tmp/tmp/chrome-upload-image-investigation.md` 参照
- **localhost HTTP → HTTPS サイト fetch**: Mixed Content でブロックされるため、画像配信経由の手法は使えない
