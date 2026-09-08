# Playwright MCPのセットアップ

この資料は新規導入・設定変更が必要な場合だけ使う。
利用中のブラウザツールが依頼を満たすなら、そのまま作業を続ける。

## インストールと設定先

インストール済みの `playwright-mcp --help` と利用するハーネスの設定仕様を確認する。
未導入なら公式の [Playwright MCP repository](https://github.com/microsoft/playwright-mcp) とregistryからパッケージ名・固定version・配布元を確認し、適用されるsupply-chain方針で導入する。
一回限りの外部実行ランチャーは使わない。

Claude Code、Codex、plugin経由ではMCP設定の場所と優先順位が異なる。
有効な設定元を特定して該当項目だけ変更する。ユーザー設定全体を読み出さず、秘密を含む値は表示しない。
chezmoi等の管理下ならsourceを更新する。変更で再起動が必要な範囲も、そのハーネスの仕様で確かめる。

## 隔離contextの設定例

以下はPlaywright MCPのserver定義の例であり、ハーネス設定ファイル全体ではない。
使用versionがフラグを提供していることを確認し、設定先の形式に合わせる。

```json
{
  "command": "playwright-mcp",
  "args": [
    "--isolated",
    "--headless",
    "--storage-state",
    "<private-storage-state-path>"
  ]
}
```

- `--isolated`: セッションを独立したcontextにする。共有profileの同時使用を避ける。
- `--headless`: 画面を表示せず実行する。ユーザーがブラウザを見る必要がある作業には使わない。
- `--storage-state`: 必要な認証状態をcontext作成時に読む。認証が不要ならこの引数を省く。
- `--user-data-dir`: 永続profileが必要で、利用権限と単独利用を確認できる場合の選択肢。共有中のprofileに別プロセスを接続しない。

認証状態ファイルはrepo外の私的な場所へ保存し、所有者以外から読めない権限にする。
新規ファイルを作る前に保存先を確認し、秘密を含む既存ファイルを上書きしない。

設定後はserver起動だけで終えず、対象ページの読み取りを確認する。
一時変更をした場合は元の設定を保全し、必要な作業が終わったら対象項目を戻す。
