# Verifier-Type Recon パターン

seed 文字列とコードベースから verifier の種類を推定し、対応する具体的コマンド / metric / artifact を抽出する。

## 3 種類の verifier

| Type | 真実の source | 典型キーワード | コードベースから抽出するもの |
|---|---|---|---|
| **command-verifier** | shell command の exit code or 出力 | test / lint / build / grep / git diff / typecheck | `npm test`, `cargo test`, `uv run pytest`, `tsc --noEmit` etc. |
| **metric-verifier** | parseable な数値 | success_rate / accuracy / loss / reward / score / BLEU / coverage / latency | eval script, benchmark, training validation |
| **artifact-verifier** | ファイルの存在 / 内容 / 構造 | word count / front-matter / index / TOC / summary | grep / find / yq / 自前 validator |

## 推定優先順位 (高 → 低)

1. **metric-verifier**: success_rate / accuracy / loss / reward / BLEU / win_rate / coverage / latency / p95 / throughput 等の数値メトリクス語が含まれる → 最優先
2. **command-verifier**: test / lint / build / typecheck / clippy / mypy / vet / grep 等のコマンド名が含まれる
3. **artifact-verifier**: word count / structure / front-matter / summary / TOC / index / orphan / duplicate 等の語が含まれる
4. **判別不可**: 上記いずれも含まれない → AskUserQuestion で 1 問確認

## verifier 抽出: command-verifier

コードベースから以下を確認:

- `package.json` → `scripts.test` / `scripts.lint` / `scripts.build` の中身
- `pyproject.toml` → `[tool.ruff]` / `[tool.mypy]` / pytest 設定
- `Cargo.toml` → `cargo test`/`cargo clippy`
- `go.mod` → `go test ./...` / `go vet ./...`
- `Makefile` / `justfile` → ターゲットの中身
- `.github/workflows/` → CI で実際に走るコマンド (最も信頼できる)

抽出例:

```
- `npm test` exits 0
- `npm run lint` outputs no errors
- `npm run build` exits 0
- `npx tsc --noEmit` outputs no errors
```

## verifier 抽出: metric-verifier

コードベースから以下を確認:

- `eval.py` / `evaluate.py` / `bench.py` / `benchmark.sh` の存在
- 訓練 config (`configs/*.yaml` / `train.py`) で定義されたメトリクス
- `.github/workflows/` の bench / eval job

抽出例:

```
- `python eval.py --task pick_place 2>&1 | grep success_rate | awk '{print $2}'` produces a number
- the number is >= 0.99
- print the parsed number to stdout each iteration
```

contract が複雑な場合は `EVAL_CONTRACT.md` を別途参照させる:

```
- prove by running `python eval.py --task X` whose output contract is in `EVAL_CONTRACT.md`
- read EVAL_CONTRACT.md before parsing
```

## verifier 抽出: artifact-verifier

コードベースから以下を確認:

- 対象ディレクトリの構造 (`ls -la`)
- 想定されるファイルパターン (e.g., `inbox/*.md`)
- 既存の validator script

抽出例:

```
- every file in `inbox/clippings/` has a `summary:` field in front-matter
- prove by running:
    `for f in inbox/clippings/*.md; do head -20 "$f" | grep -q "^summary:" || echo "missing: $f"; done`
  and seeing no output
- print the file count before and after
```

## Codex 流 audit との対応

Codex /goal の audit-first 哲学 (agent 自身が完了を監査) と verifier-type の対応:

| Verifier | Codex audit でやること |
|---|---|
| command-verifier | コマンドを実行 → exit code / 出力を agent 自身が読む |
| metric-verifier | スクリプト実行 → 数値を parse → 閾値判定 |
| artifact-verifier | ファイル走査 → grep / yq / wc 等で構造確認 |

condition には audit ステップを明示的に書いてよい (Codex は CC と違って evaluator が agent 自身)。

## 判別不可時の AskUserQuestion

判別できない場合、以下 1 問のみ:

```
このタスクの「完了」は何で判定する？
- A: 特定コマンドが exit 0 / 出力に文字列を含む (test/lint/build 等)
- B: 数値メトリクスが閾値を満たす (success rate / accuracy 等)
- C: 特定ファイルが存在する / 特定の内容を持つ
- D: その他 (自由記述)
```

返答を受けたら対応する verifier-type で進める。
