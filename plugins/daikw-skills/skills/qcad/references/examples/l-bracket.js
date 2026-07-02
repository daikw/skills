// L字ブラケット : 外寸 80(W) x 60(H) / 板厚(アーム幅) 10mm / 全コーナー R5 フィレット
// 原点 = 左下 (0,0)。外形を反時計回り(CCW)に一周。
//
// 材料占有域:
//   水平アーム  0<=x<=80, 0<=y<=10
//   垂直アーム  0<=x<=10, 0<=y<=60
// シャープ頂点(CCW): A(0,0) B(80,0) C(80,10) D(10,10) E(10,60) F(0,60)
//   A,B,C,E,F = 凸コーナー / D = 凹(再入)コーナー
//
// フィレットは lib に primitive が無いため line + 接弧(arc) を接点計算で手組みする。
// 接点 = コーナーから各辺へ R オフセットした点。弧中心 = コーナーから両辺へ R 内側オフセット。
// R=5 のため長さ 10 の辺(B-C, E-F)は直線部ゼロ、2弧が同心で連続する。

var R = 5;
var d = new Drawing();

d.addLayer("Outline", "white");
d.addLayer("Annotation", "green");

// --- 直線部（フィレット接点の間だけ残る） ---
d.line(5, 0, 75, 0, "Outline");     // A-B 底辺 (y=0)
d.line(75, 10, 15, 10, "Outline");  // C-D 水平アーム上辺 (y=10)
d.line(10, 15, 10, 55, "Outline");  // D-E 垂直アーム右辺 (x=10)
d.line(0, 55, 0, 5, "Outline");     // F-A 左辺 (x=0)

// --- R5 接弧 ---
d.arc(5, 5, R, 180, 270, "Outline");    // A 左下(凸)
d.arc(75, 5, R, 270, 360, "Outline");   // B 右下(凸)
d.arc(75, 5, R, 0, 90, "Outline");      // C 右上(凸) ※B と同心 → 右辺は半円
d.arc(15, 15, R, 180, 270, "Outline");  // D 内側(凹フィレット)
d.arc(5, 55, R, 0, 90, "Outline");      // E 垂直アーム右上(凸)
d.arc(5, 55, R, 90, 180, "Outline");    // F 左上(凸) ※E と同心 → 上辺は半円

// --- 注記 ---
d.text("L-BRACKET 80x60 t10 R5", 0, -10, 4, "Annotation");

d.saveAndReport(_qcadDrawOutput);
