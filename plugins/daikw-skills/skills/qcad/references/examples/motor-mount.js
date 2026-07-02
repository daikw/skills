// モーターマウントプレート
// 外形 150x100 / 四隅 R8 フィレット / 原点 = 左下 (0,0) / 中心 = (75,50)
// 中央 φ50 モーター穴 / PCD70 上に φ6 ボルト穴 4 個 / 四隅内側 φ8 取付穴
//
// 外形は反時計回り(CCW)に周回。polyline は弧を持てないため直線 + 接弧で構成する。
// シャープ頂点(CCW): (0,0) (150,0) (150,100) (0,100) — 全て凸コーナー。
// 各辺を R8 だけ短縮し、コーナーから内側に (R,R) オフセットした点を弧中心にする。

var d = new Drawing();

// --- 1. レイヤ定義（用途別に全て先に） ---
d.addLayer("Outline", "white");      // 外形
d.addLayer("Holes", "red");          // 穴（モーター/ボルト/取付）
d.addLayer("Center", "cyan");        // 中心線・PCD 補助円
d.addLayer("Annotation", "green");   // 注記

// --- 2. ジオメトリ ---

// 外形 直線部（接点間）
d.line(8, 0, 142, 0, "Outline");     // 底辺
d.line(150, 8, 150, 92, "Outline");  // 右辺
d.line(142, 100, 8, 100, "Outline"); // 上辺
d.line(0, 92, 0, 8, "Outline");      // 左辺

// 外形 R8 接弧（各コーナー、弧中心 = コーナーから内側に (R,R)）
d.arc(8, 8, 8, 180, 270, "Outline");    // 左下(凸)
d.arc(142, 8, 8, 270, 360, "Outline");  // 右下(凸)
d.arc(142, 92, 8, 0, 90, "Outline");    // 右上(凸)
d.arc(8, 92, 8, 90, 180, "Outline");    // 左上(凸)

// 中央 モーター穴 φ50 (r=25)
d.circle(75, 50, 25, "Holes");

// PCD70 補助円 (r=35)
d.circle(75, 50, 35, "Center");

// ボルト穴 φ6 (r=3) × 4 個、PCD70 (r=35)、90° 間隔（45° オフセットの対角配置）
var nBolt = 4;
var pcd = 35;
var boltR = 3;
var cx0 = 75, cy0 = 50;
for (var i = 0; i < nBolt; i++) {
    var ang = (2 * Math.PI / nBolt) * i + Math.PI / 4; // 45,135,225,315 度
    var bx = cx0 + pcd * Math.cos(ang);
    var by = cy0 + pcd * Math.sin(ang);
    d.circle(bx, by, boltR, "Holes");
}

// 四隅 取付穴 φ8 (r=4)、コーナーから各 15mm 内側
d.circle(15, 15, 4, "Holes");
d.circle(135, 15, 4, "Holes");
d.circle(135, 85, 4, "Holes");
d.circle(15, 85, 4, "Holes");

// --- 3. 注記（中心線含む） ---

// 中心十字線（外形より少しはみ出す）
d.line(2, 50, 148, 50, "Center");
d.line(75, 2, 75, 98, "Center");

// テキスト注記
d.text("Motor Mount Plate 150x100 R8", 4, -8, 4, "Annotation");
d.text("Center hole phi50", 4, -15, 3.5, "Annotation");
d.text("4x phi6 PCD70 / 4x phi8 corner", 4, -21, 3.5, "Annotation");

// --- 4. 保存（構造化レスポンス付き） ---
d.saveAndReport(_qcadDrawOutput);
