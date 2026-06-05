# Raster 画像生成のオプション（TODO スケルトン）

SKILL.md の主軸は SVG 生成。raster (PNG / JPEG) を生成したい場合の選択肢を
プロンプトテンプレ付きで残しておく。実装は **すべて TODO**。実行はユーザーの
責任で進める。

## 共通の prompt engineering 指針

bot アイコン用に raster を生成するときの共通ポイント：

- `flat design` / `vector style` / `simple shapes` を冒頭に置く
- `512x512 app icon` / `centered composition` でサイズ・構図を指定
- `solid color background, #1f3a5f` のように背景色を hex で指定
- `no text` または `bold single letter only` でテキスト崩壊を回避
- `silhouette readable at 24px` で縮小視認性を要件化
- `no gradients` / `no shadows` / `no realistic textures` でアンチパターンを排除

### 共通テンプレ

```
A flat vector-style app icon, 512x512, centered composition, on a solid
#1f3a5f navy background with rounded corners. The icon depicts <MOTIF>.
Use only 3-4 colors: navy background, cream (#f4e4c1), orange (#e8a13d),
white. No gradients, no shadows, no realistic textures. The silhouette
must be readable at 24px. No text or maximum one bold letter.
```

`<MOTIF>` を「a magnifying glass over a patent document」のように差し替える。

---

## Option 1: DALL-E (`gpt-image-1`) — TODO

OpenAI の最新画像生成モデル。API キーがあれば curl で 1 ショット生成可能。

### 必要な準備

- OpenAI API キー (`OPENAI_API_KEY` env)
- 課金有効化（`gpt-image-1` は有料）

### curl 例

```bash
# TODO: 動作確認後にスキル本体に統合する
curl https://api.openai.com/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-image-1",
    "prompt": "<上記の共通テンプレに MOTIF を埋めたもの>",
    "size": "1024x1024",
    "n": 4,
    "background": "opaque"
  }' | jq -r '.data[].b64_json' | while read b64; do
    echo "$b64" | base64 -d > "candidate-$(date +%s%N).png"
  done
```

### TODO

- [ ] `n=4` で 4 案を一度に生成し、preview.html で並列表示する形に統合
- [ ] 生成結果を `proposed/` に自動配置
- [ ] 512x512 に縮小（`sips -z 512 512`）
- [ ] プロンプトテンプレを bot 用途別に分岐（通知系 / 検索系 / 監視系）

---

## Option 2: Midjourney — TODO

API がない（Discord 経由のみ）。手動生成。

### プロンプトテンプレ

```
flat vector app icon, magnifying glass over patent document, navy
#1f3a5f rounded square background, cream and orange accents, minimal,
no text, readable at 24px --v 6 --ar 1:1 --style raw
```

### 手順

1. Midjourney Discord に参加（要サブスクリプション）
2. 任意の bot チャンネルで `/imagine prompt:<上記>` を実行
3. 生成された 4 案から 1-2 案を Upscale
4. ローカルにダウンロード → `misc/icons/proposed/` に配置
5. 手動で 512x512 にリサイズ

### TODO

- [ ] Midjourney → ローカル配置までを半自動化（ダウンロードリンク貼り付けで取り込む）
- [ ] preview.html への自動統合
- [ ] プロンプトテンプレのプリセット化

---

## Option 3: Stable Diffusion (ローカル) — TODO

API キー不要。GPU か Apple Silicon があればローカルで生成可能。

### 必要な準備

- ローカルに SD WebUI (`stable-diffusion-webui`) または `sd-cli`
- アイコン向けのモデル（例: `dreamshaper`, `iconography_diffusion` 系）
- LoRA: `flat-icon-lora` のようなアイコン特化 LoRA があると安定

### CLI 例

```bash
# TODO: sd-cli の正確なフラグを確認、SKILL に統合
sd-cli txt2img \
  --model dreamshaper-v8 \
  --prompt "<上記の共通テンプレに MOTIF を埋めたもの>" \
  --negative "text, blurry, gradient, shadow, photo realistic" \
  --width 1024 --height 1024 \
  --num-images 4 \
  --output ./misc/icons/proposed/sd-{seed}.png
```

### TODO

- [ ] sd-cli vs WebUI どちらを推奨するか決める
- [ ] 推奨モデル / LoRA の選定（アイコン向け）
- [ ] negative prompt の最適化
- [ ] 生成結果の自動 512x512 リサイズ + preview 統合

---

## いつ raster を選ぶか

raster 生成は SVG より柔らかい表現・写実的な質感が出せるが、以下の制約がある：

| 比較 | SVG | Raster |
|------|-----|--------|
| 拡大しても劣化しない | ◎ | △（補間でぼやける） |
| 編集の手軽さ | ◎ | △（ピクセル単位で再生成必要） |
| 表現の幅 | 幾何学的・フラット中心 | 写実・キャラ・複雑なシェーディング可 |
| 生成スピード | 数秒（Claude が直接書ける） | 数十秒〜数分（API or GPU） |
| コスト | 無料 | API 課金 or GPU 必要 |

**SVG で表現できるなら SVG が原則**。raster を選ぶのは：

- キャラクター系（フクロウ・ネコ等）で表情や毛並みが欲しい
- 写実的なロゴと統合する必要がある
- 既存の写真・素材をベースに加工したい
- ブランドガイドが特定のテクスチャ・質感を要求している

## 実装ステータス

- ✅ SVG 生成（SKILL.md 本体）
- ⏳ DALL-E（このファイルにテンプレあり、実装未）
- ⏳ Midjourney（手動フロー、半自動化未着手）
- ⏳ Stable Diffusion（テンプレあり、推奨モデル選定未）

将来 raster 対応する際は、SKILL.md 側に `mode=svg` / `mode=dalle` /
`mode=midjourney` / `mode=sd` の分岐を導入する形を想定。
