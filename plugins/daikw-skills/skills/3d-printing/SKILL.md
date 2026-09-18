---
name: 3d-printing
description: "STL のスライス、FDM プリンタの検出、印刷投入、進捗確認、停止、カメラ確認を行う。Creality K1 Max 等の機種別プロトコルと OrcaSlicer の設定を参照し、依頼された工程を進める。利用可能な機種専用スキルがあれば優先する。CAD モデリング、過去の印刷履歴やアーカイブ調査には使わない。"
---

# 3D Printing Skill

STL → スライス → アップロード → 印刷開始 → 監視 → 完了確認 までの一連を支援する。LAN プリンタの検出・機種別プロトコル吸収・カメラ起点の視覚検証も含む。

依頼された工程だけを実施する。スライスだけの依頼にプリンタ接続や印刷許可は不要。
印刷開始は、対象プリンタ・成果物・設定について得たユーザーの明示許可の範囲で行う。既にその投入を許可されていれば聞き直さず、対象や設定が変わり許可の範囲が変わる場合だけ確認する。
利用可能な機種専用スキル・検証済み手順が対象機種と作業に合う場合は優先する。例えば Bambu Lab H2D Pro には `printing-with-bambu-h2d-pro` が利用できる場合がある。別機種の API や状態値を流用しない。

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

## 工程ごとの前提

- スライス: 入力 STL/3MF と出力先、対象機種・ノズル・材料・必要な造形条件、対応する既存 slicer/profile。入力は任意の許可された場所でよく、LAN 到達性は不要。
- 投入・制御: 対象プリンタの識別と現在の状態、許可された接続経路、機種・firmware に合う操作方法。
- カメラ確認: 対象機器のカメラと取得権限、画像の保存先。未接続のカメラを直すために印刷中の機器を再起動しない。

必要な能力がない工程だけを未実施として分け、既存ツールで進められる準備は進める。インストールやネットワーク設定変更を一律の開始条件にせず、必要になった場合に固定版・供給元を確認して通常の導入方針に従う。

---

## Step 1: 操作の分類

依頼の意図と会話で対象・工程を選ぶ。成果や操作対象を変える不明点だけ確認する。

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

検出は候補の発見であり、接続先の確定ではない。`references/printers.md` の対応モデルを参照し、その機種が提供する識別情報で機種・firmware・個体を照合する。`/info` は Creality K1 Max の例であり、他機種に存在すると仮定しない。未登録機種は公式資料や検証済み手順で必要な操作を確認する。

**mDNS で見つからない場合のフォールバック**: 同一 LAN 上に見えていても mDNS が届かない環境がある（実際に発生した）。以下の順で切り分ける。

1. 対象プリンタの既知の運用記録・設定から候補の接続先を確認する。秘密を含む設定全文や無関係な履歴を検索・出力しない
2. 許可された候補に機種固有の読み取り操作を行い、現在の機器を照合する。古い IP アドレスだけで対象と断定しない
3. 直接届かない場合は、既に許可された VPN・踏み台等の接続経路を使う。接続のために権限や公開範囲を広げない
4. 到達できた IP・内部ホスト名・踏み台構成は、アクセス範囲を確認した private skill または非公開の対象プロジェクトの運用記録に残す。公開スキルの `references/printers.md` には機種・プロトコル・匿名化した接続例だけを追記する。永続メモリへの記録は、ユーザーが明示的に依頼した場合に限る

### `slice` — STL → gcode

対象機種に対応する既存 slicer と profile を使う。以下は OrcaSlicer CLI の例。プリセットは機種 + nozzle 径 + 層厚 + フィラメントの組合せで確認する。入力原本と出力先を識別し、原本や既存の gcode を意図せず上書きしない。

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
- サポート要否は形状・向き・材料・機種/profile の対応範囲と toolpath で確認する (`detect_overhang_wall`, `support_threshold_angle`)。一律の bridge 長で不要と断定しない
- 元モデルの形状を、印刷識別のためだけに変えない。刻印や別タグが必要なら依頼された設計変更として扱う

### `print` — gcode を投入 + 開始

機種別。`references/printers.md` の "upload + start" セクションを参照。Creality K1/K1 Max は:

```bash
# upload (HTTP POST multipart に "file" フィールド)
curl -F "file=@gcode/plate_1.gcode;filename=my-print.gcode" http://<IP>/upload

# start (WebSocket port 9999, JSON-RPC)
# {"method":"set","params":{"opGcodeFile":"printprt:/usr/data/printer_data/gcodes/my-print.gcode"}}
```

対象リポジトリ側（このスキル自体には同梱しない）に、機種別の upload/start をまとめたラッパースクリプト（例: `tools/print_k1.py`）を置く運用が現実的。

**印刷投入前に確認すること**:

1. 現在の接続先が許可されたプリンタ個体・機種であり、別ジョブが動いていないこと。
2. 入力モデルと生成 gcode の対応、対象機種・ノズル・材料・ベッド寸法・配置・温度設定の一致。必要な support、穴、可動部等は toolpath/preview で確認する。CAD render が必要なら、判断したい特徴が見える視点を選ぶ。固定の枚数や無関係な刻印を要求しない。
3. ベッドが空で、必要な材料・ノズルが使用可能であること。現在のカメラ画像または対象を明示した現地確認で確かめる。古い写真や gcode サムネイルを現在のベッド確認にしない。
4. 時間・材料量等の見積もりと設定を示し、今回の投入が取得済みの許可に含まれること。足りない許可だけを確認する。
5. アップロードしたファイルが意図した gcode に対応することを、機種の利用可能な照合方法で確認してから開始する。開始後は対象ファイル・ジョブと稼働状態を照合する。

開始要求がタイムアウトした場合は、同じジョブが始まっていないか先に状態を照合する。不明なまま start を再送しない。

### `status` — 進捗確認

機種別。Creality 系は `:9999` WS で `{"method":"get","params":{"reqPrinter":1}}` → `state / printProgress / printJobTime / printLeftTime / nozzleTemp / bedTemp0` 等。

判定は対象機種・firmware の状態定義を使い、対象ファイル/ジョブと関連付ける。Creality K1 Max の既存記録は `references/printers.md` にある。
`printProgress=100`、idle、経過時間のいずれか一つだけでは完了と断定しない。中止・異常・完了を区別し、定義や取得状態が矛盾する場合は未確認として報告する。

### `pause` / `stop` / `resume` — ジョブ制御

対象プリンタと現在のジョブを識別して、明示された操作を行い、操作後の状態を照合する。「止めて」と中止を指示された場合に、勝手に pause へ置き換えない。resume は再開の許可と機器状態を確認して行う。

### `verify` — カメラスナップショット取得

今回開始する印刷では、利用可能なカメラで開始直前のベッドと完了後の見える状態を確認する。既存ジョブの確認や写真取得だけの依頼なら、現在の画像を取得し、過去の baseline がないことを明記する。画像を保存しただけでなく内容を見て、対象・時点・画角の限界を示す。

```bash
# Creality K1 系: mjpg-streamer
curl -o "$ARTIFACT_DIR/baseline.jpg" http://<IP>:8080/?action=snapshot   # 印刷前
# ... 印刷 ...
curl -o "$ARTIFACT_DIR/complete.jpg" http://<IP>:8080/?action=snapshot   # 完了時
```

詳細 (機種別カメラ URL、ストリーム vs スナップショット、復活手順) は `references/camera-verification.md` 参照。

### `submit` — 一気通貫

`slice` → 投入前確認 → `print` → 対象ジョブの監視 → `verify` を依頼された範囲で進める。既に成立した工程や許可をやり直さない。
監視間隔は機種の仕様・既存運用・印刷段階に合わせる。監視を終える時点で未完了なら、進捗と残る確認を明示し、完了扱いにしない。

## 完了と記録

依頼された工程の成果物、対象、設定、実行結果、未確認を対応付けて報告する。
スライス成功、機器が報告するジョブ完了、カメラで見える造形状態、寸法・強度・嵌合等の物理試験を分ける。メタデータや写真から物理試験済みと書かない。

STL/gcode/preview/画像は、目的に必要なものを許可されたローカル保存先へ残す。commit は対象 repo の方針と依頼範囲に従い、成果物すべてを一律に追加しない。
WorkItem の note・添付、Slack 等への投稿は外部送信に当たる。宛先・本文・画像を下書きし、セッションで得た明示許可の範囲でのみ送信する。写真の背景や接続情報を無関係な公開成果物へ混入させない。

## 安全ルール

- 印刷開始・再開・機器設定変更は、対象と現在の許可範囲を確認して行う。
- スライサ override profile は bundle を書き換えず、対象プロジェクト等の別ファイルへ置く。
- stock firmware の利用可能な API を優先し、接続確認やカメラ取得のために root 化・再起動・別ジョブ中断をしない。
- 画像だけを根拠とする自動停止や失敗判定システムの導入は別タスクとして扱う。

## Anti-patterns

- 対応していない `.stl` を印刷用 gcode として送る → 機種が受け付ける形式と変換工程を確認する。
- `enable_support=1` を OrcaSlicer の CLI flag と仮定する → 対応する profile JSON と使用版の CLI を確認する。
- 応答なしを失敗と決めて start を再送する → 対象ジョブの現在状態を照合する。
- カメラがない/見えないことを理由に、ベッド確認を省いて投入する → 必要な現地確認だけ依頼する。

## References

- [printers.md](references/printers.md) — 機種別スペック・プロトコル・upload/start エンドポイント
- [camera-verification.md](references/camera-verification.md) — 印刷前後のスナップショット運用
- [support-interface-materials.md](references/support-interface-materials.md) — サポート界面への異種マテリアル活用パターン集（PETG×PLA 剥離、HIPS/PVA/BVOH、スライサー設定、ハードウェア形態別の注意）

---

## Checklist (印刷投入時)

- [ ] 入力モデル・出力 gcode・投入先プリンタの対応が確認できている
- [ ] 機種・ノズル・材料・ベッド・配置・toolpath が今回の設定と合っている
- [ ] 現在のベッドと別ジョブの有無を確認した
- [ ] 今回の投入がユーザーの明示許可に含まれる
- [ ] 投入後、対象ファイル/ジョブの開始を確認した
- [ ] 完了・中止・異常・未確認を区別し、画像確認と物理試験の範囲を分けて報告した
