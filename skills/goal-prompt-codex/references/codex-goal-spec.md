# Codex CLI /goal 仕様メモ

このスキルが生成するプロンプトが対象とする Codex CLI `/goal` 機能の仕様。

## 概要

Codex CLI の experimental スラッシュコマンド。会話スレッドに objective を永続的に貼り付け、Codex が plan → act → verify → correct のサイクルを自律的に回す。Ralph loop の OpenAI 公式実装。

## 有効化

`~/.codex/config.toml` で以下:

```toml
[features]
goals = true
```

または CLI 内で `/experimental` から有効化。

## 操作

```
/goal <objective>    # 目標を貼る
/goal                # 現在の目標を表示
/goal pause          # 一時停止
/goal resume         # 再開
/goal clear          # 破棄
```

## Lifecycle 5 状態

- `pursuing`: 作業中
- `paused`: `/goal pause` で suspended
- `achieved`: agent が audit を経て完了確認
- `unmet`: blocker 発生でユーザー入力待ち
- `budget-limited`: token budget 枯渇

## 永続性

プロセス再起動・リブート・TUI exit を跨いで状態が保持される。

## 設計哲学

**audit-first completion**: 「テストが通った」「実装が完了した」だけでは achieved にしない。元の objective に照らして agent 自身が監査する。

## 向くタスク

- マルチステップで決定論的、検証可能（test / lint / build）
- 3 ターン以上かかる作業
- マイグレーション、大規模 refactor、PLAN.md 駆動の実装

## 向かないタスク

- 単発タスク
- UI / アーキ判断のような主観
- open-ended な探索
- 不可逆な高リスク変更

## プロンプト構造の要素

良い /goal プロンプトに含めるべきもの:

1. **動詞**: build / map / find / QA / decide など終わりが見える動詞
2. **否定制約**: "Do not edit" / "Do not push" / 禁止事項
3. **検証手段**: 具体的なコマンド or 観測可能な状態
4. **スコープ**: 含む / 除く
5. **完了シグナル**: eval score / test green / 客観基準
6. **中間アーティファクト**: PLAN.md / NOTES.md を媒介
7. **報告分離**: 修正と issue 報告を別に
8. **audit ステップ**: completion を agent 自身が確認する手順

## 参考リンク

- 公式 docs: https://developers.openai.com/codex/cli/slash-commands
- Follow a goal use cases: https://developers.openai.com/codex/use-cases/follow-goals
