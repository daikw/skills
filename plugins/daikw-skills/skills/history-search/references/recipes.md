# history-search レシピ集

単純なキーワード検索を超えた分析的クエリのための、再利用可能な grep/awk/python レシピ集。

## エラー率が高いセッションを探す

会話 jsonl の各行は 1 メッセージ相当の JSON。`is_error` フィールドが true の行数と全行数の比率で判定する。

```bash
for f in ~/.claude/projects/*/*.jsonl; do
  total=$(wc -l < "$f")
  errors=$(grep -c '"is_error":true' "$f" 2>/dev/null || echo 0)
  [ "$total" -gt 0 ] && [ "$errors" -gt 0 ] && \
    awk -v e="$errors" -v t="$total" -v f="$f" 'BEGIN{printf "%.2f\t%d/%d\t%s\n", e/t, e, t, f}'
done | sort -rn | head -20
```

`grep -c` は無出力（マッチ0件）だと空文字を返すことがあるので `|| echo 0` でフォールバックする。

## 同一文字列の異常反復（degeneration）を検出する

モデルが同じトークン列を吐き続けて壊れているセッションを探す。「直近 N 行のうち同一文字列が M 回以上連続する」というヒューリスティックが実用的。

```bash
# 各セッションの assistant テキストから最頻出行を抽出し、出現回数の偏りを見る
for f in ~/.claude/projects/*/*.jsonl; do
  python3 -c "
import json, sys, collections
lines = []
for line in open('$f'):
    try:
        obj = json.loads(line)
    except Exception:
        continue
    content = obj.get('message', {}).get('content')
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get('type') == 'text':
                lines.append(c.get('text', '')[:80])
if not lines:
    sys.exit()
counter = collections.Counter(lines)
top, count = counter.most_common(1)[0]
if count >= 5:
    print(f'{count}\t$f\t{top!r}')
"
done | sort -rn | head -20
```

## 特定期間のセッション一覧

jsonl のファイル名（session UUID）自体には日付情報がないため、mtime かファイル内の最初の timestamp を使う。

```bash
# mtime ベース（ファイルの最終更新日で絞る）
find ~/.claude/projects/ -name "*.jsonl" -newermt "2026-06-01" ! -newermt "2026-07-01"

# ファイル内の最初のメッセージの timestamp で絞る（より正確）
for f in ~/.claude/projects/*/*.jsonl; do
  ts=$(head -1 "$f" | python3 -c "import json,sys; print(json.loads(sys.stdin.read()).get('timestamp',''))" 2>/dev/null)
  [ -n "$ts" ] && echo -e "$ts\t$f"
done | sort | awk -F'\t' '$1 >= "2026-06-01" && $1 < "2026-07-01"'
```

## available-skills 誤検出を避ける

スキル名や `daikw:` プレフィックスは system-reminder に毎ターン全件注入されるため、単純な `grep -rl "<skill名>"` は「言及」を大量に誤検出する（数百件単位）。実際の起動を数えたいときは以下のいずれかに絞る。

```bash
# Skill tool 経由の起動(厳密一致)
grep -o '"name":"Skill","input":{"skill":"daikw:<name>"' ~/.claude/projects/*/*.jsonl

# スラッシュコマンド形式の起動
grep -o '<command-name>/daikw:<name></command-name>' ~/.claude/projects/*/*.jsonl
grep -o '<command-name>/<name></command-name>' ~/.claude/projects/*/*.jsonl  # プレフィックスなし(ローカル配置経由)
```
