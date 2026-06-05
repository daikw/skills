# サプライチェーンセキュリティ セットアップガイド

AI エージェントによるサプライチェーン攻撃の誘発を防ぐための、ルール・フックの導入手順。

## 構成要素

| ファイル | 役割 | 適用タイミング |
|---------|------|-------------|
| `~/.claude/rules/supply-chain-security.md` | エージェントの行動ルール（常時適用） | 全セッションで自動読み込み |
| `~/.claude/hooks/supply_chain_guard.py` | コマンド実行/ファイル編集の自動検証 | PreToolUse / PostToolUse で自動実行 |

## 前提条件

- Python 3.11+（`tomllib` が標準で必要）
- Git
- Claude Code

## Step 1: ルールの配置

`~/.claude/rules/supply-chain-security.md` を配置する。このファイルは Claude Code のセッション開始時に自動で読み込まれ、エージェントの行動を制約する。

ルールが禁止する主な行動:

- `npx` / `bunx` / `pnpm dlx` / `uvx` の使用
- `^` / `~` 等の範囲指定での依存追加
- lockfile を更新しない依存変更
- install script 保護の緩和
- Docker の `latest` タグ / digest なし指定

## Step 2: フックスクリプトの配置

```bash
chmod +x ~/.claude/hooks/supply_chain_guard.py
```

### フックが検知する内容

**PreToolUse（Bash コマンド実行前）:**

| パターン | 判定 |
|---------|------|
| `npx <anything>` | deny |
| `bunx <anything>` | deny |
| `uvx <anything>` | deny |
| `pnpm dlx <anything>` | deny |
| `--ignore-scripts=false` | deny |
| `npm_config_ignore_scripts=false` | deny |
| `npm config set ignore-scripts false` | deny |
| `yarn config set enableScripts true` | deny |

**PostToolUse（ファイル編集後）:**

| 対象ファイル | 検証内容 |
|------------|---------|
| `package.json` | 依存変更時に lockfile（`pnpm-lock.yaml` / `package-lock.json`）が更新されているか |
| `pyproject.toml` | 依存変更時に `uv.lock` が更新されているか |
| `Dockerfile` | `FROM` に `@sha256:` digest pinning があるか、`latest` タグを使っていないか |

## Step 3: settings.json への hooks 登録

`~/.claude/settings.json` の `hooks` セクションに以下を追加する。

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          // ...既存の hooks...
          {
            "type": "command",
            "command": "python3 \"$HOME/.claude/hooks/supply_chain_guard.py\""
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$HOME/.claude/hooks/supply_chain_guard.py\""
          }
        ]
      }
    ]
  }
}
```

既に `PreToolUse` の `Bash` matcher がある場合は、`hooks` 配列にエントリを追加する。

## Step 4: 動作確認

### フックのテスト

```bash
# npx が deny されるか
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npx create-react-app myapp"}}' \
  | python3 ~/.claude/hooks/supply_chain_guard.py
# → permissionDecision: deny

# 通常の npm install は通るか
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npm install express"}}' \
  | python3 ~/.claude/hooks/supply_chain_guard.py
# → 出力なし（通過）

# ignore-scripts=false が deny されるか
echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npm ci --ignore-scripts=false"}}' \
  | python3 ~/.claude/hooks/supply_chain_guard.py
# → permissionDecision: deny
```

## プロジェクト側の追加設定

フックとルールはエージェントの行動を制約するが、パッケージマネージャ自体の防御はプロジェクト側で設定する。

### pnpm（推奨）

```yaml
# pnpm-workspace.yaml
minimumReleaseAge: 10080          # 7日間（分単位）
minimumReleaseAgeExclude:
  - "@<your-org>/*"               # 社内パッケージは除外

allowBuilds:
  esbuild: true
  "@swc/core": true
  protobufjs: true

strictDepBuilds: true             # 未許可の install script で CI を止める
blockExoticSubdeps: true          # transitive の git+ssh/tarball を遮断
trustPolicy: no-downgrade         # provenance の低下を検知
```

### npm（pnpm 移行前の暫定）

```ini
# .npmrc
ignore-scripts=true
save-exact=true
audit=true
```

### uv（Python）

```toml
# uv.toml or pyproject.toml [tool.uv]
index-strategy = "first-index"    # dependency confusion 防止
```

### Docker

```dockerfile
# digest pinning 必須
FROM python:3.13-slim@sha256:<actual-digest>
```

## 端末全体の追加設定（オプション）

エージェント外でも防御を入れたい場合:

```bash
# Corepack 有効化（パッケージマネージャのバージョン固定）
corepack enable

# グローバル pip 設定
# ~/.config/pip/pip.conf
# [global]
# require-virtualenv = true
# only-binary = :all:

# グローバル Git hooks（lockfile 忘れ検知）
# git config --global core.hooksPath ~/.config/git/hooks
```

## トラブルシューティング

### フックが Python 3.11 未満で動かない

`tomllib` は Python 3.11 で標準ライブラリに追加された。3.10 以下では `pyproject.toml` の解析が常に「変更あり」として扱われる（安全側に倒れる）。

### PostToolUse で lockfile 未更新の警告が出る

`package.json` を編集した直後に出る場合は正常動作。`pnpm install` / `npm install` を実行して lockfile を更新すれば解消する。

### deny されたコマンドを本当に実行したい

フックは Claude Code のエージェント向け。人間が直接ターミナルで実行する場合はフックを通らないので、`npx` 等を直接使うことは可能。ただし lockfile 整合性は手動で維持すること。
