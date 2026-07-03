---
name: history-search
description: "全プロジェクトの Claude Code 会話履歴を横断検索する。過去のトピックを調べたいとき、/resume したいがディレクトリを忘れたときに使う。単純なキーワード検索以外の分析的クエリ（エラー率集計・繰り返し検出等）は references/recipes.md を使う。ディレクトリ名から実パスを逆算するだけの用途なら対象外（後述の落とし穴があるので、まず ls で確認する）。キーワード: 履歴検索, history, resume, 過去の会話"
---

# history-search - Claude Code 履歴横断検索

全プロジェクトの Claude Code 会話履歴を横断して検索するスキル。

## When to Use

- どのプロジェクトで特定のトピックを調べたか思い出せないとき
- 過去の会話を横断的に検索したいとき
- `/resume` したいがディレクトリを忘れたとき

## 履歴の保存場所

```
~/.claude/projects/<プロジェクトパス>/   # ディレクトリ名は実パスの / と . を両方 - に置換
    <session-uuid>.jsonl                 # 1ファイル = 1会話
~/.claude/history.jsonl                  # グローバル履歴
```

**既知の落とし穴**: `/` だけでなく `.` も `-` に変換される。例えば `gitlab.photosynth.dev` は `gitlab-photosynth-dev` になる。「実パスの `/` を `-` に置換すればディレクトリ名になる」という思い込みで手で組み立てると、`.` の変換漏れで存在しないディレクトリを grep して `Exit code 2` になる（実際に踏んだ実障害）。

**決め打ちで再構成せず、まず一覧から確認する**:

```bash
ls ~/.claude/projects/ | grep -i <キーワードの断片>
```

これでディレクトリ名を確定してから、必要なら以降のコマンドで対象を絞り込む。

## 検索コマンド

### マッチしたプロジェクト名だけ表示（基本）

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u
```

### ファイルパスまで表示

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl"
```

### プロジェクト名を実パスに変換して表示

```bash
grep -rl "キーワード" ~/.claude/projects/ --include="*.jsonl" \
  | sed 's|.*projects/\([^/]*\)/.*|\1|' | sort -u \
  | sed 's|^-||; s|-|/|g'
```

> ディレクトリ名の先頭の `-` を除去し、残りの `-` を `/` に戻す。ただし元の実パスに `.` が含まれていた場合、この変換では `.` は復元されない（`/` と `.` は両方 `-` に潰れているため、`-` から先の区切りだけでは元の文字を一意に復元できない）。正確な実パスが必要なら `ls ~/.claude/projects/` の一覧と照合するか、`claude --resume` の候補一覧で確認する。

## 単純なキーワード検索を超えた用途

エラー率の集計、同一文字列の異常反復（degeneration）検出、特定期間のセッション一覧など、grep 一発では終わらないクエリは [references/recipes.md](references/recipes.md) の再利用可能なレシピを参照する。ゼロから正規表現を組み立て直すと試行錯誤が数回に及びやすい（実際に6回近く書き直した例がある）。

## /resume へのつなぎ方

検索で見つかったプロジェクトのディレクトリで Claude Code を起動し、`/resume` すれば続きから再開できる。

```bash
# 例: $HOME/<your-project> で再開
cd $HOME/<your-project> && claude
# → /resume
```
