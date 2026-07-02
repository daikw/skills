---
name: qcad
description: "自然言語の指示から QCAD で 2D 図形を作図し、DXF を生成、PNG で目視検証する。QCAD、作図、2D CAD、DXF、フランジ、ボルト穴、図面の作成を依頼されたときに使う。"
---

# QCAD 自然言語作図スキル

自然言語の指示（例: 「フランジに φ12 ボルト穴を 8 個、PCD90 で」）から QCAD Community 版で 2D 図形を headless 作図し、DXF を出力する。

## 前提

- QCAD Community 3.32.x が `/Applications/QCAD.app/` にインストール済み
- `uv` がインストール済み（PNG 変換に `ezdxf[draw]==1.4.2` を使用）
- 作図ライブラリ・ラッパはこのスキルの `scripts/` に同梱（`scripts/lib.js`, `scripts/qcad-draw.sh`）

## 単位規約・座標系

- 座標: mm（絶対モデル空間）
- 角度: 度（arc の startDeg / endDeg、反時計回りが正方向、0° = X 軸正方向）
- 半径・寸法: mm
- 原点: 図形の中心または左下隅を (0, 0) に配置する。回転対称な部品は中心原点、非対称な部品は左下原点を推奨
- arc の弧選択: startDeg → endDeg を反時計回りに掃引した弧が描かれる。劣弧が欲しければ角度範囲を 180° 未満に、優弧なら 180° 超にする

## ワークフロー（固定順序）

以下の順序を必ず守る。レイヤはジオメトリより先に全部作る。

1. **レイヤ定義** — 用途別レイヤを `addLayer` で全て先に作成（冪等: 既存なら skip）
2. **ジオメトリ** — 線・円・弧・矩形・ポリライン・楕円・スプライン
3. **注記** — テキスト・寸法線（将来対応）
4. **保存** — `saveAndReport(_qcadDrawOutput)` で DXF 出力 + 構造化 JSON レポート
5. **視覚検証** — `--png` で PNG 生成し目視確認。問題があれば 1 に戻る

## 意図→操作の決定表

| やりたいこと | 使う API | 備考 |
|---|---|---|
| 直線を引く | `d.line(x1, y1, x2, y2)` | |
| 穴・フランジ等の円 | `d.circle(cx, cy, r)` | |
| 半円・弧 | `d.arc(cx, cy, r, startDeg, endDeg)` | |
| 矩形の外形 | `d.rect(x, y, w, h)` | 閉じたポリライン |
| 任意の多角形 | `d.polyline([[x,y],...], true)` | closed=true で閉じる |
| 楕円 | `d.ellipse(cx, cy, majorX, majorY, ratio)` | |
| 滑らかな曲線 | `d.spline([[x,y],...])` | 制御点、最低 4 個 |
| 文字ラベル | `d.text("str", x, y, height)` | |
| 等間隔配置（PCD 穴等） | for ループで `cos`/`sin` 計算 | 下記フィレットの参考実装欄を参照 |
| 角丸/フィレット | `d.line` + `d.arc` を手組み | 下記パターン参照 |

### フィレット（角丸）の作り方

lib.js にフィレット primitive はない。line + arc を接点計算で組み合わせる。

**凸コーナーの R フィレット（90° 直角の場合）:**
```
辺 A が x 方向、辺 B が y 方向に曲がるコーナー (cx, cy) に半径 R のフィレットを入れる:
- 辺 A の端点を (cx - R, cy) に短縮
- 辺 B の始点を (cx, cy + R) に短縮
- 弧: d.arc(cx - R, cy + R, R, 270, 360)  // 中心は辺から R オフセット
```

**一般的な手順:**
1. コーナーの 2 辺それぞれを R だけ短縮（接点を計算）
2. 弧の中心 = コーナーから各辺に R オフセットした点
3. `d.arc(弧中心x, 弧中心y, R, startDeg, endDeg)` で弧を描く
4. startDeg/endDeg は辺の方向から決まる（反時計回りが正方向）

**凹（内側）コーナーの場合:**
弧の中心は辺から R だけ内側にオフセットする（凸と逆方向）。掃引角度も凸とは逆になる。

**degenerate case（R が辺長の半分以上）:**
辺長が 2R 以下の場合、両端のフィレットが合流して直線部が消える。この場合は直線を省略し、2 つの弧を接点で直接つなぐ（結果は半円状の丸端になる）。

**参考実装:** PCD 穴配列とフィレット適用の実例は `references/examples/` を参照

## スニペットの書き方

スニペットは `qcad-draw.sh` のラッパ内で実行される。`Drawing` と `_qcadDrawOutput` は自動で利用可能。

```javascript
var d = new Drawing();

// 1. レイヤ定義（全て先に）
d.addLayer("Outline", "white");
d.addLayer("Holes", "red");
d.addLayer("Center", "cyan");

// 2. ジオメトリ
d.circle(0, 0, 60, "Outline");
d.circle(50, 0, 6, "Holes");
d.line(-70, 0, 70, 0, "Center");

// 3. 注記
d.text("8x φ12", 0, -75, 4);

// 4. 保存（構造化レスポンス付き）
d.saveAndReport(_qcadDrawOutput);
```

## Drawing API

### レイヤ（冪等: 同名レイヤが既存なら skip）

```javascript
d.addLayer(name, color, lineweight)
```

### ジオメトリ（全関数の末尾引数 layer は省略可）

```javascript
d.line(x1, y1, x2, y2, layer)
d.circle(cx, cy, r, layer)
d.arc(cx, cy, r, startDeg, endDeg, layer)
d.point(x, y, layer)
d.rect(x, y, w, h, layer)
d.polyline([[x,y], ...], closed, layer)
d.ellipse(cx, cy, majorX, majorY, ratio, layer)
d.text("string", x, y, height, layer)
d.spline([[x,y], ...], degree, layer)   // degree=3 がデフォルト
```

### 保存・状態取得

```javascript
d.save(path)              // DXF 出力のみ
d.saveAndReport(path)     // DXF 出力 + QCAD_RESULT JSON を stdout に出力
d.entityCount()           // エンティティ数（READ_ONLY）
d.layerNames()            // レイヤ名配列（READ_ONLY）
d.summary()               // {entities, layers, byType}（READ_ONLY）
```

## 実行方法

```bash
# DXF のみ
scripts/qcad-draw.sh snippet.js -o output.dxf

# DXF + PNG
scripts/qcad-draw.sh snippet.js -o output.dxf --png
```

## 構造化レスポンス

`saveAndReport` を使うと、stdout に以下の JSON が出力される:

```json
QCAD_RESULT:{"success":true,"output":"/path/to/output.dxf","entities":3,"layers":["0","Holes"]}
```

## 注意事項

- **QCAD は JS 例外でも exit 0 を返す**。ラッパが `.error` ファイルと `QCAD_ERROR` マーカーで故障を検出し、exit 1 にする
- Community 版は DXF のみ出力可能。BMP/SVG/PNG/PDF エクスポートは Pro 限定
- PNG 変換は Python `ezdxf[draw]` + matplotlib で行う
- SPLINE は fit point ではなく control point を使う（fit point は DXF 書き出し時にエラーになる）
- `addObject` の第2引数は `false` にする（`true` だとレイヤー等の属性がデフォルトに上書きされる）
- `-platform offscreen` は macOS では使えない。`-no-gui -no-dock-icon -allow-multiple-instances` で headless 実行する
- 詳細な API リファレンスと地雷集は `references/` を参照
