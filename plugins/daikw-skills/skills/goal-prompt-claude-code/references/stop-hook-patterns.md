# Stop hook の書き方リファレンス

L3 出力で使う agent-based Stop hook の実用パターン集。

## 基本: テスト green を待つ

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Verify all unit tests pass. Run `npm test`. If anything fails, return {\"ok\": false, \"reason\": \"<failing test summary>\"}. If all green, return {\"ok\": true, \"reason\": \"all tests pass\"}.",
        "timeout": 120
      }]
    }]
  }
}
```

## 複合: test + lint + build

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Verify the migration is complete:\n1. Run `npm test` — all green\n2. Run `npm run lint` — no errors\n3. Run `npm run build` — exits 0\n4. Confirm `grep -r 'oldApi' src/` returns no matches\n\nIf any step fails, return {\"ok\": false, \"reason\": \"<which step + summary>\"}.\nIf all pass, return {\"ok\": true, \"reason\": \"migration verified\"}.",
        "timeout": 300
      }]
    }]
  }
}
```

## scope 保護: 不要なファイルが変更されていないか

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Check that only files in src/auth/ were modified.\nRun `git diff --name-only main`.\nIf any file outside src/auth/ is listed, return {\"ok\": false, \"reason\": \"out-of-scope modification: <files>\"}.\nIf scope is clean AND `npm test` passes, return {\"ok\": true, \"reason\": \"scope clean + tests pass\"}.",
        "timeout": 180
      }]
    }]
  }
}
```

## 段階的完了: PLAN.md チェックリスト

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "Read PLAN.md. Count `- [ ]` (incomplete) and `- [x]` (complete) checkboxes.\nIf any `- [ ]` remains, return {\"ok\": false, \"reason\": \"next: <first incomplete task>\"}.\nIf all complete AND `npm test` passes, return {\"ok\": true, \"reason\": \"plan complete\"}.",
        "timeout": 180
      }]
    }]
  }
}
```

## モデル指定（任意）

`model` フィールドで evaluator のモデルを上書き可能:

```json
{
  "type": "agent",
  "prompt": "...",
  "model": "claude-sonnet-4-6",
  "timeout": 300
}
```

デフォルトの Haiku で精度が足りない複雑な判定は Sonnet を指定する。

## ハマりどころ

### `stop_hook_active` チェック

無限ループを防ぐため、prompt 内に「同じエラーが 3 回連続したら ok: true を返して停止」のようなセーフティを書く。

### timeout の調整

- Light: test だけ → 60-120 秒
- Medium: test + lint + build → 180-300 秒
- Heavy: フル CI 相当 → 300-600 秒

### settings.local.json への配置

ユーザー固有の experimental 設定なので **`.claude/settings.json` ではなく `.claude/settings.local.json`** に置く。gitignore 対象。

## autoresearch 連携モード用: 薄い iteration hook

autoresearch の 1 iteration を /goal で記述する場合、Stop hook の prompt は **iteration の local check のみ** を判定する薄いものにする (global metric は autoresearch 側で見る):

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "agent",
        "prompt": "This is one iteration of an outer autoresearch loop. Check ONLY the local iteration result, not the global metric.\n\nLocal check:\n1. Does `ITERATION_RESULT.md` exist?\n2. Does it contain either a `success:` or `failure:` line?\n3. If it has a metric value (e.g., `local_metric: 0.85`), is it within sanity bounds (0 <= x <= 1)?\n\nIf all three pass, return {\"ok\": true, \"reason\": \"iteration complete, outer loop will decide keep/discard\"}.\nIf any fails, return {\"ok\": false, \"reason\": \"<which check failed>\"}.\n\nDo NOT attempt to evaluate the global goal here. The autoresearch outer loop owns that.",
        "timeout": 60
      }]
    }]
  }
}
```

このパターンの利点:

- 1 iteration あたりの hook 実行時間が短い (60 秒程度)
- evaluator が「global metric を改善したか」のような責任を負わない
- /goal 単体で数千 epoch 級のループを表現しようとして 4000 char 制約に当たる問題を回避

詳細は [autoresearch-handoff.md](autoresearch-handoff.md) を参照。
