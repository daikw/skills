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

**既知の落とし穴**: `/` だけでなく `.` も `-` に変換される。例えば `gitlab.example.com` は `gitlab-example-com` になる。「実パスの `/` を `-` に置換すればディレクトリ名になる」という思い込みで手で組み立てると、`.` の変換漏れで存在しないディレクトリを grep して `Exit code 2` になる（実際に踏んだ実障害）。

**決め打ちで再構成せず、まず一覧から確認する**:

```bash
ls ~/.claude/projects/ | grep -i <キーワードの断片>
```

### Codex CLI

```
~/.codex/sessions/<YYYY>/<MM>/<DD>/
    rollout-<timestamp>-<session-uuid>.jsonl   # 1ファイル = 1セッション、日付別に格納
~/.codex/history.jsonl        # 全セッションのユーザー発言のみ {session_id, ts(unix秒), text}
~/.codex/session_index.jsonl  # セッション名の索引 {id, thread_name, updated_at}
```

**Claude Code と構造が根本的に違う点**（推測しにくいので明記）:

- **プロジェクト別ではなく日付別**。ディレクトリにもファイル名にもプロジェクト情報がない。作業ディレクトリは各 rollout ファイル先頭行の `session_meta` に `"cwd":"..."` として入っている
- **rollout ファイルは先頭行にシステムプロンプト全文（`base_instructions`）を含む**。一般的な語で全文 grep すると全ファイルにヒットして検索にならない。まず `~/.codex/history.jsonl`（1 行 = 1 ユーザー発言）で当たりをつけ、`session_id` からファイルを特定するのが速くて確実
- `session_index.jsonl` は全セッションを網羅しない（rollout ファイル数より大幅に少ないことがある）。索引にないからといってセッションが存在しないとは限らない

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

> 最後の変換は、ディレクトリ名の先頭の `-` を除去し、残りの `-` を `/` に戻す。ただし元の実パスに `.` が含まれていた場合は復元されない（`/` と `.` は両方 `-` に潰れているため一意に戻せない）。正確な実パスが必要なら `ls ~/.claude/projects/` の一覧と照合するか、`claude --resume` の候補一覧で確認する。

### Codex CLI 履歴

```bash
# 1. まずユーザー発言から検索して session_id を得る（軽い・誤ヒットしない）
grep -i "キーワード" ~/.codex/history.jsonl

# 2. session_id から rollout 本体を特定（ファイル名末尾が session_id）
find ~/.codex/sessions -name "*<session_id>.jsonl"

# アシスタント応答まで含めて全文検索したい場合
# （システムプロンプト由来の誤ヒットに注意。固有性の高い語で絞る）
grep -rl "キーワード" ~/.codex/sessions --include="*.jsonl"

# プロジェクト（cwd）でセッションを絞り込む
grep -rl '"cwd":"[^"]*<プロジェクト名の断片>' ~/.codex/sessions --include="*.jsonl"

# セッション名（初回発言）の索引を眺める
grep -i "キーワード" ~/.codex/session_index.jsonl
```

## 単純なキーワード検索を超えた用途

エラー率の集計、同一文字列の異常反復（degeneration）検出、特定期間のセッション一覧など、grep 一発では終わらないクエリは [references/recipes.md](references/recipes.md) の再利用可能なレシピを参照する（Claude Code 履歴の jsonl 構造前提。Codex 履歴に流用する場合はフィールド名の読み替えが必要）。ゼロから正規表現を組み立て直すと試行錯誤が数回に及びやすい。

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
