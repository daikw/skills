# Evaluator の制約と condition 設計への影響

L1（公式 /goal）の evaluator は**ツール呼び出しができない**。会話 surface しか見ない。この制約が condition の書き方を強く規定する。

## 設計原則: surface-everything

evaluator は Claude が会話に「吐いた」内容しか見えない。つまり:

- ❌ "all tests pass" だけだと判定不能（テスト結果が transcript に無いと evaluator は確認できない）
- ✅ "`npm test` exits 0 and the final summary line is printed in the transcript" なら判定可能

## condition で必ずやること

### 1. proof method を明示する

```
# Bad
all tests pass

# Good
prove by running `npm test` and printing the final summary line (tests passed/failed counts)
```

### 2. 中間状態の surface 指示

```
# Bad
the migration is complete

# Good
prove by:
  1. running `npm test` and printing the result
  2. printing the count of remaining call sites with `grep -r "oldApi" src/ | wc -l` (must be 0)
```

### 3. 否定条件の検証可能性

```
# Bad (false の証明は難しい)
no other files are modified

# Good (具体的なコマンドで確認)
prove `git diff --name-only main` lists only files in src/auth/
```

## 文字数管理

condition は **4000 char 上限**。生成時に文字数をカウントし、超えそうなら:

1. 冗長な指示を削る
2. 詳細を別ファイルに切り出して「see PLAN.md」と参照
3. サイズバケットを下げる（Large → Medium）

## bounding clause の書き方

無限ループを防ぐため、必ず以下のいずれかを condition に含める:

```
or stop after 20 turns
or stop if the same error repeats 3 times
or stop after token usage reaches 500K
```

evaluator は会話履歴の長さやエラーの繰り返しを判定できるので、自然言語で書けば動く。

## L3 にすると消える制約

agent-based hook（L3）の evaluator は subagent でツール使える。よって:

- proof method を condition に書かなくてよい（evaluator が自分でテスト実行）
- 中間状態の surface 指示も不要
- objective を端的に書ける

ただし L3 は:

- experimental
- timeout / 最大ターン数の制限あり
- 1 ターンごとに subagent が走るのでコスト高い

なので「テストが green」レベルの簡単な検証なら L1 で十分、「マイグレーション完了 + テスト全 green + lint clean + 既存挙動保持」のような複合検証が必要なら L3。

## autoresearch 連携モードでの evaluator の責務縮小

condition が `autoresearch 1 iteration 内のサブゴール` として書かれる場合 (詳細は [autoresearch-handoff.md](autoresearch-handoff.md))、evaluator の責務は大幅に縮小される:

- **やること**: iteration の local check が pass したか確認
- **やらないこと**: global metric (success_rate 99% 等) の達成判定 — これは autoresearch 側が外側で担当

例えば「success_rate 99% を 1000 epoch 訓練で達成」のようなゴールは:

- autoresearch core が `python eval.py` を毎 iteration 走らせて metric を観測
- /goal は各 iteration 内で「ハイパラ調整 + 1 回 train + local check 報告」だけを担う
- /goal の evaluator は「iteration の local check が pass したか」だけを見る

これにより:

- L1 evaluator (Haiku, ツール不可) でも十分機能する (global metric の数値を読む必要がない)
- 4000 char 制約も余裕で守れる (iteration サブゴールは典型 500-1000 char)
- 数千 epoch クラスの長期最適化を /goal の session-scoped 制約下で扱える

連携モードの判定トリガと出力テンプレは [autoresearch-handoff.md](autoresearch-handoff.md) を参照。
