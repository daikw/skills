---
name: history-search
description: "Claude Code と Codex CLI 両方の会話履歴を全プロジェクト横断で検索する。過去のトピックをどちらのハーネスで話したか思い出せないとき、resume したいがディレクトリやセッションを忘れたときに使う。Claude Code / Codex CLI のどちらから起動しても、両方の履歴を検索対象にできる。単純なキーワード検索以外の分析的クエリ（エラー率集計・繰り返し検出等）は references/recipes.md を使う。ディレクトリ名から実パスを逆算するだけの用途なら対象外（後述の落とし穴があるので、まず ls で確認する）。キーワード: 履歴検索, history, resume, 過去の会話, codex 履歴, セッション検索"
---

# history-search - Claude Code / Codex CLI 履歴横断検索

Claude Code と Codex CLI、両方の会話履歴を横断して検索するスキル。検索は素の `grep` / `find` なので、どちらのハーネスから起動しても同じ手順で両方の履歴を検索できる（起動元 × 検索先の 4 通りすべて同一手順）。ユーザーがハーネスを指定しない限り、両方の履歴を検索する。

## 履歴の保存場所

### Claude Code

```
~/.claude/projects/<プロジェクトパス>/   # ディレクトリ名は実パスの / と . を両方 - に置換
    <session-uuid>.jsonl                 # 1ファイル = 1会話
~/.claude/history.jsonl                  # グローバル履歴
```

**既知の落とし穴**: `/` だけでなく `.` も `-` に変換される。例えば `gitlab.example.com` は `gitlab-example-com` になる。「実パスの `/` を `-` に置換すればディレクトリ名になる」という思い込みで手で組み立てると、`.` の変換漏れで存在しないディレクトリを grep して `Exit code 2` になる（過去に発生した障害）。

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

## 検索コマンド

### Claude Code 履歴

```bash
# マッチしたプロジェクト名だけ表示（基本）
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u

# ファイルパスまで表示
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl"

# プロジェクト名を実パスに変換して表示
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u \
  | sed 's|^-||; s|-|/|g'
```

> 最後の変換は、ディレクトリ名の先頭の `-` を除去し、残りの `-` を `/` に戻す。ただし元の実パスに `.` が含まれていた場合は復元されない（`/` と `.` が両方とも `-` に変換されているため一意に戻せない）。正確な実パスが必要なら `ls ~/.claude/projects/` の一覧と照合するか、`claude --resume` の候補一覧で確認する。

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

### Codex CLI

session_id を直接指定できるので、ディレクトリ移動は不要。

```bash
codex resume <session_id>   # UUID 直接指定
codex resume --last         # 直近セッションを継続
codex resume                # picker で選択
```
