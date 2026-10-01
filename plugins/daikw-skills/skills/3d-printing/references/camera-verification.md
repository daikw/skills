# Camera Verification

今回開始するジョブでは、利用可能なカメラで開始前のベッドと完了後の造形状態を確認する。現在の写真だけの依頼ならその画像を取得し、過去の baseline を要求して止めない。画像の確認は、画角内の見える状態についての証拠であり、寸法・強度・嵌合等の物理試験ではない。

---

## なぜカメラ起点の検証が必要か

1. **完了 != 成功**: `printProgress=100` で終了でも、糸状崩壊・ベッド剥がれ・ノズル詰まり等で造形に失敗している可能性がある
2. **ベッドが空かどうか**: 残った造形物と衝突し得るため、start 前に現在のベッドを確認する。カメラで判断できなければ対象を明示した現地確認を使う
3. **視覚確認の記録**: 対象ジョブと撮影時点を付けて許可されたローカル保存先へ残す。WorkItem / Slack / GitLab への送信・添付は明示許可の範囲だけ行う
4. **中間記録**: 失敗時点の分析等が必要な場合は、その目的に合う工程で保存する

---

## 標準フロー

```
START
 │
 ├── (1) baseline.jpg を撮る            # ベッドが空であることの確認
 │
 ├── (2) upload + start                 # gcode 投入
 │
 ├── (3) progress polling 開始
 │       (間隔は機種の仕様・既存運用・印刷段階に合わせる)
 │
 ├── (4) [optional] 必要な工程で mid-<n>.jpg
 │       (失敗時に時系列分析できる)
 │
 ├── (5) 対象ジョブの完了を機種・firmware の状態定義で確認
 │
 ├── (6) complete.jpg を撮る            # ノズル parking 後、ヒーター OFF 中
 │
 └── (7) baseline.jpg / complete.jpg を repo に保存 + ユーザ提示
```

`baseline → complete` を見比べると、ユーザーも印刷物の有無を確認できる。

---

## 機種別カメラ URL

[printers.md](printers.md) 参照。以下は既存記録の URL pattern であり、実際の機種・firmware・利用可能な手順で対応を確認して使う:

| 機種 | URL pattern | 備考 |
|---|---|---|
| Creality K1 / K1 Max (stock) | `http://<ip>:8080/?action=stream` / `?action=snapshot` | 電源 ON 直後は無効、再起動で復活する個体あり |
| OctoPrint + mjpg-streamer | `http://<ip>:8080/?action=stream` | 同じ pattern |
| Bambu P1S/X1 | `rtsps://<ip>:322/streaming/live/1` | RTSPS、ffmpeg で 1 フレーム抜き出し |
| Helper Script 改造 K1 | `http://<ip>:8080/?action=stream` | 常時稼働 |

stream か snapshot かで実装が変わる:

- **snapshot**: 単発 GET → JPEG ファイル → そのまま保存
- **stream**: multipart/x-mixed-replace MJPEG → 1 フレーム取り出して JPEG 化 (OpenCV / ffmpeg)

---

## 実装パターン

### Python (Creality K1 系)

```python
import requests
from pathlib import Path
from datetime import datetime

def snapshot(host: str, label: str, outdir: Path = Path("camera")) -> Path:
    """K1 mjpg-streamer から 1 フレーム取得して保存する"""
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = outdir / f"{stamp}_{label}.jpg"
    r = requests.get(
        f"http://{host}:8080/?action=snapshot",
        timeout=10,
    )
    r.raise_for_status()
    target.write_bytes(r.content)
    return target
```

### MJPEG ストリームからフレーム抜き (OpenCV)

```python
import cv2
def grab_stream_frame(url: str, dest: Path) -> Path:
    cap = cv2.VideoCapture(url)
    try:
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError(f"no frame from {url}")
        cv2.imwrite(str(dest), frame)
        return dest
    finally:
        cap.release()
```

---

## カメラが「見えない」とき

対象機器と許可された経路を確認し、対応するカメラ endpoint の応答と形式を調べる。接続拒否だけで mjpg-streamer 未起動や原因を断定しない。

Creality K1 stock には再起動後にカメラが利用できた既存記録があるが、カメラ取得の依頼はプリンタ再起動・root 化・ジョブ中断の許可ではない。印刷中の機器を復旧のために再起動しない。機種マニュアルで手動有効化等の手順を確認し、機器状態と許可範囲に合う場合だけ進める。

取得できなければカメラ確認は未実施と報告する。投入前のベッド確認が必要なら現地確認を依頼し、機器の状態取得まで不能ならジョブ完了も未確認として扱う。

---

## 自動失敗検知への発展 (オプション)

このスキルの範囲は "起動と完了時のスナップショット" まで。それ以上の「印刷中の失敗自動検知」は別タスクで:

- Obico (CNN-based、既存 OSS) を Helper Script + OctoPrint 経由で導入
- LLM-as-judge パターン (VLM に画像を投げて failure mode 判定)
- 設計指針: print 監視を LLM-as-judge で組む場合の references を別途参照

このスキル単体では、**完了時点での視覚確認**までに留める。印刷途中の監視を自動化する場合は別タスクで扱う。

---

## 保存先と Git 管理

印刷した repo の直下に `camera/` ディレクトリを置く。1 ジョブにつき:

```
camera/
└── 2026-05-18T19:48_pi-pico-case-v6/
    ├── 20260518-194800_baseline.jpg     # start 直前のベッド
    ├── 20260518-200315_complete.jpg     # 完了時
    └── (任意) 中間スナップショット群
```

`.gitignore` に含めるか、commit するかは状況次第:

- **commit する**: 設計変更の検証記録として残したい場合 (Pi Pico ケースのような小物)
- **gitignore**: ジョブごとの画像を保存する用途で repo に含める必要がなければ除外

ローカル保存・commit は外部投稿の許可にならない。WorkItem の note や添付は、宛先・本文・画像を下書きし、明示許可の範囲でのみ送信する。

---

## Anti-patterns

- **現在のベッドを確認せずに start** → 残った造形物を見落とす。写真が不十分なら現地確認を使う
- **機器の完了表示だけで造形成功と報告** → 画像未確認ならその限界を示し、必要な現地確認を依頼する
- **ストリーム連続録画を repo に commit** → 5h ジョブで数 GB になる。**1 ファイル = 1 ショット**が原則
- **保存した画像を自動で Slack/GitLab に投稿** → 背景のプライバシーと送信許可を確認し、許可された画像だけ送る
- **失敗時に判断不能な角度のカメラ** → カメラ位置 (側面 / 正面 / 上方) を機種別にメモしておく
