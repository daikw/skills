---
name: business-evaluation
description: "事業評価（投資判断/新規事業Go-NoGo/M&A初期DD）を投資メモ形式で実施する。Web検索・社内資料・並列エージェントを活用し、Fact/Assumption/Unknown を分離したレポートを生成する。キーワード: 事業評価, DD, デューデリ, 投資メモ, Go-NoGo, ビジネス分析"
user-invocable: true
argument-hint: "<事業概要 or 評価対象の説明>"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebSearch
  - WebFetch
  - Task
  - AskUserQuestion
  - TaskCreate
  - TaskUpdate
  - TaskList
---

# Business Evaluation - 事業評価レポート生成

投資メモ / Due Diligence 形式で事業を評価し、GO / NO_GO / HOLD の判断材料を生成する。

## When to Use

- 新規事業の Go/NoGo 判断
- 投資先の初期評価・DD
- M&A のスクリーニング段階
- 既存事業の定期見直し
- 競合分析・市場参入検討

## 前提ルール（厳守）

1. **Fact / Assumption / Unknown を絶対に混ぜない**
   - Fact: 出典URL付きで示す。重要主張は2ソース以上でクロスチェック
   - Assumption: 「仮説」と明記し、影響度と検証方法を添える
   - Unknown: 「不明」「未検証」と正直に書く
2. **数字は「定義 → 式 → 代入 → 結果」** の順で示し、前提（単位・期間・通貨）を明記
3. **判断は確率ではなく「条件付き推奨」** で書く（例: ○○が満たされるなら GO）
4. **反証を必ず書く** - なぜ間違い得るか、Pre-mortem 的に列挙
5. **LLM出力を鵜呑みにしない** - 「それっぽいメモ」で安心して検証を止めないよう注意喚起を含める

## 実行手順

### Phase 0: 入力の確認

`$ARGUMENTS` を解析し、不足があれば AskUserQuestion で聞く。

必要な入力:
- **事業概要**: 何をやるのか（1-3行）
- **ターゲット顧客**: 誰向けか
- **提供価値**: 何を解決するか
- **価格/課金モデル**: どう稼ぐか
- **現状の数字**: 売上・ユーザー数など（あれば）
- **競合**: 把握している範囲で
- **地域/規制**: 対象市場
- **評価目的**: Go/NoGo ？ 投資判断？ M&A？
- **参考資料**: URL や社内ドキュメントのパス

### Phase 1: 調査計画の策定

入力をもとに 5-12 個の調査クエリを作成する。以下の観点をカバー:

| 章 | 調査観点 | 主なフレームワーク |
|----|----------|-------------------|
| 市場・外部環境 | 市場規模・成長・規制・マクロ | TAM/SAM/SOM, PESTLE |
| 業界構造 | 競争要因・収益性の構造 | Porter's 5 Forces（※静的スナップショットの限界に注意） |
| 顧客課題 | 誰のどんな痛み？代替行動は？ | Value Proposition Canvas |
| ビジネスモデル | 収益/原価/チャネル/リソース | Business Model Canvas |
| 競合・差別化 | 勝ち筋・ポジショニング | SWOT |
| 財務 | 価値算定・感度 | DCF（※前提依存の落とし穴に注意）, マルチプル |
| リスク | 致命傷・前提崩壊 | Pre-mortem |

### Phase 2: 並列調査（Task エージェントを活用）

調査クエリを **並列で** Task エージェントに投げる。各エージェントには以下を指示:

- 目的とスコープ境界
- Fact/Assumption/Unknown を分離して返すこと
- 出典URLを必ず付けること
- 主要主張は2ソース以上で検証すること

**典型的な並列分担:**
1. **市場調査** - TAM/SAM/SOM, PESTLE, 業界成長率
2. **競合調査** - 主要プレイヤー, SWOT, 差別化要因
3. **ビジネスモデル分析** - BMC, ユニットエコノミクス
4. **リスク調査** - 規制, 技術, オペレーション, 法務

### Phase 3: 統合 & 反証

1. 各エージェントの結果を統合
2. **矛盾点・未検証事項を洗い出す**
3. **Pre-mortem を実施**: 「この事業が失敗するとしたら何が原因か？」を列挙
4. **Red Team 的に反証**: 楽観的な結論に対して意図的に反論を構築

### Phase 4: レポート生成

以下の投資メモ形式で Write ツールを使って出力する。

## 出力フォーマット（投資メモ形式）

```markdown
# 事業評価レポート: {事業名}

_生成日: {date}_
_評価目的: {Go/NoGo | 投資判断 | M&A スクリーニング}_

---

## 1. Executive Summary
結論、なぜ今、推奨/非推奨の核心。条件付きで GO / NO_GO / HOLD を明示。

## 2. Problem & Customer
誰のどんな痛みか。代替行動は何か。VPC の観点で整理。

## 3. Market
- TAM / SAM / SOM（定義 → 式 → 代入 → 結果）
- PESTLE 分析（該当する項目のみ）
- 成長率・購買構造

## 4. Competition & Moat
- 競合マップ
- SWOT（内部: 強み/弱み、外部: 機会/脅威）
- 差別化の持続可能性
- （必要なら）Porter's 5 Forces

## 5. Product & Distribution
提供価値、導入障壁、GTM 戦略。

## 6. Business Model
BMC 形式: 収益 / 原価 / チャネル / キー資源 / キーパートナー。

## 7. Traction & Metrics
売上 / 成長率 / 継続率 / 粗利 / チャーン等。
データなしの項目は「不明」と明記。

## 8. Unit Economics
LTV / CAC / 粗利 / 回収期間。
データ不足なら推定値を使い「仮説」と明記。

## 9. Financials & Valuation
DCF / マルチプル（該当する場合）。
**感度分析は必須**（楽観/基本/悲観の3シナリオ）。
※ DCF の前提（割引率・成長率・CF推定）に非常に敏感であることを注記。

## 10. Risks & Mitigations
- 技術 / 法務 / セキュリティ / オペ / 資金繰り
- **Pre-mortem**: この事業が失敗する理由トップ3
- 各リスクの軽減策

## 11. Open Questions
未解決の論点と、必要な追加調査（一次情報: 顧客ヒアリング・財務明細・契約）。

## 12. Decision
- **推奨**: GO / NO_GO / HOLD
- **条件**: ○○が満たされるなら GO、満たされないなら HOLD
- **次のアクション**: 具体的なネクストステップ
- **必要な一次情報**: LLM では取れない、人間が取るべき情報

---

## Appendix: Fact / Assumption / Unknown 分離表

### Facts（出典あり）
| # | 主張 | 出典 | 検証状況 |
|---|------|------|----------|
| 1 | ... | URL | 2ソース確認済 |

### Assumptions（仮説）
| # | 仮説 | 間違った場合の影響 | 検証方法 |
|---|------|-------------------|----------|
| 1 | ... | High/Med/Low | ... |

### Unknowns（不明）
| # | 不明事項 | 理由 | 必要なデータ |
|---|----------|------|-------------|
| 1 | ... | ... | ... |

## Appendix: スコアカード

| 評価軸 | スコア(0-5) | 根拠 |
|--------|------------|------|
| 市場の魅力度 | | |
| 顧客課題の深さ | | |
| 競争優位性 | | |
| ビジネスモデルの健全性 | | |
| チーム/実行力 | | |
| 財務の見通し | | |
| リスクの許容度 | | |

**赤信号（致命傷候補）:**
- ...
```

## よくある失敗（この評価で気をつけること）

1. **フレームを回すこと自体が目的化** → 意思決定に効く「致命傷」の発見を最優先
2. **Porter/DCF を万能視** → 5 Forces は静的スナップショットに過ぎない。DCF は前提に超敏感
3. **「それっぽいメモ」で安心して検証を止める** → AI出力は必ず検証。不明は不明と書く
4. **一次情報を取りに行かない** → 不明が多い事業ほど、顧客/契約/原価の一次情報が先

## フレームワーク参考リンク

- [EBAN DD Guidelines](https://www.eban.org/due-diligence-guidelines-and-template-document/)
- [Carta Investment Memo](https://carta.com/learn/private-funds/management/portfolio-management/investment-memo/)
- [Visible Investment Memo](https://visible.vc/blog/investment-memo/)
- [Business Model Canvas (Strategyzer)](https://www.strategyzer.com/library/the-business-model-canvas)
- [Value Proposition Canvas (Strategyzer)](https://www.strategyzer.com/library/the-value-proposition-canvas)
- [PESTLE (CIPD)](https://www.cipd.org/en/knowledge/factsheets/pestle-analysis-factsheet/)
- [SWOT (CIPD)](https://www.cipd.org/en/knowledge/factsheets/swot-analysis-factsheet/)
- [Porter's 5 Forces (HBR)](https://hbr.org/1979/03/how-competitive-forces-shape-strategy)
- [DCF Pitfalls (Investopedia)](https://www.investopedia.com/investing/pitfalls-of-discounted-cash-flow-analysis/)
- [DoorDash VC Memo](https://www.alexanderjarvis.com/doordash-venture-capital-investment-memo/)

## ステージ別の評価軸カスタマイズ

評価対象のステージに応じて重点を変える:

| ステージ | 重点評価軸 |
|----------|-----------|
| **SaaS** | NRR/GRR, チャーン, ARR成長率, マジックナンバー |
| **製造業** | 設備投資回収, 稼働率, 原価率, サプライチェーン |
| **規制産業** | 許認可, コンプライアンスコスト, 参入障壁 |
| **マーケットプレイス** | テイクレート, 流動性, ネットワーク効果 |
| **ハードウェア** | BOM原価, 量産コスト, 認証(CE/FCC等) |
