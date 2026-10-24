---
name: history-search
description: "通常の Codex、Claude Code、Discord 経由の Codex 会話履歴を横断検索する。過去の話題、作業場所、セッション、元の Discord スレッドを探すときに使う。履歴の集計や著者判定では収録範囲と来歴を照合する。履歴の移動や Discord 投稿は対象外。"
---

# 会話履歴の横断検索

通常の Codex、Claude Code、Discord bridge の会話を一つの検索入口から探す。
ユーザーが検索先を指定しなければ、アクセスできる全保存先を対象にする。
実行環境ごとの履歴を移動、コピー、書き換えず、出典と元の作業場所を付けて結果をまとめる。

## まず同梱の検索を使う

今回読み込んだこの `SKILL.md` の親ディレクトリを特定し、同梱の [scripts/search.py](scripts/search.py) を既存の Python で実行する。
`history_skill_dir` はその実在するディレクトリに置き換える。新しい依存は不要。

```sh
uv run --offline --no-project python "$history_skill_dir/scripts/search.py" -- 'キーワード'
```

検索語は正規表現ではなく、大文字小文字を区別しない部分一致。
`--` の後に渡せば `-` で始まる語も検索できる。
別の home を調べる場合は `--home /path/to/home` を指定する。
現在の `CODEX_HOME` が設定されている場合は、対象 home の `--codex-home` も明示して検索範囲を揃える。
カスタムの保存先には `--codex-home /path/to/codex-state`、`--discord-state-dir /path/to/bridge-state` を指定する。
通常の Codex 保存先は現在の `CODEX_HOME`、未設定なら `~/.codex`。

出力は JSON。`matches` は `origin`、ファイル、`session_id`、記録された `cwd` 等の metadata で、発言本文は出さない。
Discord は読み取り専用で bridge の `threads` 表を照合し、`channel_id`、`thread_ids`、`codex_home` とホスト側 workspace を付ける。
コンテナー内の `/workspace` は `recorded_cwd` として残す。
対応表がない、古い、曖昧な場合は `cwd` を推測せず、`mapping_status` を示す。
同じ session ID でも別保存先の会話を同一視せず、同じファイルの alias だけを重複除外する。
派生する保存先が指定した base や別チャンネルの外へ symlink で抜ける場合は対象にせず、読取不能と同様に検索範囲の欠損として示す。
FIFO など通常ファイル以外の JSONL は読み込まない。

`coverage.roots` の `status` で検索済み、保存先なし、読取失敗を区別する。
`coverage.problems` がある場合は終了コード `2` だが、取得できた結果も JSON に残る。
不正 JSON、途中の書き込み、読取失敗を無視して「全履歴を検索済み」「該当なし」と断定しない。
保存先がなくなる前の履歴や、別ホスト、未取得のクライアント履歴まで網羅するものではない。

本文の検索対象は user / assistant の表示テキスト。
既知の AGENTS 展開、ツール結果、analysis、Discord の役割指示や引用された別スレッドの文脈は除外する。
未知の版の注入形式や、ユーザーによる引用、fork の継承を完全に分類する保証はない。
ヒットした会話の特定箇所を追加で読み、来歴を確認する。集計や本人の文体の根拠には検索ヒットだけを使わない。

この統合検索は保存先にアクセスできるホストで使う。
隔離された Discord 実行環境からホストの全履歴を読めるようにする機能ではない。
そこから参照する必要がある場合は、許可する利用者と履歴範囲を別途定める。

## 履歴の保存場所

### Claude Code

```
~/.claude/projects/<プロジェクトパス>/   # ディレクトリ名は実パスの / と . を両方 - に置換
    <session-uuid>.jsonl                 # 1ファイル = 1会話
~/.claude/history.jsonl                  # グローバル履歴
```

**既知の落とし穴**: `/` だけでなく `.` も `-` に変換される。例えば `gitlab.example.com` は `gitlab-example-com` になる。「実パスの `/` を `-` に置換すればディレクトリ名になる」という思い込みで手で組み立てると、`.` の変換漏れで存在しないディレクトリを grep して `Exit code 2` になる（実際に踏んだ実障害）。

**決め打ちで再構成せず、まず一覧から確認する**:

```bash
ls ~/.claude/projects/ | grep -i <キーワードの断片>
```

### Codex CLI

```
~/.codex/sessions/<YYYY>/<MM>/<DD>/
    rollout-<timestamp>-<session-uuid>.jsonl   # 1ファイル = 1セッション、日付別に格納
~/.codex/history.jsonl        # 対応クライアントが保存した入力履歴 {session_id, ts(unix秒), text}
~/.codex/session_index.jsonl  # セッション名の索引 {id, thread_name, updated_at}
```

**Claude Code と構造が根本的に違う点**（推測しにくいので明記）:

- **プロジェクト別ではなく日付別**。ディレクトリにもファイル名にもプロジェクト情報がない。現行形式では、作業ディレクトリは rollout ファイル先頭行の `session_meta` に `"cwd":"..."` として入っている。古い形式では実際のフィールドを確認する
- **rollout ファイルは `session_meta` にシステムプロンプト（`base_instructions`）を含む場合がある**。一般的な語で全文検索すると注入された指示までヒットする。まず軽量な `~/.codex/history.jsonl` で当たりをつけ、`session_id` からファイルを特定する。ただし、見つからない場合は rollout など別の保存先も調べる
- `history.jsonl` と `session_index.jsonl` は、どちらも全セッションを網羅するとは限らない。クライアント・保存設定・版・保持期間によって収録範囲が異なる。索引にないことを、セッションや入力が存在しない根拠にしない

### Discord bridge

標準の bridge state は `~/.local/state/codex-discord/`。
異なる `stateDir` を使う構成では、設定の参照先を確認して helper に渡す。

```text
<stateDir>/channels/<parent-channel-id>/codex/sessions/**/*.jsonl
<stateDir>/codex/sessions/**/*.jsonl  # チャンネル別状態へ移行する前の保存先がある場合
<stateDir>/bridge.sqlite            # 元スレッド、session、workspace の対応
```

通常の Codex では `sessions/` に加え、存在する `archived_sessions/` も helper が検索する。
bridge の DB は `mode=ro` と `query_only` で読む。
DB 本体、WAL、transcript の内容は更新しない。SQLite が既存 SHM の reader 管理情報を更新する場合はある。
WAL モードで必要な sidecar が欠けている場合は、再作成せず対応表を取得不能として示す。
稼働中 daemon の WAL に最近の対応表があるため、`immutable=1` で古い本体だけを正本とみなさない。
DB や履歴の修復、checkpoint、索引の書戻しは検索の操作に含めない。

## 保存形式を直接調べる場合

### Claude Code 履歴

```bash
# マッチしたプロジェクト名だけ表示（基本）
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u

# ファイルパスまで表示
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl"

```

Claude のプロジェクトキーは `/`、`.`、元からの `-` を区別できない。
`-` を `/` に置換して実パスを捏造せず、helper の `cwd`、元 transcript の metadata、実在する候補ディレクトリを照合する。
`cwd` がないときはキー名を候補のまま示す。

### Codex CLI 履歴

```bash
# 1. 保存された入力テキストから検索して session_id を得る（軽量な入口）
grep -i "キーワード" ~/.codex/history.jsonl

# 2. session_id から rollout 本体を特定（ファイル名末尾が session_id）
find ~/.codex/sessions -name "*<session_id>.jsonl"

# アシスタント応答まで含めて全文検索したい場合
# （システムプロンプト由来の誤ヒットに注意。固有性の高い語で絞る）
grep -rl "キーワード" ~/.codex/sessions --include="*.jsonl"

# プロジェクト（cwd）でセッションを絞り込む
grep -rl '"cwd":"[^"]*<プロジェクト名の断片>' ~/.codex/sessions --include="*.jsonl"

# セッション名の索引を眺める（本文の発言履歴ではない）
grep -i "キーワード" ~/.codex/session_index.jsonl
```

## 単純なキーワード検索を超えた用途

エラー率の集計、同一文字列の異常反復（degeneration）検出、特定期間のセッション一覧など、grep 一発では終わらないクエリは [references/recipes.md](references/recipes.md) の再利用可能なレシピを参照する（Claude Code 履歴の jsonl 構造前提。Codex 履歴に流用する場合はフィールド名の読み替えが必要）。ゼロから正規表現を組み立て直すと試行錯誤が数回に及びやすい。

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

## resume へのつなぎ方

### Claude Code

見つかったプロジェクトのディレクトリで起動して `/resume` する。

```bash
cd $HOME/<your-project> && claude
# → /resume
```

### 通常の Codex

結果の `codex_home` と `cwd` を確認し、保存時の state directory を使って `codex resume <session_id>` を実行する。
現在の `CODEX_HOME` が異なれば、通常の picker や UUID 指定だけではその履歴を見つけられない。
検索だけを求められた場合は再開を実行せず、出典と再開先を返す。

### Discord 経由の Codex

原則は結果の `channel_id` と `thread_ids` が示す元の Discord スレッドで続ける。
専用の `codex_home` とコンテナー内 cwd があるため、通常の `~/.codex` に対して同じ UUID を渡しても同じ実行環境にはならない。
ホスト上での再開を明示的に求められた場合は、元の state directory、workspace、認証、接続機器などの実行条件を確認する。
履歴を移動したり、他チャンネルに状態や認証情報をコピーしたりして解消しない。
