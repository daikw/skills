# Verifierの確認

verifierはユーザーの成功条件を観測する手段である。
語彙やファイルの存在だけから選ばず、内容と適用環境を読む。

## command

package managerのscripts、Makefile/justfile/miseのtask、既存test、CI job等から、実際のコマンドと対象を確認する。
manifestがあるだけで `npm test` 等が実装済みと判断しない。
追加のtoolを導入する前に既存の検証層を使う。

生成文にはコマンド、cwd、必要な環境、期待する結果、何を証明するかを書く。
exit 0でも対象testが収集されていない場合や別versionを検査した場合は成功の証拠にならない。
例は確認したrepoコマンドへ置き換える。

```text
Verify in <repo> using <existing check command>.
Confirm <required behavior and expected result> on the changed revision.
```

## metric

測定scriptの入力、datasetや環境、単位、計算、出力schemaを確認する。
ユーザーや既存の評価契約が固定した比較条件を保持する。
目標値は出典付きで使い、欠損・未実行・startup失敗をゼロ点にしない。

```text
Use <existing evaluator> with the inputs and metric defined in <evaluation contract>.
Compare the measured result with <user-specified target>.
Record input identity, environment, raw result and interpretation.
```

## artifact

成果物の内容・構造・参照関係が要求を満たすか確認する。
既存validatorがあれば使い、ファイル存在や文字数だけで内容の正しさを代用しない。
文書・設計では、指定された論点・根拠・制約・表示結果などを観測可能な受入条件にできる。

```text
Produce <artifact> covering <required content>.
Verify <content/structure/rendering condition> using <existing checker or inspection method>.
```

## 複数の検証と未確認

同じ目的に複数の検証が必要なら組み合わせる。成功条件を変えず、単位や比較対象を揃える。
生成時のverifier確認と、目標実行後の合格は別である。
生成時に実行していないコマンドを実行済みとは書かない。
検証手段が分からないときは、どの成果の何が観測できないかを明示して確認する。
