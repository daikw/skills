# QCAD ECMAScript API リファレンス（検証済み）

QCAD 3.32.9 Community (macOS) で実機検証した API のみを記載。

## ドキュメント作成（headless）

```javascript
include("scripts/library.js");

var storage = new RMemoryStorage();
var spatialIndex = new RSpatialIndexSimple();
var doc = new RDocument(storage, spatialIndex);
var di = new RDocumentInterface(doc);
```

## エンティティ追加

```javascript
var op = new RAddObjectsOperation();

// LINE
op.addObject(new RLineEntity(doc,
    new RLineData(new RVector(x1, y1), new RVector(x2, y2))), false);

// CIRCLE
op.addObject(new RCircleEntity(doc,
    new RCircleData(new RVector(cx, cy), radius)), false);

// ARC (角度はラジアン)
op.addObject(new RArcEntity(doc,
    new RArcData(new RVector(cx, cy), radius, startRad, endRad, false)), false);
// 最後の false = 反時計回り (reversed=false)

// POINT
op.addObject(new RPointEntity(doc,
    new RPointData(new RVector(x, y))), false);

// POLYLINE (LWPOLYLINE として出力)
var pl = new RPolylineData();
pl.appendVertex(new RVector(x, y));
// ... 頂点追加
pl.setClosed(true); // 閉じる場合
op.addObject(new RPolylineEntity(doc, pl), false);

// ELLIPSE
op.addObject(new REllipseEntity(doc,
    new REllipseData(
        new RVector(cx, cy),      // center
        new RVector(majorX, majorY), // 長軸方向ベクトル（中心からの相対）
        ratio,                     // 短軸/長軸 比率 (0-1)
        0, Math.PI * 2,           // startParam, endParam (full)
        false                      // reversed
    )), false);

// TEXT (MTEXT として出力)
var td = new RTextData();
td.setText("text content");
td.setAlignmentPoint(new RVector(x, y));
td.setTextHeight(5);
op.addObject(new RTextEntity(doc, td), false);

// SPLINE (制御点方式、degree=3 は最低 4 制御点)
var sd = new RSplineData();
sd.setDegree(3);
sd.appendControlPoint(new RVector(x, y));
// ... 制御点追加 (最低 degree+1 個)
op.addObject(new RSplineEntity(doc, sd), false);

di.applyOperation(op);
```

## addObject の第2引数

| 値 | 意味 | 用途 |
|---|---|---|
| `false` | エンティティの属性をそのまま保持 | レイヤー・色を指定する場合に必須 |
| `true` / 省略 | ドキュメントの現在属性で上書き | デフォルト。レイヤーは "0" に強制される |

## レイヤー追加

```javascript
var linetypeId = doc.getLinetypeId("CONTINUOUS");
var layerOp = new RModifyObjectsOperation();
layerOp.addObject(new RLayer(doc, "LayerName", false, false,
    new RColor("red"), linetypeId, RLineweight.Weight025));
di.applyOperation(layerOp);
```

- `RAddObjectOperation` ではなく `RModifyObjectsOperation` を使う
- レイヤーは先に追加してからエンティティを作成する

### エンティティにレイヤーを割り当て

```javascript
entity.setLayerId(doc.getLayerId("LayerName"));
op.addObject(entity, false);  // false 必須
```

- `setLayerName()` は機能しない（`setLayerId` を使う）

## エクスポート

```javascript
var result = di.exportFile("/absolute/path/output.dxf", "R24 (2010) DXF");
// result: true=成功, false=失敗
```

### Community 版で利用可能なフォーマット

| フォーマット | 対応 |
|---|---|
| DXF (`"R24 (2010) DXF"`) | ✓ |
| BMP / SVG / PNG / PDF | ✗ (Pro 限定) |

## ユーティリティ

```javascript
RSettings.getLaunchPath()   // qcad を実行した cwd
doc.queryAllEntities()      // 全エンティティ ID 配列
doc.getLayerNames()         // 全レイヤー名配列
doc.getLayerId("name")      // レイヤー名 → ID
new QFileInfo(path).isAbsolute()  // 絶対パス判定
```

## 未検証（Pro 限定 or 未テスト）

- 寸法（Dimension 系エンティティ）
- ハッチ（RHatchEntity）
- ブロック（RBlockReferenceEntity）
- 線種の変更（CONTINUOUS 以外）
- 線幅の指定（エンティティレベル）
