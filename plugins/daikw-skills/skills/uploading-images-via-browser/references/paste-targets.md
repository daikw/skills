# Paste Target DOM Reference

サービスごとの paste-to-upload 対応 textarea / contenteditable 要素のセレクタと注意点。

`browser_snapshot` で実際の DOM を確認し、以下をガイドとして使う。UI 変更で壊れた場合は snapshot ベースで調整する。

---

## GitHub

GitHub は textarea ベースのマークダウンエディタ。paste すると `user-attachments/assets/<uuid>` に自動アップロードされ、`<img>` タグが挿入される。

### セレクタ

| ページ | セレクタ | 備考 |
|--------|----------|------|
| New Issue (body) | `textarea[placeholder*="Type your description"]` | |
| Issue/PR Comment | `textarea[placeholder*="Leave a comment"]` | |
| PR Review comment | `.js-comment-field` | inline review |
| Edit Comment | `textarea.js-comment-field` | 編集モード |
| Discussions | `textarea[placeholder*="Type your description"]` | Issue と同じ |

### フォールバック戦略

```javascript
const ta = document.querySelector('textarea[placeholder*="Type your description"]')
        || document.querySelector('textarea[placeholder*="Leave a comment"]')
        || document.querySelector('.js-comment-field');
```

### 注意点

- `<input type="file">` は存在しない。paste event が唯一の方法
- paste 後、GitHub の JS が非同期でアップロード処理を行う。3 秒の待機が必要
- `dispatchEvent` が `false` を返すのは正常（`preventDefault` で処理済み）
- アップロード完了で textarea の値が `<img ... src="https://github.com/user-attachments/assets/..." />` に差し替わる

---

## GitLab

GitLab もマークダウン textarea ベース。paste すると `/uploads/<hash>/<filename>` にアップロードされ、`![image](/uploads/...)` が挿入される。

### セレクタ

| ページ | セレクタ | 備考 |
|--------|----------|------|
| MR/Issue Comment | `textarea#note-body` | メインのコメント欄 |
| Issue Description | `textarea.js-gfm-input` | GFM 対応 textarea |
| New Issue body | `textarea[data-testid="issuable-form-description-field"]` | 新 UI |
| Wiki editor | `textarea.js-gfm-input` | |
| Snippet description | `textarea#personal_snippet_description` | |

### フォールバック戦略

```javascript
const ta = document.querySelector('textarea#note-body')
        || document.querySelector('textarea.js-gfm-input')
        || document.querySelector('textarea[data-testid="issuable-form-description-field"]');
```

### 注意点

- セルフホスト GitLab ではセレクタが異なる場合がある
- paste 後の待機は 3-5 秒推奨（セルフホストは遅い場合がある）
- アップロード完了で `![image](/uploads/<hash>/image.png)` 形式のマークダウンが挿入される

---

## Notion

Notion は contenteditable ベースのブロックエディタ。paste すると Notion の内部ストレージにアップロードされる。

### セレクタ

| ページ | セレクタ | 備考 |
|--------|----------|------|
| ページ本文 | `div.notion-page-content [contenteditable="true"]` | ブロック単位 |
| フォーカス中のブロック | `div[data-block-id][contenteditable="true"]` | 編集中のブロック |
| コメント | `div.notion-overlay-container [contenteditable="true"]` | コメントパネル |

### フォールバック戦略

```javascript
const el = document.querySelector('div[data-block-id][contenteditable="true"]')
        || document.querySelector('.notion-page-content [contenteditable="true"]');
```

### 注意点

- **contenteditable** なので `ClipboardEvent` の構築が textarea と少し異なる場合がある
- Notion はブロック単位の編集。フォーカス位置に画像ブロックが挿入される
- SPA のためページ遷移後にセレクタが変わることがある。`browser_snapshot` で都度確認推奨
- paste 後の待機は 3-5 秒推奨

---

## Slack (Web)

Slack Web はリッチテキストエディタ（contenteditable）。paste で画像がメッセージに添付される。

### セレクタ

| ページ | セレクタ | 備考 |
|--------|----------|------|
| メッセージ入力 | `div.ql-editor[contenteditable="true"]` | Quill ベース |
| メッセージ入力 (新UI) | `div[data-qa="message_input"] [contenteditable="true"]` | |
| スレッド返信 | `div[data-qa="message_input"] [contenteditable="true"]` | スレッドパネル内 |

### フォールバック戦略

```javascript
const el = document.querySelector('div.ql-editor[contenteditable="true"]')
        || document.querySelector('div[data-qa="message_input"] [contenteditable="true"]');
```

### 注意点

- **contenteditable** ベース。textarea ではない
- Slack は頻繁に UI を更新するため、セレクタの寿命が短い
- 画像は Slack のファイルストレージにアップロードされる
- ワークスペースによってはファイルアップロードが制限されている場合がある
- paste 後、ファイルプレビューが表示されるまで 2-3 秒待つ

---

## Google Docs

Google Docs は独自の canvas ベースエディタだが、paste event は受け付ける。

### セレクタ

| ページ | セレクタ | 備考 |
|--------|----------|------|
| ドキュメント本文 | `div.kix-appview-editor` | メインエディタ領域 |
| 入力受付要素 | `iframe.docs-texteventtarget-iframe` 内の `body` | イベントターゲット |

### フォールバック戦略

```javascript
// Google Docs はイベントターゲットが iframe 内にある
const iframe = document.querySelector('iframe.docs-texteventtarget-iframe');
const el = iframe?.contentDocument?.body;
```

### 注意点

- Google Docs は **iframe 内の body** にイベントを送る必要がある
- `mcp__playwright__browser_run_code` の `page.evaluate` ではクロスオリジン iframe にアクセスできない場合がある
- `upload_image` の `coordinate` 方式（ドラッグ＆ドロップ）の方が確実な場合がある（ただし claude-in-chrome の upload_image はバグあり）
- 画像は Google のストレージにアップロードされる
- **難易度が高い**。動かない場合はフォールバックとして手動操作を案内する

---

## 汎用パターン: CKEditor / TipTap / ProseMirror

多くの Web アプリがこれらのリッチテキストエディタを使っている。

### CKEditor

```javascript
const el = document.querySelector('.ck-editor__editable[contenteditable="true"]');
```

### TipTap / ProseMirror

```javascript
const el = document.querySelector('.ProseMirror[contenteditable="true"]')
        || document.querySelector('.tiptap[contenteditable="true"]');
```

### 注意点

- contenteditable ベースのエディタは全て同じ paste event 方式で動作する
- エディタによっては `paste` ではなく `drop` イベントの方が確実な場合がある
- カスタムエディタの場合は `browser_snapshot` で DOM を確認してセレクタを特定する

---

## paste event の構築パターン

### textarea 向け（GitHub, GitLab）

```javascript
const file = new File([blob], filename, { type: mimeType });
const dt = new DataTransfer();
dt.items.add(file);
const evt = new ClipboardEvent('paste', {
  bubbles: true,
  cancelable: true,
  clipboardData: dt
});
element.focus();
element.dispatchEvent(evt);
```

### contenteditable 向け（Notion, Slack, CKEditor 等）

```javascript
const file = new File([blob], filename, { type: mimeType });
const dt = new DataTransfer();
dt.items.add(file);
const evt = new ClipboardEvent('paste', {
  bubbles: true,
  cancelable: true,
  clipboardData: dt
});
element.focus();
// contenteditable では selection を設定してからの paste が安定する
const sel = window.getSelection();
const range = document.createRange();
range.selectNodeContents(element);
range.collapse(false); // カーソルを末尾に
sel.removeAllRanges();
sel.addRange(range);
element.dispatchEvent(evt);
```
