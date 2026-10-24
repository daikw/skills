---
name: history-search
description: "Claude Code と Codex の会話履歴から、過去の話題、作業場所、再開するセッションを探す。ホストやコンテナなど実行環境によって保存先が異なる履歴の調査にも使う。集計や著者判定では収録範囲と来歴を確認する。履歴の移行は対象外。"
---

# 会話履歴の検索

Claude Code と Codex の会話履歴を調べる。
ユーザーが対象を指定していなければ、今回の調査範囲に関係する両方の履歴を確認する。

## 検索範囲を確認する

既定パスは候補であり、すべての履歴がそこにあるとは限らない。

- 調査しているホストと、会話が実行された環境を確認する。コンテナや別の実行環境の内部にも履歴があり得る。
- 実効 `CODEX_HOME`、起動設定、永続化先を確認する。コンテナの場合は volume や bind mount の対応から、コンテナ内の保存先とホスト側の参照先を区別する。個別環境の配置はその運用資料を参照する。
- アクセスできる保存先を検索し、検索した範囲と、存在しない・読めない・未取得の範囲を区別する。見えている場所にないことだけで、会話が存在しないとは判断しない。
- 保存先や元の実行環境を出典に残す。同じ session ID やコンテナ内の `/workspace` だけから、同じ会話やホストの実パスだと推測しない。

検索のために履歴を移動・複製・更新したり、アクセス権限を広げたりしない。

## 標準の保存形式

### Claude Code

```text
~/.claude/projects/<project-key>/<session-id>.jsonl
~/.claude/history.jsonl
```

project-key は元の実パスの `/` と `.` などを `-` に変換したもの。
元からの `-` と区別できず、一意に逆変換できない。
実在する保存先を一覧で確認し、正確な作業場所は transcript の `cwd` などの metadata と照合する。

### Codex

`CODEX_HOME` が設定されていればその場所、未設定なら `~/.codex` が標準の state directory。

```text
<CODEX_HOME>/sessions/<YYYY>/<MM>/<DD>/rollout-<timestamp>-<session-id>.jsonl
<CODEX_HOME>/archived_sessions/   # 存在する場合
<CODEX_HOME>/history.jsonl
<CODEX_HOME>/session_index.jsonl
```

rollout はプロジェクト別ではなく日付別。
作業場所は通常、先頭付近の `session_meta` の `cwd` に記録される。
版によって形式が異なるため、実際のフィールドを確認する。
`history.jsonl` は入力履歴、`session_index.jsonl` は名前などの索引だが、全セッションを網羅するとは限らない。

## 検索例

実在する対象を選び、まずファイル名や metadata で候補を絞る。
次は標準配置の例。別の state directory を確認した場合は、その保存先に置き換える。

```sh
# Claude の会話ファイルを探す
rg -l -i -F --glob '*.jsonl' -- 'キーワード' "$HOME/.claude/projects"

# 現在の Codex state の会話ファイルを探す
codex_state_dir="${CODEX_HOME:-$HOME/.codex}"
rg -l -i -F --glob '*.jsonl' -- 'キーワード' "$codex_state_dir/sessions"

# 索引や archive は、存在するものを必要に応じて確認する
rg -l -i -F -- 'キーワード' "$codex_state_dir/history.jsonl" "$codex_state_dir/session_index.jsonl"
```

全文検索には、注入された指示やツール結果もヒットする。
候補ファイルの該当箇所を読み、実際の発言と文脈を確認して結果を返す。
検索語はデータとしてクォートし、`--` でオプションと区別する。

分析的なクエリは [references/recipes.md](references/recipes.md) の保存形式に合うレシピを必要に応じて使う。

### 集計とプロンプトの著者判定

検索ヒットは候補の発見であり、全件収録や本人の執筆を証明しない。集計や文体分析では、
対象期間・クライアント・保存先・数える単位を決め、欠損と除外件数を記録する。

- **保存先を照合する**。Claude の `history.jsonl` と `projects/` の transcript は保持範囲が一致するとは限らず、貼付本文がプレースホルダーだけのこともある。Codex では版によって `thread_history_*.sqlite` に `userMessage` の投影が存在し、入力集合を得る入口になる。ファイル名・schema・収録範囲を読み取りで確認し、rollout や history と照合する。内部 DB の版や網羅性を固定の保証として扱わない。
- **会話ロールと入力を分ける**。Claude の `type=user` には `tool_result`、Skill 展開、通知、圧縮要約も入る。Codex の `role=user` にも AGENTS・環境・goal などの注入内容が入る。利用可能な metadata、内容ブロック種別、元の tool call を使って区別し、フィールドが欠ける古い記録は未判定として残す。
- **同一イベントを重複集計しない**。history、rollout、投影、音声転記の対応や、fork・subagent が継承した親の文脈を確認する。同じ文面の再提出は別イベントになり得るため、テキスト一致だけで全体を重複排除しない。異なる保存形式の ID が共通とも限らない。
- **送信経路と本文の著者を分ける**。`origin.kind=human`、`promptSource=typed`、`user.text`、`UserMessage`、CLI/SDK の別は、人が文章を書いた証拠ではない。人によるモデル出力の貼付や、モデルによる送信があり得る。親の tool call や先行する assistant 出力との一致は来歴の根拠になるが、その出力自体が人の文章を引用していないかも確かめる。一致しないことも人の執筆の証明にはならない。
- **推定と確定を分ける**。著者のラベルは人・モデル・混合・不明を保持し、モデルの提案と本人の確認を別に記録する。モデルが書き、本人が採用した指示は、本人が求める成果の根拠にはなるが、本人の文体の根拠とは限らない。

履歴には秘密や個人情報が含まれ得る。まずファイル名・schema・metadata を絞って調べ、
本文の出力・共有は必要な範囲に限定して秘匿する。検証用に履歴や内部 DB を更新しない。

Codex の保存形式の確認には、公式実装の
[入力履歴](https://github.com/openai/codex/blob/45134c04632b971776d88edfdea71c051ebe4161/codex-rs/message-history/src/lib.rs)、
[内容の分類 metadata](https://github.com/openai/codex/blob/45134c04632b971776d88edfdea71c051ebe4161/codex-rs/protocol/src/models/item_metadata.rs)、
[履歴の投影](https://github.com/openai/codex/blob/45134c04632b971776d88edfdea71c051ebe4161/codex-rs/app-server-protocol/src/protocol/thread_history.rs)
を参照できる（2026-09-09 確認版）。Claude の上記フィールドは同日のローカル transcript の観測例であり、両者とも全ての過去・将来の版への保証ではない。

## 再開先を案内する

Claude Code は記録された作業場所とセッションを確認し、その環境の `/resume` を使う。
Codex は session ID に加えて、保存時の state directory と作業場所を確認する。
コンテナなどで実行された会話は、元の実行条件を確認してから再開先を案内する。
検索依頼だけでは再開や投稿を実行しない。
