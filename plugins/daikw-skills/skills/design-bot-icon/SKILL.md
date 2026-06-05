---
name: design-bot-icon
description: Slack / Discord / その他 bot のアイコンを対話的に提案・生成・配置するスキル。コンセプトヒアリング → 4-6 案を表で提示 → 採用案を SVG で生成 → 192/48/24px の 3 段プレビュー → PNG 変換 → アップロード手順までを 1 ストロークで進める。トリガー：「アイコン提案して」「bot icon」「Slack App アイコン」「Discord bot アイコン」「アイコンデザイン」「アイコン作って」。SVG 以外の生成手段（DALL-E / Midjourney / Stable Diffusion）は raster-generators.md に TODO スケルトンとして残している。
---

# design-bot-icon

bot 用アイコン（Slack App / Discord bot / その他）の提案から配置までを支援する。

## 主な用途

- 新規 bot を立てたタイミングで、ブランド色や用途を踏まえたアイコン候補を出す
- 既存アイコンが暫定で済まされているプロジェクトに、本採用候補を提示する
- 24px に縮小しても判別できる視認性を担保する

## 守ること

- **コンセプトを最低 4 案出す**: モチーフ単発の案だけだと比較できない。表形式で
  メリット / デメリットを併記する
- **3 段プレビュー必須**: 192px (詳細表示) / 48px (通常) / 24px (サイドバー) を
  並べた preview.html を必ず生成する。24px で潰れるデザインは即却下対象
- **採用版を本ファイル名にコピー**: `magnifier.svg` のようなコンセプト名のまま
  運用しない。`<bot-name>.svg` / `<bot-name>.png` にリネームする
- **不採用案は捨てない**: `proposed/` に保管。別 bot や差し替え時に再利用できる
- **manifest 注意書き**: Slack App では manifest 経由でアイコン設定不可。App 作成
  後に管理画面から手動アップロードが必要なことを README に必ず書く

## ワークフロー

### Step 1. コンテキスト収集

最低限ヒアリングする項目：

- **bot の名前**: ファイル名・display name に使う
- **対象プラットフォーム**: Slack / Discord / Teams / その他（推奨サイズが変わる）
- **bot の主用途**: 通知 / 検索 / 監視 / 司会 / 等。モチーフ選定の核
- **ブランド色**: 既存の Slack App manifest や会社ガイドラインがあれば優先
- **雰囲気の希望**: ポップ / 真面目 / ミニマル / 親しみ
- **既存のキャラ・マスコット有無**: 既存資産があれば踏襲する

不明な項目は AskUserQuestion で 2-3 個に絞って一度に聞く。全部聞き出してから
案出しに進む。

### Step 2. コンセプト案提示

4-6 案を表形式で出す。各案には：

- **モチーフ**: 何をビジュアル化するか（例: 虫眼鏡 × 文書）
- **印象**: ユーザーが受け取る感情・読み取る意味
- **24px 判別性**: 潰れにくさの主観評価（◎ / ○ / △）
- **メリット / デメリット**: 1 行ずつ

例：

| 案 | モチーフ | 印象 | 24px | メリット | デメリット |
|---|---------|------|------|---------|-----------|
| 1 | フクロウ × 書類 | 親しみ・キャラ立ち | ◎ | 覚えやすい、固有性高い | 真面目な業務文脈とややギャップ |
| 2 | ベル × 書類 | 通知役を直接表現 | ○ | 機能的、迷いがない | 凡庸、差別化弱い |
| 3 | 虫眼鏡 × 番号 | 検索・調査特化 | △ | 機能を最も正確に伝える | 文字が潰れやすい |
| 4 | 鍵穴 × 文書 | ブランド統合 | ○ | 社内文脈にハマる | 解釈に説明が必要 |

ユーザーから「この案でいって」と回答が来るまで、複数案を維持。1 案だけ深堀り
しない。

### Step 3. SVG 生成

採用案を SVG で書く。要件：

- **viewBox 512x512**: Slack / Discord 共通の最大表示サイズに合わせる
- **角丸背景**: `<rect width="512" height="512" rx="96" fill="<brand>"/>` から開始
- **フラットデザイン**: グラデーション・影・複雑な装飾は避ける（24px で消える）
- **2-4 色まで**: 背景・主要モチーフ・アクセント・白の 4 色程度
- **太い線**: 24px 縮小時の視認性のため `stroke-width` は最低 4px
- **テキストは大きく**: 文字を入れるなら 100px 以上、英字 1〜2 文字まで

詳しい設計指針は [`svg-design-guidelines.md`](./svg-design-guidelines.md) 参照。

保存先：`<repo>/misc/icons/<concept>.svg`（採用前）または `<bot-name>.svg`（採用後）

### Step 4. プレビュー HTML 生成

`preview.html` を `misc/icons/` に置く。各案を 3 段で並べる：

```html
<div class="row">
  <img src="x.svg" width="192">  <!-- 詳細表示 -->
  <img src="x.svg" width="48">   <!-- 通常表示 -->
  <img src="x.svg" width="24">   <!-- サイドバー -->
</div>
```

- 背景色をグレーに（実際の Slack 表示に近づける）
- 各サイズにラベルを添える
- 採用前は複数案を並列、採用後は 1 案 + 採用根拠

`open misc/icons/preview.html` でブラウザに開いて、ユーザーに視認性を確認して
もらう。

### Step 5. PNG 変換

採用後は PNG を書き出す。優先順位：

```bash
# 1. librsvg（推奨。Homebrew: brew install librsvg）
rsvg-convert -w 512 -h 512 patent-bot.svg -o patent-bot.png

# 2. macOS 標準（品質はやや劣る）
qlmanage -t -s 512 -o . patent-bot.svg
mv patent-bot.svg.png patent-bot.png
```

`which rsvg-convert` で利用可否を確認。なければ `brew install librsvg` を提案。

### Step 6. 採用版にリネーム

```bash
cp <concept>.svg <bot-name>.svg
cp <concept>.png <bot-name>.png
mkdir -p proposed && mv <非採用>.svg <非採用>.png proposed/
```

### Step 7. アップロード手順 / README

`misc/icons/README.md` を作成または更新：

- ファイル一覧
- デザイン根拠
- SVG → PNG 変換コマンド
- アップロード手順（プラットフォーム別）

**Slack App の場合**:

1. https://api.slack.com/apps の対象 App を開く
2. **Basic Information** → **Display Information** → **App icon**
3. 512x512 PNG をアップロード
4. **Background color** を SVG の背景色 hex に合わせる

**Discord bot の場合**:

1. https://discord.com/developers/applications の Application を開く
2. **General Information** → **App Icon** から PNG をアップロード
3. 推奨は 512x512 PNG（最大 1024x1024 まで対応）

manifest や設定ファイル経由でアイコン設定はできないことが多い。手動アップロード
が必要な点を必ず README に書く。

## 拡張: SVG 以外の生成

DALL-E / Midjourney / Stable Diffusion を使った raster 生成は
[`raster-generators.md`](./raster-generators.md) にスケルトンを残してある。

現状このスキルは **SVG 生成のみ実装**。raster は TODO。raster を選びたい
ユーザーには `raster-generators.md` のテンプレを提示し、実行は手動で進めて
もらう（OpenAI API キー設定や Midjourney Discord 招待などはユーザー側責任）。

## チェックリスト

完了前に確認：

- [ ] コンセプト案を 4 つ以上提示した
- [ ] 各案にメリット / デメリットを併記した
- [ ] 採用案を 3 段プレビュー（192/48/24px）で視認性確認した
- [ ] SVG → PNG 変換が完了した
- [ ] `<bot-name>.svg/png` にリネームした
- [ ] 不採用案を `proposed/` に保管した
- [ ] README にアップロード手順を書いた
- [ ] manifest 経由でのアイコン設定不可を明記した
