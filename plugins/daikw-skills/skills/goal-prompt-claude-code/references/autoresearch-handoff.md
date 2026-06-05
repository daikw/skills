# autoresearch 連携モード

seed が「累積最適化 / 長期実験 / 横断 refactor」を含む場合、`/goal` だけでは収まらない。**外部ループを autoresearch に委譲**し、`/goal` は 1 iteration 内のサブゴール記述に限定する。

## トリガ条件

以下のいずれかが seed に含まれたら **autoresearch 連携モード**に切り替える:

- 数値メトリクス目標 + 累積最適化を示唆: `success_rate を 99%` / `loss を 0.1 以下` / `coverage を 95%` / `latency p95 を 100ms 以下`
- 数千〜数万単位の繰り返し: `数千 epoch` / `1 万件のテストケース` / `全 PR を順に`
- 横断的 refactor: `全モジュール` / `monorepo 全体` / `repo-wide`
- ML / RL / sim 用語: `train` / `eval` / `episode` / `rollout` / `reward` / `policy`

これ以外 (= 単一 mission で完結) は通常モードのまま。

## 連携モードでの出力

通常の `/goal <full condition>` ではなく、**autoresearch の 1 iteration 内サブゴール**を生成する。autoresearch loop が外側で modify → verify → keep/discard を回し、`/goal` は各 iteration 内のサブミッションを担う。

### 連携モードの出力構造

```
Sub-goal of autoresearch iteration:
{{ONE_LINE_ACTION_FOR_THIS_ITERATION}}

Verification (this iteration only):
{{LOCAL_CHECK}}

Constraints:
- This is ONE iteration of an autoresearch loop. Do NOT attempt to converge the global metric here.
- If the local check fails, report findings concisely and stop; the outer loop will decide keep/discard.
- Do not modify {{OUT_OF_ITERATION_SCOPE}}.
- Stop after {{N}} turns.

# autoresearch iteration sub-goal
# Outer loop: /autoresearch:plan or see results log
```

## autoresearch:plan への誘導コメント

連携モードの paste-ready 出力の末尾に、必ず以下を添える:

```markdown
> **Note**: This is a sub-goal for one iteration of an autoresearch loop.
> To set up the full loop:
>
>   /autoresearch:plan
>   Goal: <your big goal here>
>
> autoresearch will define Scope/Metric/Direction/Verify, then call this
> sub-goal (or similar) once per iteration.
```

## 連携モードでの Judge 緩和

通常モードでは 3 軸 pass/fail を厳格にチェックするが、連携モードでは以下を緩和:

- **measurable**: iteration の local check が機械的なら OK (global metric は autoresearch 側で担当)
- **proof**: iteration 内の verification command が明示されていれば OK
- **bounding**: iteration の turn 上限 (5-20 turn 程度) が明示されていれば OK

つまり「global goal 達成の責任は持たない、1 iteration を確実に終わらせる」だけを Judge する。

## Codex における連携モードの利点

Codex /goal は永続 state + pause/resume を持つので、autoresearch 連携モードでも以下が可能:

- iteration ごとに `/goal pause` → autoresearch が結果を解析 → `/goal <next sub-goal>` で再開
- iteration の audit を agent 自身が行い、結果を `RESULT.md` 等に書き出して autoresearch に渡す
- 失敗 iteration は `/goal clear` で破棄、`git revert` 連動

## 連携モードを使わない判断

以下なら通常モードで OK:

- 単一 mission で完結 (1-100 turn で終わる前提)
- metric が無く、command-verifier or artifact-verifier で完了判定できる
- 累積最適化が要らない
- そもそも metric 駆動の探索ではない (UI 設計 / 文書執筆 等)

迷ったら通常モード。連携モードは「明らかに autoresearch の領域」のときだけ。
