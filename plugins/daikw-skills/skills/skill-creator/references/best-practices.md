# Skill Authoring Best Practices - 参照リソース

## 公式ドキュメント

- **Best practices（公式）**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Complete Guide to Building Skills（PDF）**: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

## 主要原則の要約

### Context Window の節約

- startup 時はすべてのスキルの `name` + `description` のみロード
- `SKILL.md` 本文はスキル発火時にのみ読まれる
- 参照ファイルは Claude が必要と判断したときのみ読まれる
- → **本文に書く価値のある情報のみ置く**

### description が discovery の鍵

100 個以上のスキルがある環境では、description だけでスキルが選ばれる。
以下を必ず含める:
1. スキルが何をするか（動詞 + 対象）
2. いつ使うか（トリガー条件・ユーザー発話例）

### Progressive Disclosure の 3 レベル

| レベル | 内容 | タイミング |
|---|---|---|
| Metadata | name + description | 常時（~100 words） |
| SKILL.md 本文 | 手順・ワークフロー | 発火時（< 5k words） |
| 参照ファイル | 詳細スキーマ・例・API仕様 | 必要時（無制限） |

### Evaluation-Driven Development

1. スキルなしで Claude にタスクを実行させ、失敗箇所を記録
2. その失敗をカバーする評価シナリオを 3 つ作成
3. 最小限の手順を書いてシナリオを通過させる
4. 実使用で観察 → 改善を繰り返す

広範な手順を最初から書かない。実際のギャップにのみ対応する。

### Multi-model テスト

| モデル | 注意点 |
|---|---|
| Haiku | 情報量が少ないと詰まる。十分なガイドが必要 |
| Sonnet | バランス型。標準的なターゲット |
| Opus | 説明過多になりがち。不要な説明を省く |

Haiku で動けば他でも動く。Opus 向けに最適化すると Haiku で過少情報になるリスクがある。

### Feedback Loop パターン

品質が重要な処理には validate → fix → repeat ループを組み込む:

```markdown
1. ドキュメントを編集する
2. **すぐ検証**: `python validate.py output/`
3. エラーがあれば修正して再検証
4. 検証通過後のみ次へ進む
```

### Dynamic Context Injection

スキル発火時に実行結果をコンテキストに注入できる:

```markdown
## Current PR context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
```

バッククォートで囲まれたコマンド（`` !`cmd` ``）は Claude に送信される前に実行される。

## 過去の学習事例

### coding-agent-spec スキル設計（2026-03-12）

`~/.claude/skills/coding-agent-spec/` を作成した際の教訓:

- **Phase 1 のコマンドをプロジェクト固有にしない**: `./internal/*.go` のような言語依存コマンドは汎用スキルに不向き
- **時間範囲を固定しない**: `2024-2026年` → `最新安定版` に変更すべき
- **参照URLは別ファイルに**: 本文に URL を直書きすると陳腐化リスクがある
- **Freedom Level を明示する**: 低/中/高とデフォルト値を書くと Claude の自由度が適切に調整される
- **フェーズごとにチェックリスト**: 複雑なワークフローでは各フェーズの完了条件を書くと品質が上がる
