# LLM-as-Judge Rubric (subagent dispatch 版、3 軸 pass/fail)

生成した condition を **新規 subagent で評価** する。同一セッションでの自己評価は mizchi 原則違反として禁止する。

## なぜ subagent dispatch なのか

[mizchi `empirical-prompt-tuning`](https://zenn.dev/mizchi/articles/empirical-prompt-tuning) の核心原則:

> 書いた本人と判定者を完全に分離するのがポイント。同じ AI を使い回すと、前回の指摘を全部学習してるのでそりゃ通る。

**例外条項なし**。「客観命題なら自己評価できる」も成立しない (jasagiri 記事の「`raise にしたから OK` 確証バイアス」実例)。

→ Judge は **新規 subagent dispatch** で実行する。skill 本体 = writer、subagent = judge、明確に分離。

## 3 軸

| 軸 | 質問 (yes/no) | pass の最低条件 |
|---|---|---|
| **measurable** | 成功基準が数値 / 真偽 / exit code に帰着できるか? | 「all tests pass」「success_rate >= 0.99」「git diff is empty」など、機械的にチェックできる命題が 1 つ以上ある |
| **proof** | その基準を観測する具体的コマンド / アーティファクトパス / parsing が明示されているか? | `npm test`, `python eval.py | grep X | awk Y`, `find inbox -name '*.md'` のような **実行可能な検証手段**が書かれている |
| **bounding** | turn 上限 / metric 上限 / エラー反復制限のいずれかが含まれるか? | `stop after 20 turns`, `or if success_rate plateaus for 5 iterations`, `or if the same error repeats 3 times` 等が含まれる |

## subagent dispatch プロトコル

Task tool で新規 subagent を起動し、以下の入力を渡す:

- **対象**: 生成した /goal condition (本文)
- **元 seed**: ユーザーが渡したゴール (自然言語、コンテキスト用)
- **タスク指示**: 3 軸を独立に judge し、yes/no と理由を返す

subagent 起動契約のテンプレは [../assets/judge-subagent-prompt.md](../assets/judge-subagent-prompt.md) を参照。

### 期待される subagent 出力

```json
{
  "measurable": {"verdict": "pass" | "fail", "reason": "<1-2 文>"},
  "proof":      {"verdict": "pass" | "fail", "reason": "<1-2 文>"},
  "bounding":   {"verdict": "pass" | "fail", "reason": "<1-2 文>"}
}
```

または自然言語の同等表現でも可。skill 側で 3 軸の verdict を抽出する。

### dispatch 不能時の挙動

Task tool が使えない環境 (既に subagent として動作中、Task tool 無効化等) では:

1. Judge を **スキップ**
2. 出力末尾に明示: `<!-- empirical evaluation skipped: subagent dispatch unavailable. Manual review with /empirical-prompt-tuning in a fresh session is recommended. -->`
3. **自己評価で代替しない** (mizchi 原則)

軽量形式チェック (skill 内の regex / 文字数チェック) は dispatch 不能でも常に実行する。これは mizchi 原則の対象外 (LLM 判定ではないため)。

## 判定例 (subagent が返す結果のサンプル)

### Pass する condition

```
all TypeScript errors in src/auth/ are resolved
prove by running `npx tsc --noEmit src/auth/**/*.ts` and seeing no errors
do not modify files outside src/auth/
stop after 20 turns or if the same error repeats 3 times
```

subagent の判定:
- measurable: pass (errors = 0 = exit code 0)
- proof: pass (`npx tsc --noEmit src/auth/**/*.ts` 明示)
- bounding: pass (`20 turns` + `same error repeats 3 times`)

### Fail する condition

#### 例 1: measurable fail

```
improve the code quality of src/auth/
```

- measurable: fail (「quality」が数値/真偽に帰着しない)
- proof: fail (検証手段なし)
- bounding: fail (turn 上限なし)
→ 全 fail。再生成。

#### 例 2: proof fail

```
all tests pass
stop after 10 turns
```

- measurable: pass (tests = pass/fail で機械的)
- proof: fail (具体的コマンドなし。`npm test`? `pytest`? 不明)
- bounding: pass
→ proof fail。再生成。

#### 例 3: bounding fail

```
migrate src/legacy/auth.ts from callback to async/await
prove by `npm test` exiting 0 and `grep -r "callback(" src/legacy/auth.ts` returning no matches
```

- measurable: pass
- proof: pass
- bounding: fail (上限なし → 無限ループの危険)
→ bounding fail。再生成して `stop after 30 turns or if migration fails 3 times in a row` を追記。

## Failure mode と対処

### measurable fail を直す

「quality / readability / cleanness」のような主観語を **機械的命題に翻訳**:

| 主観語 | 機械的翻訳 |
|---|---|
| quality を上げる | test coverage を X% 以上にする |
| readability を上げる | 関数の cyclomatic complexity を X 以下にする (lint で計測) |
| cleanness | ESLint / Ruff / Clippy のエラー数 = 0 |

翻訳できない場合 (UI デザイン等) は /goal の用途ミスマッチ → ユーザーに「主観判断は /goal 向きじゃない、`/autoresearch:reason` を検討」と返す。

### proof fail を直す

「prove by X」「verify by running Y and seeing Z」を condition に明示。

```
# Bad
all tests pass

# Good
prove by running `pytest tests/` and seeing "passed" in the last line
```

### bounding fail を直す

最低 1 つの bounding clause を末尾に追加:

```
or stop after 20 turns
or if the same error repeats 3 times
or if no progress for 5 consecutive turns
```

metric-verifier の場合は **plateau 検出**も書ける:

```
or stop if success_rate doesn't improve by >= 0.01 for 10 consecutive iterations
```

## 自動再生成のルール (mizchi 原則準拠)

- Judge subagent が 1 つでも fail → 1 回だけ自動再生成
- 再生成時は **新規 subagent を改めて dispatch** (同 subagent は使い回さない — 前回の指摘を学習してしまうため)
- 2 回目も fail → 再生成を諦めて Judge コメント併記で出力。ユーザー判断に委ねる
- ユーザーが手動で再呼び出しすれば、新セッションでの再 dispatch になる

## アンチパターン

- ❌ skill 内で同一セッション LLM-as-Judge (= 自己評価) — mizchi 原則違反
- ❌ 同じ subagent を再生成で使い回す — 前回学習でバイアス
- ❌ dispatch 不能時に自己評価で代替 — mizchi 原則違反
- ✅ 軽量形式チェック (regex / 文字数) は skill 内 OK — LLM 判定ではないため
- ✅ Judge を subagent dispatch で独立実行 — writer/judge 分離

## Claude Code 固有: 4000 char 内に 3 軸を収める書き方

Claude Code L1 では condition が **4000 char 上限**。3 軸を満たしつつ短く書くテクニック:

### 構造化を最大限活用

冗長な散文を避け、項目化・コマンド埋め込みで密度を上げる:

```
# Verbose (NG)
The goal is to fix all TypeScript errors in the src/auth/ directory.
We should verify by running the TypeScript compiler. The verification
command is npx tsc --noEmit. After running this command, we expect
no errors to be reported.

# Compact (OK, ~1/3 size)
all TS errors in src/auth/ resolved
proof: `npx tsc --noEmit` → no errors
do not modify outside src/auth/
stop after 20 turns
```

### proof を `→ <expected>` で短縮

```
# Long
prove by running `npm test` and seeing the output contains "0 failing"

# Short
proof: `npm test` → "0 failing" in output
```

### autoresearch 連携モードでは更に短く

iteration サブゴールなので 1000 char 以下が現実的。global metric の判定は autoresearch 側に任せ、condition には iteration の local check のみ書く。

### 4000 char チェックポイント

- 3500 char で **警告** (Mega 系で余裕が無いことが多い)
- 4000 char 超過なら **L3 (agent hook) への切替**を提案
  - L3 では evaluator が tool 使えるので、proof method を condition に書かなくてよい
  - condition は薄く objective だけ書ければよくなる
