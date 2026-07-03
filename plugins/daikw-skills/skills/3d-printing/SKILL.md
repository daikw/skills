---
name: 3d-printing
description: "STL から 3D プリントまでの一気通貫ワークフロー。slicer 選定・印刷ジョブ投入・進捗監視・完了確認を支援する。LAN 上のプリンタを自動検出し、機種別の API/プロトコル差を吸収する。印刷空間にカメラがあれば、開始時のベースライン + 完了時のスナップショットを取得して結果を視覚的に検証する。過去の印刷履歴やアーカイブ済みファイルの調査目的では使わない（リアルタイム操作専用）。キーワード: 3D プリント, FDM, 印刷, スライス, Creality, K1 Max, OrcaSlicer, PrusaSlicer, gcode, STL, mjpg-streamer"
---

# 3D Printing Skill

STL → スライス → アップロード → 印刷開始 → 監視 → 完了確認 までの一連を支援する。LAN プリンタの検出・機種別プロトコル吸収・カメラ起点の視覚検証も含む。

**Freedom Level: 中** — 大筋（スライス → 投入 → 監視 → 検証）は固定。slicer 選定・サポート設定・camera 取り扱いは状況依存。物理リソース（フィラメント・時間）を消費する操作なので、**印刷開始の最終 Go は必ずユーザ承認を取る**。

---

## When to Use

- "STL を印刷して" / "K1 で印刷" / "FDM で出力" 等の依頼
- 印刷状況の確認 / 監視ループの設計
- 新しいプリンタを LAN に追加した時の検出・接続性確認
- 既存印刷ジョブの pause/stop/resume

## When NOT to Use

- CAD モデリングそのもの（ForgeCAD / Fusion / OnShape 等の作業）→ そちらのツール
- 印刷後の後処理（サポート除去・研磨）の物理作業 → そもそも Claude の射程外
- スライサーの GUI 越しの細かい設定調整 → 一発勝負ならこのスキル、対話的なら slicer を直接開く

---

## 前提

- `~/ghq/<host>/<owner>/<repo>` 配下に印刷したい STL がある（自分の repo 推奨）
- macOS の場合: OrcaSlicer 2.3+ が `/Applications/OrcaSlicer.app` に。`brew install --cask orcaslicer` で導入
- プリンタが同 LAN にある (`ifconfig` で同セグメント / `ping` 通る)
- `uv` で Python スクリプトを走らせる前提

不足してたら `mise use -g`, `brew install`, `ghq get` 等の導入手順を提示してからユーザ承認 → 実行する。

---

## Step 1: 操作の分類

意図で 1 つ選ぶ。曖昧なら `AskUserQuestion` で確認。

| 意図 | 操作 | 発話例 |
|---|---|---|
| プリンタを検出・接続性確認 | `discover` | 「LAN のプリンタ探して」「K1 検出」 |
| STL を slice する | `slice` | 「これスライスして」「gcode 作って」 |
| slice 済の gcode を印刷投入 | `print` | 「印刷投入」「キューに入れて」 |
| 進捗確認 | `status` | 「印刷状況は」「あと何分」 |
| 完了スナップショット取得 | `verify` | 「印刷物の写真撮って」「カメラで確認」 |
| pause / stop | `pause` / `stop` | 「一時停止」「止めて」 |
| STL → slice → 印刷 → 完了確認まで一気通貫 | `submit` | 「これ印刷して」「ケース作って印刷まで」 |
| 印刷履歴・過去ファイルの調査 | 対象外（このスキルはリアルタイム操作専用） | 「印刷履歴から探して」「前にプリントしたやつある?」 |

> 履歴・過去ファイル調査は discover/status のような単発 API 呼び出しでは完結しない（history/thumbnail 抽出は本スキルの守備範囲外で、WebSocket 生パケット解析等の即興実装が必要になる）。過去の印刷物や過去リポジトリの調査が目的なら `security-archaeology` のような調査系スキルに委ねるか、目的を明確にしたうえで都度アドホックに対応する。

---

## Step 2: 各操作の詳細

### `discover` — LAN プリンタ検出

mDNS で機種固有のサービス名を探す。Creality 系なら `_Creality-<hex>._udp.local.`、Prusa は `_octoprint._tcp.local.` 等。

```bash
# 全 service type を一覧
( dns-sd -B _services._dns-sd._udp local. & PID=$!; sleep 4; kill $PID ) 2>&1 \
  | awk '/Add/ {print $7}' | sort -u

# Creality 系の instance 解決
( dns-sd -B _Creality-XXXXXX._udp local. & PID=$!; sleep 3; kill $PID ) 2>&1

# IPv4 解決
( dns-sd -G v4 K1Max-XXXX.local & PID=$!; sleep 2; kill $PID ) 2>&1
```

検出後、`references/printers.md` の対応モデルを参照して、機種固有の `/info` エンドポイントで確証を取る。**機種が未登録だったら `references/printers.md` に追記**する。

**mDNS で見つからない場合のフォールバック**: 同一 LAN 上に見えていても mDNS が届かない環境がある（実際に発生した）。以下の順で切り分ける。

1. 過去に同じプリンタへ接続した記録（同一/別リポジトリのコード・設定・commit メッセージ）に IP アドレスが埋め込まれていないか `grep` する
2. 見つかった IP に直接 `curl http://<IP>/info` などで疎通確認する
3. それでも届かない場合、Tailscale 等の VPN 経由で別ホスト（プリンタと同一 LAN にいる別マシン）に SSH で入り、そちらを踏み台に到達する
4. 一度到達できたら、その IP と踏み台構成を `references/printers.md` に追記して次回の試行錯誤を防ぐ

### `slice` — STL → gcode

OrcaSlicer CLI を使う。プリセットは機種 + nozzle 径 + 層厚 + フィラメント の組合せ。

```bash
ORCA=/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer
PROF=/Applications/OrcaSlicer.app/Contents/Resources/profiles

"$ORCA" --slice 0 --outputdir gcode \
  --load-settings "$PROF/<vendor>/process/<process>.json;$PROF/<vendor>/machine/<machine>.json" \
  --load-filaments "$PROF/<vendor>/filament/<filament>.json" \
  input.stl
```

**注意点**:

- OrcaSlicer は同一 `type` の config 2 つを `;` chain で渡すと **"duplicate process config file"** で reject される。プロセスを override したい場合は **bundle profile をフルコピー → 必要 key だけ書き換え → 1 ファイルに統合** する
- `--orient` 既定は auto。ベッド範囲超過時は自動回転する
- スライス後は `head -120 gcode/plate_1.gcode` でメタデータ確認:
  - `total layer number` / `max_z_height` / `filament used` / `estimated printing time`
  - `;TYPE:Support` の出現数で supports 検知
- サポート要否は overhang 角度で決まる (`detect_overhang_wall`, `support_threshold_angle`)。Bridge で済む 5mm 以下の overhang は不要だが、それ以上は支持材推奨

### `print` — gcode を投入 + 開始

機種別。`references/printers.md` の "upload + start" セクションを参照。Creality K1/K1 Max は:

```bash
# upload (HTTP POST multipart に "file" フィールド)
curl -F "file=@gcode/plate_1.gcode;filename=my-print.gcode" http://<IP>/upload

# start (WebSocket port 9999, JSON-RPC)
# {"method":"set","params":{"opGcodeFile":"printprt:/usr/data/printer_data/gcodes/my-print.gcode"}}
```

対象リポジトリ側（このスキル自体には同梱しない）に、機種別の upload/start をまとめたラッパースクリプト（例: `tools/print_k1.py`）を置く運用が現実的。

**印刷投入前に必ず実施**:

1. `slice` の出力ログをユーザに提示（時間・物量・supports 件数・bbox）
2. **CAD-as-code 由来 (forgecad / build123d / cadquery 等) なら、印刷物本体にモデル名 + バージョンを凹彫りで入れる**。例: `PARTS-TRAY V2`。底面・裏面・邪魔にならない床面など、機能を損ねず印刷後に読める場所を選ぶ。ForgeCAD なら `text2d(...).onFace(...).extrude(...)` を `subtract` / `cutout` で浅く彫る。既製 STL で編集困難な場合だけ、別途タグ/ラベル形状を同時印刷する。
3. **CAD-as-code 由来 (forgecad / build123d / cadquery 等) なら設計を 3〜4 アングルで render してユーザに提示**。 top / iso / side を最低限、 隠れた特徴 (穴 / 内部ポケット / 段差) があれば section view か裏側 view も。 数値検証 (bbox / volume / assert) と render 目視は **直交する failure mode** を捕えるので両方必要 — bbox が正しくても CSG boolean の順序ミスで穴が塞がってる、 みたいなのは render を見ないと気付かない
4. ベッド状態確認 (前のプリントが残ってないか) — カメラがあれば snapshot で確認
5. ユーザに **「投入していい？」と明示確認**を取る (物理リソース消費)
6. 確認取れたら `submit`

> 例外: 既製 STL (CAD コードなし) は 2 をスキップ。 同じ CAD で preset 比較だけなら初回 render で OK。

### `status` — 進捗確認

機種別。Creality 系は `:9999` WS で `{"method":"get","params":{"reqPrinter":1}}` → `state / printProgress / printJobTime / printLeftTime / nozzleTemp / bedTemp0` 等。

判定:
- `state = 1, printProgress = 100, printJobTime > 0` → 完了
- `state = 0` または `deviceState = 0` → idle
- `err.errcode != 0` → エラー（コード詳細は機種依存）

### `verify` — カメラスナップショット取得

**印刷空間にカメラがある場合は、開始時と完了時の 2 枚を最低必ず取る**。

```bash
# Creality K1 系: mjpg-streamer
curl -o "$ARTIFACT_DIR/baseline.jpg" http://<IP>:8080/?action=snapshot   # 印刷前
# ... 印刷 ...
curl -o "$ARTIFACT_DIR/complete.jpg" http://<IP>:8080/?action=snapshot   # 完了時
```

詳細 (機種別カメラ URL、ストリーム vs スナップショット、復活手順) は `references/camera-verification.md` 参照。

### `submit` — 一気通貫

`slice` → ユーザ確認 → `print` → `status` polling → 完了で `verify` を自動的に流す。各段でユーザ介入ポイントを残す。

擬似フロー:

```
1. slice            (出力: layer数/時間/物量)
2. engraving check  (CAD-as-code のみ — モデル名 + バージョンの凹彫りを確認)
3. design render    (CAD-as-code のみ — top/iso/side + 必要なら section)
4. pre-flight       (supports 件数、レイアウト、bridge 件数)
5. baseline 撮影    (カメラあれば — ベッドが空かの目視確認用)
6. ユーザ確認       「render + 物量 6cm³ / 15 分 / supports 32 件。印刷投入してよし？」
7. upload + start
8. status polling   (60-90 秒間隔)
9. 完了検知
10. complete 撮影    (カメラあれば)
11. baseline vs complete を並べてユーザに提示
```

---

## Step 3: 完了後の記録

印刷物の物理確認は人間しかできない。Claude 側でできるのは:

- 今回の印刷の目的に直接紐づく成果物（gcode / STL / レンダ / baseline.jpg / complete.jpg）を repo に commit する。**「一律すべて commit」ではなく、目的に紐づくものだけを選ぶ**（例: セキュリティ調査など別タスクのついでに撮った写真を、無関係な commit に混入させない）
- 物量・時間・supports 件数を WorkItem (GitLab/Notion) に note 投稿
- ユーザに「物理確認お願い」の依頼を明示

完了確認の note 例 (physai-tasks 経由で GitLab に投稿する場合):

```
### 印刷完了 (2026-05-18 20:03)

- 投入: pi-pico-case-v6-20260518-1948.gcode (520 KB)
- 結果: state=2, printJobTime=15m32s (見積もり 14m42s から +0.8 分)
- baseline / complete スナップショットを添付
- 物理確認: <ユーザによる>

[baseline]  ← <upload from camera/baseline.jpg>
[complete]  ← <upload from camera/complete.jpg>
```

---

## 安全ルール

- **印刷ジョブの開始** = 物理リソース消費 + ロールバック不能 → **必ずユーザ承認後**
- CAD-as-code 由来の印刷物は、モデル名 + バージョンを読める凹彫りで本体に入れてからスライスする。
- **stop** は最終手段。pause で済むなら pause（resume できる）
- スライサ override profile を OrcaSlicer の bundle 上に直接書かない。**対象リポジトリ側（例: `tools/print-profiles/`）に置く**
- カメラスナップショットを Slack/GitLab 等の外部に流すとき: プライバシー範囲を意識する (背景に映る作業環境)

---

## Anti-patterns

- スライスせずに `.stl` を直接プリンタへ流そうとする → プリンタは gcode しか食わない
- プリセットを毎回手打ち → 対象リポジトリ側に preset wrapper（例: `tools/slice.py`）を置く
- `enable_support=1` を CLI flag で渡そうとする → OrcaSlicer は flag を持たない、profile JSON で渡す
- 自動 stop ロジックを単一フレーム判定で組む → false positive が高すぎる。N 連続検知 + 進捗段階別閾値が現実解 (`docs/print-monitoring-llm-as-judge.md` 参照例)
- 印刷投入時にカメラを叩かない → 完了時に bed が空かどうか後から検証できなくなる
- プリンタを ROOT/Helper Script 改造ありき → stock firmware で叩ける API があるなら、保証維持のためそちらを優先

---

## References

- [printers.md](references/printers.md) — 機種別スペック・プロトコル・upload/start エンドポイント
- [camera-verification.md](references/camera-verification.md) — 印刷前後のスナップショット運用

---

## Checklist (印刷投入時)

- [ ] STL が動作確認済み（CAD ツール側で衝突・寸法検証済み）
- [ ] CAD-as-code 由来なら、印刷物にモデル名 + バージョンの凹彫りが入っている
- [ ] スライス結果のメタデータ (time/material/supports) をユーザに提示した
- [ ] **ユーザ承認**を取った（物理リソース消費の明示）
- [ ] カメラがあれば baseline.jpg を取った
- [ ] 投入後、status polling で開始確認した
- [ ] 完了検知後、complete.jpg を取った
- [ ] gcode / STL / レンダ / スナップショット を repo に commit した
