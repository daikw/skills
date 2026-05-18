# SVG アイコン設計ガイドライン

24px に縮小しても判別できる SVG を書くための実務指針。

## 基本仕様

- **viewBox**: `0 0 512 512` 固定（Slack / Discord 共通の最大サイズ）
- **背景**: `<rect width="512" height="512" rx="96" fill="<hex>"/>` で角丸
  正方形。`rx="96"` は iOS 的な丸み
- **色数**: 2-4 色。背景・主要モチーフ・アクセント・白抜き
- **stroke-width**: 4px 以上。線が細いと 24px で消える
- **テキスト**: 1-2 文字、80px 以上のフォントサイズ
- **font-family**: serif（タイトル・印章）/ sans-serif（数字）/ monospace
  （特許番号など）

## 24px 視認性チェックリスト

縮小したとき：

- [ ] 主要モチーフがシルエットで認識できる
- [ ] 背景色とモチーフ色のコントラストが十分（WCAG AA: 4.5:1 以上）
- [ ] 細かい装飾（補助線、ハイライト）が消えても本質が残る
- [ ] テキストが入る場合、文字数 1-2 で 60% 以上の高さを占める
- [ ] 色だけに頼らず、形状でも識別可能（色覚多様性対応）

`preview.html` に 24px 表示を必ず含める。「ぱっと見で何の bot か分かるか」を
チームメンバーに見てもらうのが手堅い。

## モチーフカタログ

bot 用途別の頻出モチーフ：

| 用途 | 頻出モチーフ | 例 |
|------|------------|-----|
| 通知 | ベル / 拡声器 / 雷 / バッジ赤丸 | Slackbot |
| 検索・調査 | 虫眼鏡 / 双眼鏡 / レーダー | Spotlight, Sherlock |
| 監視 | フクロウ / 目 / カメラ | Sentry, Watchman |
| 文書・知識 | 本 / 書類 / 巻物 / 印章 | Notion, Confluence |
| 鍵・認証 | 鍵 / 鍵穴 / 盾 / ロック | Auth0, 1Password |
| AI・自動化 | ロボット / 歯車 / 脳 / 星 | GitHub Copilot, ChatGPT |
| データ | グラフ / 棒チャート / DB円柱 | Datadog, Grafana |
| コミュニケーション | 吹き出し / マイク / 会話 | Slack, Discord |

組み合わせの定石：「**機能モチーフ × 対象モチーフ**」（例: 虫眼鏡 × 文書、
ベル × 書類、フクロウ × 書類）。単発モチーフより意味が明確になる。

## 配色のセオリー

- **背景は濃色**: 白背景の Slack UI で目立つ。`#1f3a5f`（紺）/ `#2d2d2d`（黒）/
  `#5a3a8a`（紫）など
- **モチーフは暖色 or 黄系**: 紺背景に映える `#e8a13d`（オレンジ）/
  `#f4e4c1`（クリーム）/ `#ffffff`（白）
- **アクセントは赤**: 印章・通知バッジに `#c8493d` / `#d94c4c` あたり

ブランド色がある場合は、それを背景に固定して、モチーフ色を補色から選ぶと
収まりがよい。

## SVG 構造のテンプレ

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <!-- 1. 背景（角丸正方形） -->
  <rect width="512" height="512" rx="96" fill="#1f3a5f"/>

  <!-- 2. 背面モチーフ（書類など、薄い色） -->
  <g transform="translate(...)">
    ...
  </g>

  <!-- 3. 主要モチーフ（虫眼鏡、ベル等） -->
  <g transform="translate(...)">
    ...
  </g>

  <!-- 4. アクセント（印章、通知バッジ等） -->
  ...
</svg>
```

### よく使う形状パターン

**虫眼鏡**:

```xml
<g transform="translate(316,300)">
  <!-- ハンドル -->
  <line x1="78" y1="78" x2="160" y2="160"
        stroke="#a67c52" stroke-width="34" stroke-linecap="round"/>
  <!-- フレーム -->
  <circle r="98" fill="none" stroke="#e8a13d" stroke-width="22"/>
  <!-- レンズ -->
  <circle r="86" fill="#ffffff" opacity="0.95"/>
</g>
```

**ベル**:

```xml
<path d="M 0 -130 C -90 -130 -120 -50 -120 0
         L -130 20 L 130 20 L 120 0
         C 120 -50 90 -130 0 -130 Z"
      fill="#e8a13d" stroke="#a67c52" stroke-width="4"/>
<ellipse cx="0" cy="44" rx="22" ry="22" fill="#a67c52"/>
```

**書類**:

```xml
<g transform="translate(98,108)">
  <rect width="240" height="304" rx="10" fill="#f4e4c1" stroke="#0d2540" stroke-width="4"/>
  <!-- 折れ角 -->
  <path d="M 210 0 L 240 30 L 210 30 Z" fill="#d9b779"/>
  <!-- 罫線 -->
  <line x1="20" y1="64" x2="216" y2="64" stroke="#1f3a5f" stroke-width="3" stroke-linecap="round"/>
  <!-- 印章 -->
  <circle cx="194" cy="252" r="22" fill="none" stroke="#c8493d" stroke-width="4"/>
  <text x="194" y="262" font-size="22" text-anchor="middle" fill="#c8493d"
        font-family="serif" font-weight="bold">P</text>
</g>
```

## アンチパターン

- 細い線（stroke-width < 4px）→ 24px で消える
- グラデーション → フラットデザインの世界観を壊す、PNG 変換で品質劣化
- 細かい文字（< 60px）→ 24px で潰れて読めない
- 4 色超 → 視覚的にうるさい、24px で混色して識別困難
- 写実的なイラスト → ベクター向きでなく、サイズ縮小で破綻
