# Claude Code /goal 仕様メモ

このスキルが生成するプロンプトが対象とする Claude Code 公式 `/goal` 機能の仕様。

## 概要

Claude Code 公式の session-scoped slash command。condition を設定すると、各ターン終了後に別モデル（"small fast model"）が会話履歴と condition を読んで yes/no 判定。`no` なら理由を guidance として次ターン継続、`yes` でクリア。

## 実装の正体

`/goal` は **prompt-based Stop hook の session-scoped 版**。既存の hook 機構の薄いラッパーであり、新規ランタイム機能ではない。

## 操作

```
/goal <condition>     # 設定（即座に最初のターンが走る）
/goal                 # 状態確認（elapsed / turns / tokens / 最新理由）
/goal clear           # 解除（stop / off / reset / none / cancel もエイリアス）
```

- 1 セッション 1 goal。新しい `/goal` で上書き
- condition は **4000 char 上限**
- `--resume` / `--continue` で active goal 復活。ただし counter は reset
- 信頼済み workspace 必須
- `disableAllHooks` / `allowManagedHooksOnly` が有効だと使えない

## Headless モード

```bash
claude -p "/goal CHANGELOG.md has an entry for every PR merged this week"
```

`-p` で完了まで一括実行。Ctrl+C で中断。

## evaluator (小モデル)

- デフォルト: Haiku
- 設定で変更可能（`model` フィールド）
- **ツール呼び出し不可**。会話に surface された内容しか見えない
- yes/no と短い理由を返す

## L1 / L3 の使い分け（このスキル独自分類）

- **L1**: 公式 `/goal` をそのまま使う。evaluator は Haiku、ツール不可
- **L3**: agent-based Stop hook を自前で書く。evaluator は subagent、ツール可
- L2（prompt-based Stop hook 自前 + Haiku 以外のモデル）は L1 と L3 の中間だが、運用上のメリットが薄いのでこのスキルでは扱わない

## prompt-based hook の仕様

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Check if all tasks are complete. If not, respond with {\"ok\": false, \"reason\": \"what remains\"}."
      }]
    }]
  }
}
```

- model フィールドで上書き可（デフォルト Haiku）
- 返り値: `{"ok": true/false, "reason": str}`
- Stop hook で `ok: false` → reason が次ターン guidance

## agent-based hook の仕様

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Verify all unit tests pass. Run the test suite and check results.",
        "timeout": 120
      }]
    }]
  }
}
```

- experimental（変更の可能性あり）
- 同じ `{"ok": ..., "reason": ...}` 形式
- デフォルト timeout 60 秒、最大 50 ターン
- **subagent はツール使える**（Read / Bash / Edit など）
- Codex /goal の audit-first 相当の動作が可能

## 参考リンク

- 公式 docs: https://code.claude.com/docs/en/goal
- Hooks guide: https://code.claude.com/docs/en/hooks-guide
- Headless mode: https://code.claude.com/docs/en/headless
