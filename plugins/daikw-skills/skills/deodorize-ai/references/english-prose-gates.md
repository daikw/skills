# English prose gates — 英語散文ゲート（B 系 + 語彙付録）

english-prose ルートの surface ゲート。構造ゲート S 系は [prose-structure-gates.md](prose-structure-gates.md)、捏造・残骸は [universal-gates.md](universal-gates.md) を併用する。

### B-1 定型オープナー — major

- 検出: 冒頭が `I hope this email finds you well` / `I wanted to reach out` / `I came across your profile` か？
- なぜ: ビジネスメール冒頭の最尤系列。受け手は一斉送信と読み、返信率が下がる。
- 修正: 相手・案件に固有の 1 文で始める。書けないなら本題から始める。

### B-2 偽の親しみクローザー — major

- 検出: 締めが `I hope this helps` / `Feel free to reach out` / `Let me know if you have any questions` か？
- 修正: 具体的な次アクション（誰が・いつまでに・何を）に置き換える。

### B-3 コーポレート・フィラー — major

- 検出: `in today's fast-paced world` / `in today's digital landscape` / `circle back` / `touch base` / `synergy` / `leverage` が出るか？
- 修正: 削除。文が成立しなければ、その文自体が内容を持っていない。

### B-4 独自視点の不在 — critical

- 検出: 文書全体を読んだあと、**著者しか知り得ない情報**（自分の経験・社内の数値・特定の顧客名・失敗談）が 1 つでもあるか？ → 無ければ陽性。
- なぜ: 訓練分布の平均への回帰。「自信ありげな語り口なのに汎用的でぼやけた質感」が生じる。表層 tell を全部消しても最後に残る判定基準。
- 修正: 著者固有の情報を最低 1 つ入れる。入れられないなら出さない。

### B-5 マーケティング空語 — major

- 検出: `groundbreaking` / `revolutionary` / `cutting-edge` / `seamless` / `robust` / `unleash` / `supercharge` / `empower` / `elevate` / `game changer` が製品・成果の形容に使われているか？
- 修正: 形容詞を削除し、測定可能な事実に置き換える（「高速」→ ベンチマーク値、または削除）。

## 語彙付録（密度判定・モデル世代で入れ替わる）

**運用注意**: 単一語の 1 回の出現は証拠にならない。1000 語あたりの密度と共起で判定する。特徴語はモデル世代ごとに入れ替わる（GPT-4 期の 19 語が GPT-5 期には 4 語に減少）ため、このリストは固定的な判定基準ではなく参考資料。判定の主軸は S 系（構造）と F 系（捏造）に置く。

| 世代 | 特徴語 |
|---|---|
| GPT-4 期 | additionally, boasts, crucial, delve, emphasizing, intricate, interplay, landscape, meticulous, pivotal, underscore, tapestry, testament, vibrant |
| GPT-4o 期 | align with, crucial, enhance, fostering, highlighting, pivotal, showcasing, underscore, vibrant |
| GPT-5 期 | emphasizing, enhance, highlighting, showcasing |
| Grok 系 | causal, empirical, correlate, underscore |

定型フレーズ: `let's dive in` / `picture this` / `here's the deal` / `stay tuned` / `secret sauce` / `deep dive` / `it's important to note`

### em-dash（—）について

英語圏で最も話題になった tell だが有効性は争われている（人間の書き手も昔から使う。OpenAI は過剰使用を修正済みで今後は検出力が落ちる）。**単独判定に使わない（minor）。** 段落あたり 2 個以上を密度の目安とする。日本語の「——」多用は JA-1 でカバーする。

---

出典: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing / https://www.contentbeta.com/blog/list-of-words-overused-by-ai/ / https://ozigi.app/blog/cold-email-that-does-not-sound-like-ai / https://techcrunch.com/2026/07/30/linkedin-adds-a-button-to-report-ai-generated-slop/ / https://theconversation.com/too-many-em-dashes-weird-words-like-delves-spotting-text-written-by-chatgpt-is-still-more-art-than-science-259629
