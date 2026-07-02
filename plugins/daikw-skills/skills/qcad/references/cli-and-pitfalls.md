# QCAD CLI と地雷集

QCAD 3.32.9 Community (macOS) で実機検証済み。

## CLI 起動

```bash
/Applications/QCAD.app/Contents/Resources/qcad \
    -no-gui \
    -no-dock-icon \
    -allow-multiple-instances \
    -autostart /absolute/path/to/script.js
```

| フラグ | 意味 |
|---|---|
| `-no-gui` | GUI を起動しない |
| `-no-dock-icon` | macOS Dock にアイコンを出さない |
| `-allow-multiple-instances` | GUI 版 QCAD が起動中でも並走可能 |
| `-autostart <path>` | 指定した JS スクリプトを実行 |

## 地雷

### 1. JS 例外でも exit 0

QCAD は autostart スクリプト内で例外が発生しても **常に exit 0** を返す。

**対策**: ラッパスクリプト (`qcad-draw.sh`) で以下の複合判定:
- try/catch で `.error` ファイルを書き出し
- stdout に `QCAD_ERROR:` マーカーを出力
- DXF ファイルの存在・サイズチェック

### 2. `-platform offscreen` は macOS で使えない

macOS の QCAD は Qt の cocoa プラグインのみ同梱。`-platform offscreen` を指定すると abort する。

**対策**: `-no-gui -no-dock-icon` だけで headless 実行可能。

### 3. `addObject` のデフォルトは属性を上書きする

`RAddObjectsOperation.addObject(entity)` の第2引数を省略するか `true` にすると、エンティティの属性（レイヤー、色等）がドキュメントのカレント属性で上書きされる。

**対策**: 常に `addObject(entity, false)` を使う。

### 4. `setLayerName()` が機能しない

エンティティに `setLayerName("MyLayer")` を呼んでも DXF に反映されない。

**対策**: `entity.setLayerId(doc.getLayerId("MyLayer"))` を使う。

### 5. SPLINE の fit point は DXF エクスポートで消える

`RSplineData.appendFitPoint()` で作った SPLINE は、DXF エクスポート時に "Discarding spline: not enough control points given." 警告で消える。

**対策**: `appendControlPoint()` を使う。degree=3 なら最低 4 制御点。

### 6. レイヤー追加は `RModifyObjectsOperation`

`RAddObjectOperation` や `RAddObjectsOperation` でレイヤーを追加しても反映されない。

**対策**: `RModifyObjectsOperation` にレイヤーオブジェクトを追加して applyOperation する。

### 7. Community 版は DXF しかエクスポートできない

`di.exportFile()` で BMP/SVG/PNG/PDF を指定しても "No suitable exporter found" で失敗する。

**対策**: DXF → PNG 変換は Python `ezdxf[draw]==1.4.2` で行う。

### 8. `di.destroy()` は存在しない

`RDocumentInterface` に `destroy()` メソッドはない。呼ぶと TypeError 例外。

**対策**: 呼ばない。GC に任せる。

### 9. Plugin loader の libqcadtrace.dylib エラー

起動時に `Cannot load library libqcadprojsapi.dylib` エラーが出るが、Community 版では正常動作に影響しない。

**対策**: 無視してよい。

## DXF → PNG 変換

```bash
uv run --with 'ezdxf[draw]==1.4.2' python -c "
import ezdxf
from ezdxf.addons.drawing import matplotlib as mpl_draw
doc = ezdxf.readfile('input.dxf')
mpl_draw.qsave(doc.modelspace(), 'output.png', dpi=150)
"
```
