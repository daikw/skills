# Printer reference

機種別のプロトコル・API・スペックの集約。新しい機種を LAN に追加したら、ここに 1 セクション足すのだ。

## 共通フィールド (各機種の最低限)

- mDNS service type / instance pattern
- HTTP/REST endpoints (info, upload, file list)
- WebSocket/Socket protocol (control)
- Camera URL (あれば)
- Slicer profile location
- Build volume / nozzle defaults
- Known quirks

---

## Creality K1 Max (stock firmware)

ファームウェア 1.0.0+ の純正 (Helper Script 等の root mod 未導入) を対象。

### 検出

| 項目 | 値 |
|---|---|
| mDNS service type | `_Creality-<6-byte-hex>._udp.local.` (例: `_Creality-XXXXXXXXXXXXXX`) |
| instance | `K1Max-<last-4-MAC>` (例: `K1Max-XXXX`) |
| hostname | `<instance>.local` (例: `K1Max-XXXX.local`) |
| ホスト解決 | `dns-sd -G v4 <instance>.local` |
| MAC (`/info`) | `FCEE:XXXX:XXXX` (Creality OUI) |

### HTTP

| Method | Path | Content | 用途 |
|---|---|---|---|
| GET  | `/info` | JSON `{mac, model, version}` | 機種・FW 確認 |
| POST | `/upload` | multipart, field name `file` | gcode をアップロード → `/usr/data/printer_data/gcodes/<filename>` |
| GET  | `/downloads/original/current_print_image.png` | PNG (300×300) | 現在印刷中の gcode サムネ（**カメラ画像ではない**） |
| GET  | `/downloads/video/` | directory listing | リスティングは表示できるが mjpg-streamer は別ポート |

`POST /upload` のレスポンス: `{"code":200,"message":"OK"}`。filename は multipart の Content-Disposition から取る。

### WebSocket (制御チャネル)

`ws://<ip>:9999/` — JSON-RPC ish。**ポート 80 の `/websocket` ではない**。

| 方向 | params | 効果 |
|---|---|---|
| `get` | `{"reqPrinter": 1}` | 全状態 push を要求 (state, temp, progress, position, etc.) |
| `get` | `{"reqGcodeFile": 1}` | `retGcodeFileInfo2` でファイル一覧 |
| `set` | `{"opGcodeFile": "printprt:<absolute path>"}` | 印刷開始。path は `/usr/data/printer_data/gcodes/<filename>` |
| `set` | `{"pause": 1}` | 一時停止 |
| `set` | `{"stop": 1}` | 中止 |
| `set` | `{"lightSw": 0/1}` | 庫内ライト |
| `set` | `{"fan": 0/1}` | モデルファン |
| `set` | `{"aiSw": 0/1}` | AI 検知 ON/OFF (内部処理。LAN ストリーム露出には影響しない) |

State push の主要 key:

- `state` / `deviceState` — 0=idle, 1=printing/probing, 2=completed, 9=preparing
- `printProgress` (0-100), `printJobTime` (秒), `printLeftTime` (秒)
- `printFileName` (絶対パス)
- `nozzleTemp` / `targetNozzleTemp`, `bedTemp0` / `targetBedTemp0`
- `curPosition` ("X:.. Y:.. Z:..")
- `layer` / `TotalLayer`
- `err.errcode` (0 = OK)

### カメラ

| URL | 内容 |
|---|---|
| `http://<ip>:8080/?action=stream` | MJPEG (multipart/x-mixed-replace, 1280×720, ~9 Mbps) |
| `http://<ip>:8080/?action=snapshot` | JPEG 単発 (~10-15 KB / 1280×720) |

**重要なクセ**: stock firmware は **電源 ON 直後 mjpg-streamer が立ち上がらないことがある**。`:8080` が接続拒否なら **プリンタ再起動** で復活する。常時起動したいなら Helper Script (root mod) を入れる。

### スペック

| 項目 | 値 |
|---|---|
| Build volume | 300 × 300 × 300 mm |
| Nozzle (stock) | 0.4mm。0.6 / 0.8 オプションあり |
| Hotend max temp | 300°C |
| Bed max temp | 100°C |
| Max travel speed | 600 mm/s (実用 200-300) |
| ファームウェア基盤 | Klipper (隠蔽されている) |
| ファイル保存先 | `/usr/data/printer_data/gcodes/` |

### OrcaSlicer プロファイル (bundle)

```
/Applications/OrcaSlicer.app/Contents/Resources/profiles/Creality/
├── machine/Creality K1 Max (0.4 nozzle).json
├── machine/Creality K1 Max (0.6 nozzle).json
├── machine/Creality K1 Max (0.8 nozzle).json
├── process/0.12mm Fine @Creality K1Max (0.4 nozzle).json
├── process/0.16mm Optimal @Creality K1Max (0.4 nozzle).json
├── process/0.20mm Standard @Creality K1Max (0.4 nozzle).json
├── process/0.24mm Draft @Creality K1Max (0.4 nozzle).json
└── filament/Creality Generic PLA @K1-all.json
```

### Known quirks

- スライサに渡す process profile は **override 連結 (`;`) 不可** → bundle profile をフルコピーしてから書き換える
- 印刷終了後の error code 210/506 は **正常終了からの自動 filament 監視 trip** で実害なし
- `aiSw=1` にしても LAN ストリーム自体は活性化しない（mjpg-streamer 起動とは独立）
- `printJobTime` は probing/heating 時間を含む、`printLeftTime` は残り推定値

---

## 機種テンプレート（未対応機種を追加するとき）

```markdown
## <Vendor> <Model> (<firmware>)

### 検出
- mDNS: `_xxxxxx._tcp.local.` ...
- hostname pattern: ...

### HTTP
| Method | Path | Content | 用途 |
|---|---|---|---|

### WS / Socket
- `ws://<ip>:<port>/` or `tcp://<ip>:<port>/`
- メッセージ形式 (JSON / line-based / binary)
- 主要 method 一覧

### カメラ
- URL とフォーマット
- 起動条件 (常時 / 印刷中のみ / 手動有効化)

### スペック
- Build volume / Nozzle / 各種 max temp / FW 基盤

### OrcaSlicer / 他 slicer プロファイル
- bundle 内 path
- override 必要なら repo 内に置く方針

### Known quirks
- 検出した非自明な挙動を列挙
```

---

## TODO: 追加候補

このスキルが対応するべき主要機種:

- [ ] Bambu Lab P1S / X1 Carbon (LAN MQTT + RTSP, root 不要だが access code が必要)
- [ ] Prusa MK4S / Core One (OctoPrint 互換 REST + WebSocket)
- [ ] Anycubic Kobra (Klipper 系、Cura 派生 slicer)
- [ ] Original Prusa MINI (古いが安定、PrusaLink REST)
- [ ] Voron (community Klipper, Mainsail/Fluidd UI 標準)
