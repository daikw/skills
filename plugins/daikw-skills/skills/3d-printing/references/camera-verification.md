# Camera Verification

印刷空間にカメラがあれば、**印刷の前後で必ずスナップショットを取って結果を視覚的に検証**する。Claude は物理確認できないが、画像なら確認できる。

---

## なぜカメラ起点の検証が必要か

1. **完了 != 成功**: `printProgress=100` で終了でも、糸状崩壊・ベッド剥がれ・ノズル詰まり等で物理的には失敗してる可能性がある
2. **ベッドが空かどうか**: 前のジョブの残骸がベッドにある状態で start すると即衝突 → カメラで baseline を取って空であることを確認する
3. **物理確認の記録**: 完了画像は WorkItem / Slack / GitLab に貼って残しておくと、後でデザイン iteration の根拠になる
4. **長時間ジョブの中間記録**: 数時間ジョブで、途中の状態を 1 〜数枚保存しておくと、後から失敗時点を遡って分析できる

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
 │       (60-90 秒間隔、first-layer 直後は 10-15 秒)
 │
 ├── (4) [optional] 5-10 分おきに mid-<n>.jpg
 │       (失敗時に時系列分析できる)
 │
 ├── (5) printProgress=100 検知
 │
 ├── (6) complete.jpg を撮る            # ノズル parking 後、ヒーター OFF 中
 │
 └── (7) baseline.jpg / complete.jpg を repo に保存 + ユーザ提示
```

`baseline → complete` の対比でユーザにも視覚的に「印刷物が乗ってるか」分かる。

---

## 機種別カメラ URL

`references/printers.md` 参照。代表例:

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

以下を順に試す:

1. **`ping <ip>` で機器は生きてるか** — 生きてるなら次へ
2. **`curl -m 4 -I http://<ip>:8080/?action=stream`** — Content-Type が `multipart/x-mixed-replace` なら OK
3. **接続拒否 (code 7) なら mjpg-streamer 未起動** — プリンタ再起動 (Creality K1 stock の既知のクセ)
4. **再起動しても出ない** — Helper Script でロックされてる可能性、機種マニュアル要参照
5. **タッチパネル UI 上の "Monitor" / カメラボタンを押してから再確認** — 一部 firmware は手動有効化が必要

`references/printers.md` の各機種 "Known quirks" にも記載する。

---

## 自動失敗検知への発展 (オプション)

このスキルの範囲は "起動と完了時のスナップショット" まで。それ以上の「印刷中の失敗自動検知」は別タスクで:

- Obico (CNN-based、既存 OSS) を Helper Script + OctoPrint 経由で導入
- LLM-as-judge パターン (VLM に画像を投げて failure mode 判定)
- 設計指針: print 監視を LLM-as-judge で組む場合の references を別途参照

このスキル単体では、**完了時点での視覚確認**までに留める。途中監視の自動化は別レイヤ。

---

## 保存先のお作法

印刷した repo の直下に `camera/` ディレクトリを置く。1 ジョブにつき:

```
camera/
└── 2026-05-18T19:48_pi-pico-case-v6/
    ├── 20260518-194800_baseline.jpg     # start 直前のベッド
    ├── 20260518-200315_complete.jpg     # 完了時
    └── (任意) 中間スナップショット群
```

`.gitignore` に含めるか、commit するかは状況次第:

- **commit する**: design iteration のエビデンスとして残したい場合 (Pi Pico ケースのような小物)
- **gitignore**: ジョブごとに大量に出るなら除外 (5+ MB ジョブを毎回 commit すると repo が肥大)

`commit` する場合は WorkItem (`physai-tasks`) の note にも添付して、後から検索できるようにする。

---

## Anti-patterns

- **baseline を撮らずに start** → 失敗時に「最初からそうだったか / 印刷で発生したか」分からない
- **complete を撮らずに完了報告** → ユーザに「物理確認お願い」と頼んでも証跡が残らない
- **ストリーム連続録画を repo に commit** → 5h ジョブで数 GB になる。**1 ファイル = 1 ショット**が原則
- **スナップショットを Slack/GitLab に流すとき** → 背景に作業環境が映る。プライバシー範囲を確認する
- **失敗時に判断不能な角度のカメラ** → カメラ位置 (側面 / 正面 / 上方) を機種別にメモしておく
