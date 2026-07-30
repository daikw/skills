# サポート界面への異種マテリアル活用パターン集

X (Twitter) 上の実践報告から収集した、サポート界面（interface）に本体と別のマテリアルを
使うパターン集。2026-07 時点の収集。原理は共通で「**相溶性のないポリマー同士は層間接着
しない**」ことを利用し、界面だけ異種材にしてサポートを無傷で剥がす。

## パターン一覧（材料ペア）

| 本体 | 界面/サポート | 分離方式 | コスト | 実践報告の要点 |
|---|---|---|---|---|
| PETG | PLA | 剥離（ぺりぺり） | ◎ 余り材で可 | 定番。Top Z distance 0 でも密着から剥がれる。サポート面の方が滑らかになるという報告も |
| PLA | PETG | 剥離 | ◎ | 逆向きも同様に有効。透明 PETG をサポートにすると見分けやすい |
| TPU | PLA | 剥離 | ◎ | 「程よくくっつき綺麗に剥がれる」。フォーミング系 TPU はサポート最小化が前提 |
| ABS / ASA | HIPS | 剥離 or リモネン溶解 | ○ | 剥離用途が現実的。**溶解は non-recommended**: リモネンは ABS 本体も侵す |
| PLA / PETG / ナイロン | BVOH | 水溶 | △ 高価（~$80-90/500g） | PVA より速く溶け、接着相性も広い。薄層 interface 限定なら消費は少ない |
| PLA 等（低温材） | PVA | 水溶 | △ | 中空・複雑形状の決定版だが**吸湿に極端に弱い**（stringy/brittle 化）。乾燥保管必須 |
| ナイロン / PC / PEEK | AquaSys 120/180 | 水溶 | ✕ 高価 | 高温材で PVA が焦げる領域の専用品 |
| PLA / PETG | 専用サポート材（Bambu Support for PLA/PETG 等） | 剥離 | ○ | 界面品質は最良との報告。組成は非公開（PLA ベース説、TPU+PETG 説あり）。Bambu「Support for ABS」は実質 HIPS |

## スライサー設定パターン

- **interface のみ異種材にする**: サポート本体は本体と同じ材、interface 層（2-3 層）だけ
  異種材を割り当てる。高価な水溶材・専用材の消費を 1 桁減らせる。Bambu Studio は
  サポート設定で interface filament を独立に指定できる
- **密着設定に振る**: 異種材界面なら接着しないので、通常サポートのような隙間が不要。
  実測ベストとの報告（@ddesign, 2025-07）: `Top Z distance = 0mm`、
  `Top interface spacing = 0mm`、`Interface pattern = Rectilinear interlaced`。
  隙間ゼロにすることで被サポート面の面品質がむしろ向上する
- **マルチパーツへの材料割り当て**: OBJ 等でインポートしてパーツごとに
  filament 1 = PLA / filament 2 = PETG を割り当てれば、嵌合パーツの「くっつかない」
  組み立て（interlocked print-in-place）にも同じ原理を流用できる（@adnarimnavi の
  PrusaXL 事例: PLA ハンドル + PETG スプリングの一体印刷）

## ハードウェア形態別の注意

| 形態 | 相性 | 注意点 |
|---|---|---|
| デュアルノズル（H2D/H2C, IDEX 等） | ◎ | パージ不要・コンタミなし・造形時間の伸びが最小。「dual nozzle ではプロファイル調整すれば no scarring」（@Latinvixen） |
| AMS / MMU（単ノズル切替） | ○ | フィラメント交換のパージ waste が発生（"poops"）。interface 層だけ異種材にして交換回数を抑える。`Long retraction when cut` でパージ約 25% 減 |
| 単ノズル手動切替 | △ | **クロスコンタミに注意**: パージしても残留 PLA が PETG 押し出しに微膜として乗り、界面近傍の層間接着を破壊する報告あり（@Leonard0Retard0）。強度部品では避ける |

## 落とし穴

- **PLA マット系は非推奨**: Bambu wiki の PETG×PLA 剥離手法は PLA Basic のみ推奨。
  マット系はフィラー由来で挙動が変わる（@yakumoreo89300 の指摘）
- **PVA は保管が全て**: 吸湿で印刷不能レベルまで劣化する。乾燥剤 + 密閉、印刷前乾燥
- **HIPS 溶解は ABS を侵す**: 溶解前提の HIPS 運用は事実上 breakaway 専用と考える
- **サポート材と気付かず本体印刷**: サポート用 PLA を通常 PLA と取り違えると層間剥離する
  （AMS 在庫のラベリングを厳格に）
- **強度が要る部品での単ノズル異種材**: 上記コンタミ問題。デュアルノズル機を使うか
  同種材サポートに戻す

## 出典（X posts, 収集 2026-07-30）

- @Latinvixen 2026-07-09 — PETG サポート + PLA Tough、デュアルノズルで no scarring（728 likes）
- @Tsukasa_3D 2024-07-09 — PETG 本体 + PLA サポート、密着から剥離・サポート面が滑らか（241 likes）
- @mcafe68 2024-10-26 — AMS 導入で support interface に PETG、「パリリッと剥がせる」
- @goshintai_crf 2025-11-27 — PLA×PETG、0 距離設定でも剥離
- @shirohebi 2024-12-20 — PLA×PETG サポート推奨
- @Natsu_umidigi 2026-06-30 — PETG のサポートに PLA「めちゃキレイに剥がれる」
- @sat_chan_pe 2021-04-23 — TPU 本体 + PLA サポート（Creator3）
- @ddesign 2025-07-08 — PLA 専用サポート + Top Z distance/interface spacing 0mm + Rectilinear interlaced がベスト
- @PatrickLebel9 2026-04-10 / 2026-07-28 — H2D で ABS+HIPS interface、X1C 比の運用差。単ノズルはパージ増が必要
- @Leonard0Retard0 2026-07-26 — 単ノズルのクロスコンタミによる層間接着破壊の機序
- @Jorel_2557 2026-07-26 — PVA/BVOH/AquaSys/HIPS の体系的整理（溶媒・弱点・適合材）
- @3DPBelgian 2025-09-29 — ABS サポート選定の苦悩（リモネンが ABS を侵す、PVA 温度不適合、BVOH 高価）
- @emberprototypes / @VectorRoll 2025-07-06 — Bambu 専用サポート材の組成考察（Support for ABS ≒ HIPS）
- @maahirpanchal 2024-09 — AMS で専用サポート材プロファイルを流用して PLA/ABS を相互 interface 化
- @yakumoreo89300 2026-07-27 — PLA マット系が Bambu wiki 推奨外という指摘
- @adnarimnavi 2024-02-13 — PrusaXL で PLA+PETG interlocked 一体印刷（262 likes）
- @GUMM13 2025-01-05 — 水溶サポートは AMS 交換 waste でむしろ非効率になりうる
- @BambulabGlobal 2024-04-08 — Long retraction when cut でパージ最大 25% 減
