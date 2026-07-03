---
name: mitigating-supplychain-attack
description: "Verifies supply-chain safety of dependency and Docker base image changes, and sets up protective rules/hooks on the developer's machine. Use when package.json, pyproject.toml, pnpm-lock.yaml, uv.lock, or Dockerfile has been modified, or when the user asks for dependency review, supply-chain check, typosquatting verification, or supply-chain security setup. フックの再導入は無条件の標準手順としてではなく、過去に一度ユーザー自身が誤検知過多を理由に無効化した経緯を確認してから提案する。"
---

# mitigating-supplychain-attack

2つのモードを持つ。

- **検証モード**（デフォルト）: 現在のリポジトリの依存・Docker 変更を検証する
- **セットアップモード**（`setup` 引数）: ルール・フック・settings.json を端末に導入する

**Freedom Level: 低** — 手順通りに実行する。検証項目をスキップしない。

---

## 検証モード

引数なし、または依存変更の検証を求められた場合。

### 1. 静的検証

```bash
# diff モード: git 変更分のみ（デフォルト）
python3 ~/.claude/skills/mitigating-supplychain-attack/scripts/verify_supply_chain.py

# full モード: リポジトリ全体
python3 ~/.claude/skills/mitigating-supplychain-attack/scripts/verify_supply_chain.py --full
```

引数なしで実行すると diff を試み、変更対象がなければ自動的に full にフォールバックする。明示的に `--full` を渡すと常にリポジトリ全体を検査する。

- `ERROR` → その場で修正
- `MANUAL` → Step 2 の registry review へ

### 2. Registry review（新規依存のみ）

Node.js:
```bash
npm view <pkg> name version maintainers repository.url dist-tags.latest time.created time.modified --json
```

Python:
```bash
python3 -c "
import json, sys, urllib.request
with urllib.request.urlopen(f'https://pypi.org/pypi/{sys.argv[1]}/json', timeout=10) as r:
    i = json.load(r)['info']
    print(json.dumps({k: i.get(k) for k in ('name','version','summary','home_page','project_urls')}, indent=2))
" <pkg>
```

確認ポイント:
- パッケージ名が意図した名前と完全一致（typosquatting でない）
- 公式 repo/org が一致、メンテナ・公開履歴が不自然でない
- lifecycle script がある場合は実行内容を確認

### 3. Docker review（Dockerfile 変更時）

- `FROM` が `tag@sha256:<digest>` で固定されている
- `latest` / タグ省略がない
- リモート script 実行があれば checksum 検証がある

### Output

```
Changed files: ...
Added packages: ...
Findings:
  ERROR: ...    (修正必須)
  MANUAL: ...   (人手確認が必要)
  UNKNOWN: ...  (確認不能 → fail closed)
Verdict: PASS / FAIL
```

### Rules

- lockfile 不整合 → FAIL
- digest pinning なし → FAIL
- 生成したパッケージ名を自己承認しない
- registry metadata を確認できない → UNKNOWN → FAIL

---

## セットアップモード

`setup` 引数が渡された場合。配置すべきファイルは `assets/` にバンドル済み。

### 既知の経緯（フック導入前に必ず確認する）

このフック（`supply_chain_guard.py`）は過去に一度導入され、2026-04-13 にユーザー自身の手で `~/.claude/settings.json` の hooks から除去されている。理由は「過剰反応するせいでめんどくさい」という明示的なフィードバックで、当時の実装は package.json/pyproject.toml/Dockerfile への編集を **すべて** PreToolUse/PostToolUse で block する設計だった（一時的な下書き編集や複数ステップにまたがる意図的な中間状態も区別なくブロックしていた）。一方でルールファイル（`~/.claude/rules/supply-chain-security.md`）は同じタイミングで無効化されておらず、現在も定着している。

つまり「ルール導入は成功、フック導入だけがユーザーの意思で明示的にロールバックされた」という非対称な状態が今も続いている。この経緯を知らないセッションがこのスキルの `setup` を実行すると、ユーザーが意図的に外した挙動を無言で復活させてしまう。

**したがって、フックの配置・登録に進む前に、必ずユーザーに以下を確認する**:
- 過去に「過剰反応でめんどくさい」という理由で無効化した経緯を知っているか
- それでも今回フックを再導入したいか、それともルール（常時ロード済み）だけで十分と考えているか

ユーザーが再導入を明示的に希望した場合のみ、以下の手順に進む。その際は block ではなく **警告のみ（`additionalContext` を返すだけで `decision: block` を返さない）** から始めることを推奨し、しばらく運用して誤検知が少ないと確認できてから block へ強めるかどうかを改めて相談する。

### 手順

1. **ルールファイル**: [assets/supply-chain-security.md](assets/supply-chain-security.md) を読み、`~/.claude/rules/supply-chain-security.md` に書き込む
2. **フックスクリプト**: [assets/supply_chain_guard.py](assets/supply_chain_guard.py) を読み、`~/.claude/hooks/supply_chain_guard.py` に書き込み、`chmod +x` する
3. **settings.json**: `~/.claude/settings.json` を読み、`hooks` セクションに以下を追加する（既存エントリは壊さない）:
   - `PreToolUse` → `Bash` matcher の hooks 配列に `python3 "$HOME/.claude/hooks/supply_chain_guard.py"` を追加
   - `PostToolUse` → `Edit|Write|MultiEdit` matcher で同スクリプトを登録
4. **動作確認**: 以下を実行して deny/pass を確認する:
   ```bash
   echo '{"hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"npx foo"}}' | python3 ~/.claude/hooks/supply_chain_guard.py
   ```

### 注意

- 既存ファイルがある場合は差分を確認してからユーザーに上書きを確認する
- セットアップ完了後、検証モードも実行して現在のリポジトリの状態を確認する

設定の詳細な解説は [references/setup.md](references/setup.md) を参照。
