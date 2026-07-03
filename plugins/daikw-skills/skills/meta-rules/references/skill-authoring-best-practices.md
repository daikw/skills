# Skill Authoring Best Practices - 公式原則の要約

[meta-rules](../SKILL.md) の frontmatter・本文の書き方を補う、Anthropic 公式ベストプラクティスの要約。
ユーザー・プロジェクト固有の判断（配置4系統・両ハーネス両置き等）は meta-rules 本文の正本を参照する。

## 公式ドキュメント

- **Best practices（公式）**: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- **Complete Guide to Building Skills（PDF）**: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

## Context Window の節約

- startup 時はすべてのスキルの `name` + `description` のみロード
- `SKILL.md` 本文はスキル発火時にのみ読まれる
- 参照ファイルは Claude が必要と判断したときのみ読まれる
- → 本文に書く価値のある情報のみ置く

## description が discovery の鍵

多数のスキルが並存する環境では description だけでスキルが選ばれる。必ず含める:
1. スキルが何をするか（動詞 + 対象）
2. いつ使うか（トリガー条件・ユーザー発話例）
3. いつ使わないか（誤爆・不発を両方抑える）

## Progressive Disclosure の 3 レベル

| レベル | 内容 | タイミング |
|---|---|---|
| Metadata | name + description | 常時（~100 words） |
| SKILL.md 本文 | 手順・ワークフロー | 発火時（< 5k words） |
| 参照ファイル | 詳細スキーマ・例・API仕様 | 必要時（無制限） |

## Evaluation-Driven Development

1. スキルなしで Claude にタスクを実行させ、失敗箇所を記録する
2. その失敗をカバーする評価シナリオを 3 つ作成する
3. 最小限の手順を書いてシナリオを通過させる
4. 実使用で観察し、改善を繰り返す

広範な手順を最初から書かない。実際のギャップにのみ対応する。

## Multi-model テスト

| モデル | 注意点 |
|---|---|
| Haiku | 情報量が少ないと詰まる。十分なガイドが必要 |
| Sonnet | バランス型。標準的なターゲット |
| Opus | 説明過多になりがち。不要な説明を省く |

Haiku で動けば他でも動く。Opus 向けに最適化すると Haiku で過少情報になるリスクがある。

## Feedback Loop パターン

品質が重要な処理には validate → fix → repeat ループを組み込む:

```markdown
1. ドキュメントを編集する
2. すぐ検証する: `python validate.py output/`
3. エラーがあれば修正して再検証する
4. 検証通過後のみ次へ進む
```

## Dynamic Context Injection

スキル発火時に実行結果をコンテキストに注入できる:

```markdown
## Current PR context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
```

バッククォートで囲まれたコマンド（`` !`cmd` ``）は Claude に送信される前に実行される。
