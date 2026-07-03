# スキルスクリプトのテスト設計チェックリスト

Claude Code のスキル（主にシェルスクリプト）に `scripts/` を含める場合のテスト設計指針。
実際のスキル開発（move-project）と Codex (GPT-5.3) のレビューから蒸留した知見。
[meta-rules](../SKILL.md) の「動作検証」節から参照される。

## 核心原則: ツール境界の引き方

> **エージェントは「仮説生成・実験設計」まで担当。「事実生成・観測・判定」はツールに委ねる。**
> 境界は「知識量」ではなく「反証可能性」と「観測可能性」で引く。

エージェントが「やるべきでないこと」と対応ツール:

| やるべきでないこと | 理由 | 対応ツール |
|---|---|---|
| テスト入力を自分で作り自分で評価 | 生成器と判定器が同一知識源 → 盲点が固定化 | Radamsa, AFL++, Hypothesis |
| OS/実装差分を推論で吸収 | 差分は知識問題でなく実行環境問題 | Docker matrix, Nix flakes |
| 副作用を目視・推測で判断 | mtime/権限/FDは推測不能 | inotifywait, dtrace, fs snapshot diff |
| 正しさを自然言語仕様だけで決める | 「正しい出力」より「壊れない変換関係」の方が検証しやすい | differential testing, metamorphic testing |
| 再現性のないテストを通過判定に使う | 不安定な失敗は資産化できない | SEED固定, delta debugging |

---

## 1. 実データからテストデータを逆算せよ

自作テストデータはエージェント自身の「知識の偏り」を反映する。
実環境に存在するパターンを先にサンプリングしてからテスト設計する。

```bash
# 例: Claude Code のプロジェクトキー命名規則を観察してからテスト設計
ls ~/.claude/projects/ | head -20
# → 発見: gitlab.example.com → gitlab-example-com（. も - に変換）
# → この発見がなければ FZ-01 のバグは見つからなかった
```

**Seed Corpus の作り方（Codex 推奨）:**
```bash
# 実データを層化サンプリングしてバケット化
awk '
function bucket(s) {
  if (s ~ /\./) return "dot"         # ドット含む
  if (length(s) >= 64) return "long" # 長いパス
  if (s ~ /[[:space:]]/) return "space"
  if (s ~ /[^[:alnum:]_\/\.-]/) return "symbol"
  return "normal"
}
{ if (count[bucket($0)] < 50) print }
' real_paths.txt > seed_corpus.txt
```

---

## 2. 副作用ごとにテスト層を分けよ

| 層 | 対象 | 例 |
|---|---|---|
| **ユニット** | 純粋関数・変換処理 | `_escape_sed_pattern` 単体 |
| **統合** | スクリプト全体の入出力 | `migrate.sh src dst` |
| **副作用** | ファイルシステムへの影響 | mtime・permissions・バイナリ |
| **失敗注入** | ロールバック動作 | mv権限不足・途中中断 |

```bash
# 副作用テンプレート（macOS/Linux 両対応）
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cp fixture.jsonl "$tmp/f.jsonl"

# mtime を記録
before=$(stat -f %m "$tmp/f.jsonl" 2>/dev/null || stat -c %Y "$tmp/f.jsonl")

bash migrate.sh "$tmp/src" "$tmp/dst"

# アウトカムを直接検証
grep -q '"/dst"' "$tmp/dst/f.jsonl"          || echo "FAIL: path not updated"
after=$(stat -f %m "$tmp/dst/f.jsonl" 2>/dev/null || stat -c %Y "$tmp/dst/f.jsonl")
[ "$after" -eq "$before" ]                   || echo "FAIL: mtime changed"
[ ! -d "$tmp/src" ]                          || echo "FAIL: src still exists"
```

---

## 3. ファジング優先チェックリスト（シェルスクリプト向け）

```
入力の多様性:
□ セデリミタ文字を含むパス（| @ # など）
□ 正規表現特殊文字（. * [ ] ^ $）
□ スペース・タブを含むパス
□ ドット入りコンポーネント（domain.com → キー変換に影響）
□ 非常に長いパス（255バイト近く）
□ Unicode・日本語
□ src と dst がプレフィックス関係（/tmp/foo と /tmp/foo-new）

環境の多様性（Environment Fuzzing）:
□ locale, TZ, umask の差異
□ macOS(BSD) vs Linux(GNU) の sed/grep/stat 差分
□ mtime の粒度・clock skew
□ バイナリファイルが混在するディレクトリ
□ ファイルシステム種別（APFS, ext4, NFS）

ツール:
- Radamsa: radamsa input.txt | ./script.sh  （シェル向け汎用ファジング）
- ShellCheck: 静的解析（クォート・グロビング問題の早期検出）
- Bats / ShellSpec: 構造化テストフレームワーク
```

---

## 4.「動いた」と「正しく動いた」を区別せよ

終了コード 0 ≠ 正しく動いた。無言の失敗が最も危険。

```bash
# 実際に起きた事故: BSD sed が空文字を返しても終了コード 0
_escape_sed_pattern() {
  printf '%s' "$1" | sed 's/[]\[.^$*\\]/\\&/g'
  # BSD sed: unbalanced brackets → 空文字を返す
  # 後続の sed が「/ を全部 dst/ に置換」という壊滅的誤動作
}

# 検出方法: 関数出力を UNIT テストで直接検証
result=$(_escape_sed_pattern "/tmp/test.dir")
[ "$result" = "/tmp/test\.dir" ] || echo "FAIL: escape broken, got: $result"
```

**仕様の不変条件（invariant）を明文化する（Codex 推奨）:**
- 「対象外ファイルは 1 バイトも変わらない」
- 「変換後のキーは全プロジェクトで一意」
- 「dst が存在する場合は src を移動しない」

---

## 5. エントロピーの導入：エージェントの「無知の無知」を検出する

エージェントが自分で「生成・実行・判定」を完結させると盲点が固定化する。
**Cross-model-play** が有効: 別モデルに「反証ケースだけ」作らせる。

```
自己一致率が高い = 危険シグナル
→ 同一エージェントで生成・実行・判定を閉じるほど盲点が固定化する

エントロピー導入の手法:
1. Seed Corpus（実データ匿名化）+ Mutation（SEED固定で再現可能）
2. Metamorphic testing: 入力が変わっても守る「関係」を先に定義
3. Cross-model-play: Claude が設計したテストを Codex/Gemini に壊させる
4. Environment fuzzing: locale/TZ/FS種別/umask をランダム変化させる
5. Oracle fuzzing: 判定器（テストハーネス）自体を壊しにいく
```

---

## 6. 人間が介入すべき最小の3点（Codex 推奨）

自動化できる部分と人間が承認すべき部分を分ける:

1. **不変条件の承認** — 「何を壊したら失敗とするか」の定義
2. **危険副作用境界の承認** — 「書込先・削除対象・権限変更の範囲」
3. **昇格判定の承認** — 「CI通過を本番可とみなす閾値」

この 3 点以外は自動化しても品質を落としにくい。

---

## 7. 見落とされがちな観点（Codex 指摘）

1. **テストハーネス自体のバグ** — diff・終了コード解釈・grep のオプションが壊れているケース（今回: `grep -q "$VAR"` で変数が `-` 始まりだとオプション解釈された）

2. **ファイルシステム意味論** — mtime 粒度・rename 原子性・`sed -i` の実装差・NFS/overlayfs が本体バグを生む

3. **終了コード契約の曖昧さ** — stdout 一致だけ見て stderr/終了コード契約を見ないと「成功扱いの失敗」を量産する

---

## 8. ライブ外部環境を操作するスキルのテスト

GUI アプリ・実機・SaaS ダッシュボードなど、**巻き戻せる sandbox が存在しない外部環境**を操作するスキル（例: EasyEDA のような EDA クライアント）は、上記の 4 層テストがそのまま適用できない。ファイルシステムと違い `mktemp -d` で使い捨てられず、テストの副作用がユーザーの実環境に残り続ける。

実際に起きた事故: EasyEDA 操作スキルの empirical testing で、テスト実行のたびにユーザーのサンプルプロジェクト内へ匿名の `Board1`〜`Board8` が堆積し、並列実行では複数エージェントが同じ GUI ウィンドウを取り合って成果物が相互汚染した。

1. **専用テストフィクスチャを用意せよ** — ユーザーの実データ・実プロジェクトでテストしない。専用のテストプロジェクト/サンドボックスを作るか、テスト先をユーザーに確認してから着手する。

2. **テスト成果物に命名規約を課せ** — テストが作る資源には `test-<日付>-<目的>` のような識別可能なプレフィックスを付け、後から一括発見・クリーンアップできるようにする。`Board1` `Untitled` のような匿名リソースの堆積は環境そのものを汚す。

3. **1環境1エージェントを守れ** — GUI アプリ・実機・単一ウィンドウのような単一インスタンスのライブ環境に対する並列テストは禁止。直列化するか、環境インスタンス自体を分離する。

4. **クリーンアップ手順をテスト設計に含めよ** — 削除操作が破壊的で自動化すべきでない場合は、作成した資源の一覧（UUID・名前）をレポートに残し、人間が後で安全に消せるようにする。

5. **リセット不能な環境では汚染を最小化せよ** — 巻き戻し手段がない環境では、新規リソースの追加のみをテストで許可し、既存リソースの変更・削除はテストで行わない。

---

## 副作用観測ツールの実用性マトリクス

| ツール | macOS CI | Linux CI | 備考 |
|---|---|---|---|
| `opensnoop` / `dtrace` | △ SIP制限あり | - | ローカル開発では有効 |
| `inotifywait` | - | ○ | CI で最も使いやすい |
| `fanotify` | - | ○ (kernel 5.12+) | 高機能だが権限必要 |
| `fs snapshot diff` | ○ | ○ | 独自実装が手軽 |
| Bats / ShellSpec | ○ | ○ | テストフレームワーク本命 |
| ShellCheck | ○ | ○ | 静的解析、まず入れる |
| Nix flakes | ○ | ○ | BSD/GNU sed 差分の根本解決 |

---

## チェックリスト

```
テスト設計前:
□ 実環境をサンプリングして命名規則・データ形式を把握したか
□ OS・ツールのバージョン固有の挙動を調べたか
□ 不変条件（invariant）を言語化したか

テスト設計中:
□ ユニット・統合・副作用・失敗注入の4層に分けたか
□ ファジング対象（特殊文字・OS差異・環境）を洗い出したか
□ 終了コードだけでなくアウトカムを検証しているか
□ テストハーネス自体の正しさを確認したか

テスト実施後:
□ 実データで動かして確認したか（テストデータとの乖離チェック）
□ 別モデル・別エージェントに反証ケースを作らせたか
□ PASS の理由が「偶然」ではないか（偽陽性チェック）
```
