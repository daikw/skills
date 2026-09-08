# Rasterアイコンの制作

bitmapの表情・質感・写真素材が必要な場合や、既存bitmapを編集する場合に読む。
このスキルは専用の画像生成runnerを同梱しない。

## 実行経路

現在の環境で利用可能な画像生成・編集skillまたはtoolを確認し、その文書化された操作方法に従う。
特定のmodel名、未導入CLI、API契約を推測して実行しない。
利用できない場合は不足する能力を示し、制作済みのように報告しない。

既存画像の編集では先に画像を確認し、対象の識別、残す特徴、変更内容を渡す。
制作物は保存して実際の小サイズ表示で確認する。生成サービスの返答だけで視認性を合格にしない。

## 渡す内容

- bot名・用途・読者に伝えたい印象
- 既存資産・ブランド・残す特徴
- モチーフ、構図、必要な背景・crop・透過
- 実表示で必要な識別性と出力サイズ
- 文字を入れる場合の正確な文字列

```text
Create a bot icon for <purpose> using <reference or brand>.
Preserve <required features>. Convey <intended impression> through <motif>.
It will appear at <actual sizes> on <background/crop>.
Keep the main silhouette distinguishable at the smallest size.
Deliver <required format and dimensions>.
```

制作方法の都合で候補数、色数、モデル、課金budgetを追加しない。
指定のない作画上の選択は目的に合わせて行い、追加の有料実行が必要なら適用される権限・budgetに従う。
